"""
TimelineRenderer — Human-Like Pro Video Editor (A.Z.E. Blueprint System)
Converts a Gemini-generated JSON blueprint into a finished MP4 video.

Blueprint schema:
  meta, video_track, audio_track, sfx_track, text_track, timing_events, color_grade_map
"""

import logging
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps
from PIL import Image as _PIL_Image
from moviepy import AudioFileClip, CompositeAudioClip, VideoClip, concatenate_audioclips

logger = logging.getLogger("AZE.timeline_renderer")

TARGET_W, TARGET_H = 1080, 1920
RENDER_FPS         = 24
_FONT_DIR          = Path(__file__).resolve().parent.parent / "data" / "fonts"
THAI_FONT          = str(_FONT_DIR / "kanit.ttf")
THAI_FONT_FALLBACK = "C:/Windows/Fonts/tahoma.ttf"
BGM_URL            = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
BGM_PATH           = Path("data/bgm.mp3")


# =========================================================
# FONT LOADING (reused from video_maker pattern)
# =========================================================

def _load_thai_font(size: int) -> ImageFont.FreeTypeFont:
    import warnings
    for fp in [THAI_FONT, THAI_FONT_FALLBACK]:
        for use_raqm in [True, False]:
            try:
                kwargs = {"layout_engine": ImageFont.Layout.RAQM} if use_raqm else {}
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    fnt = ImageFont.truetype(fp, size, **kwargs)
                raqm_ok = use_raqm and not any("Raqm" in str(w.message) for w in caught)
                logger.debug("Font: %s [%s]", Path(fp).name, "RAQM" if raqm_ok else "FreeType")
                return fnt
            except Exception:
                continue
    return ImageFont.load_default()


# =========================================================
# COLOR GRADING
# =========================================================

def _apply_color_grade(img: _PIL_Image.Image, grade: dict) -> _PIL_Image.Image:
    """Apply saturation / brightness / contrast from a grade spec (PIL ImageEnhance)."""
    sat = grade.get("saturation", 1.0)
    bri = grade.get("brightness", 1.0)
    con = grade.get("contrast",   1.0)
    if sat != 1.0:
        img = ImageEnhance.Color(img).enhance(sat)
    if bri != 1.0:
        img = ImageEnhance.Brightness(img).enhance(bri)
    if con != 1.0:
        img = ImageEnhance.Contrast(img).enhance(con)
    # hue_shift: not implemented in PIL without cv2 — logged and skipped
    hue = grade.get("hue_shift", 0)
    if hue != 0:
        logger.debug("hue_shift=%d — skipped (requires cv2)", hue)
    return img


# =========================================================
# TIMELINE RENDERER
# =========================================================

class TimelineRenderer:
    """Render a JSON blueprint into a final MP4 video."""

    def render(
        self,
        blueprint: dict,
        voiceover_path: str,
        output_path: str = "data/final_video.mp4",
    ) -> str:
        meta         = blueprint.get("meta", {})
        total_dur    = float(meta.get("total_duration", 30.0))
        grade_map    = blueprint.get("color_grade_map", {})
        video_segs   = blueprint.get("video_track", [])
        text_cues    = blueprint.get("text_track",  [])
        sfx_entries  = blueprint.get("sfx_track",   [])
        audio_segs   = blueprint.get("audio_track", [])

        # ── Pre-build per-segment image arrays ─────────────────
        seg_arrays: dict[str, np.ndarray] = {}
        for seg in video_segs:
            key = self._seg_key(seg, grade_map)
            if key not in seg_arrays:
                seg_arrays[key] = self._load_graded_array(seg, grade_map)

        # ── Pre-render text overlays ────────────────────────────
        text_overlays = self._prepare_text_overlays(text_cues)

        # ── make_frame callback ────────────────────────────────
        sorted_segs = sorted(video_segs, key=lambda s: float(s.get("t_start", 0.0)))

        def make_frame(t: float) -> np.ndarray:
            seg  = self._find_segment(sorted_segs, t)
            key  = self._seg_key(seg, grade_map)
            base = seg_arrays.get(key)
            if base is None:
                return np.zeros((TARGET_H, TARGET_W, 3), dtype=np.uint8)

            frame_pil = self._apply_effect(
                base, seg,
                t - float(seg.get("t_start", 0.0)),
                float(seg.get("t_end", total_dur)) - float(seg.get("t_start", 0.0)),
            )
            frame_pil = self._composite_text(frame_pil, text_overlays, t)
            return np.array(frame_pil.convert("RGB"))

        video = VideoClip(make_frame, duration=total_dur).with_fps(RENDER_FPS)

        # ── Audio mix ──────────────────────────────────────────
        audio = self._build_audio_mix(audio_segs, sfx_entries, voiceover_path, total_dur)
        if audio is not None:
            video = video.with_audio(audio)

        # ── Export ────────────────────────────────────────────
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.info("⏳ Timeline render → %s  (fps=%d, dur=%.1fs)", output_path, RENDER_FPS, total_dur)
        video.write_videofile(
            output_path,
            fps=RENDER_FPS,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="fast",
            logger=None,
        )
        logger.info("✅ Timeline render เสร็จสิ้น → %s", output_path)
        return output_path

    # =========================================================
    # SEGMENT HELPERS
    # =========================================================

    @staticmethod
    def _seg_key(seg: dict, grade_map: dict) -> str:
        """Unique cache key: asset path + color_grade name."""
        return f"{seg.get('asset','')}__{seg.get('color_grade','')}"

    def _load_graded_array(self, seg: dict, grade_map: dict) -> np.ndarray | None:
        """Load image asset, fit to target resolution, apply color grade, return numpy array."""
        asset = seg.get("asset", "")
        p = Path(asset) if asset else None
        if p and p.exists():
            try:
                with Image.open(p) as img:
                    img_rgb = img.convert("RGB")
                    if img_rgb.size != (TARGET_W, TARGET_H):
                        img_rgb = ImageOps.fit(
                            img_rgb, (TARGET_W, TARGET_H), Image.Resampling.LANCZOS
                        )
                    grade_name = seg.get("color_grade", "")
                    if grade_name and grade_name in grade_map:
                        img_rgb = _apply_color_grade(img_rgb, grade_map[grade_name])
                    return np.array(img_rgb)
            except Exception as exc:
                logger.warning("ไม่สามารถโหลด asset '%s': %s", asset, exc)

        # Fallback: try the default processed product image
        fallback = Path("data/images/processed_product.jpg")
        if fallback.exists():
            try:
                with Image.open(fallback) as img:
                    img_rgb = img.convert("RGB")
                    if img_rgb.size != (TARGET_W, TARGET_H):
                        img_rgb = ImageOps.fit(
                            img_rgb, (TARGET_W, TARGET_H), Image.Resampling.LANCZOS
                        )
                    grade_name = seg.get("color_grade", "")
                    if grade_name and grade_name in grade_map:
                        img_rgb = _apply_color_grade(img_rgb, grade_map[grade_name])
                    return np.array(img_rgb)
            except Exception:
                pass
        return None

    @staticmethod
    def _find_segment(sorted_segs: list, t: float) -> dict:
        """Return the active video_track segment at time t."""
        for seg in reversed(sorted_segs):
            if float(seg.get("t_start", 0.0)) <= t:
                return seg
        return sorted_segs[0] if sorted_segs else {}

    # =========================================================
    # EFFECT ENGINE
    # =========================================================

    def _apply_effect(
        self,
        src_array: np.ndarray,
        seg: dict,
        t_local: float,
        seg_dur: float,
    ) -> _PIL_Image.Image:
        """Apply zoom / Ken Burns / jump_cut effect to a source numpy array."""
        effect      = seg.get("effect", "ken_burns")
        scale_start = float(seg.get("scale_start", 1.0))
        scale_end   = float(seg.get("scale_end",   1.08))
        h, w        = src_array.shape[:2]
        pil_src     = _PIL_Image.fromarray(src_array)

        if seg_dur <= 0:
            seg_dur = 1.0
        progress = min(t_local / seg_dur, 1.0)

        if effect == "jump_cut":
            # Fast scale punch at cut point: spike to 120% then settle over 0.3s
            SETTLE = 0.3
            if t_local < SETTLE:
                punch = 1.2 + (scale_start - 1.2) * (t_local / SETTLE)
                scale = punch
            else:
                # After settling, do a gentle ken_burns
                post_progress = (t_local - SETTLE) / max(seg_dur - SETTLE, 0.01)
                scale = scale_start + (scale_end - scale_start) * post_progress
        elif effect in ("ken_burns", "zoom_in"):
            scale = scale_start + (scale_end - scale_start) * progress
        else:
            scale = scale_start  # static

        scale    = max(scale, 1.0)
        crop_w   = int(w / scale)
        crop_h   = int(h / scale)
        x1       = (w - crop_w) // 2
        y1       = (h - crop_h) // 2
        cropped  = pil_src.crop((x1, y1, x1 + crop_w, y1 + crop_h))
        return cropped.resize((TARGET_W, TARGET_H), _PIL_Image.Resampling.LANCZOS).convert("RGBA")

    # =========================================================
    # TEXT OVERLAY SYSTEM
    # =========================================================

    def _prepare_text_overlays(self, text_cues: list) -> list[dict]:
        """Pre-render RGBA overlay PIL images for each non-pause text cue."""
        overlays = []
        font_cache: dict[int, ImageFont.FreeTypeFont] = {}

        for cue in text_cues:
            if cue.get("style") == "pause" or not cue.get("text", "").strip():
                overlays.append({**cue, "_overlay": None})
                continue

            font_size = int(cue.get("font_size", 95))
            if font_size not in font_cache:
                font_cache[font_size] = _load_thai_font(font_size)
            font = font_cache[font_size]

            color_hex = cue.get("color", "#FFE600").lstrip("#")
            try:
                r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
            except ValueError:
                r, g, b = 255, 230, 0

            # Determine Y position from "position" field
            pos = cue.get("position", "bottom")
            if pos == "top":
                y_ratio = 0.12
            elif pos == "center":
                y_ratio = 0.50
            else:  # bottom (default)
                y_ratio = 0.85

            overlay  = _PIL_Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
            draw     = ImageDraw.Draw(overlay)
            text     = cue["text"]
            STROKE   = 6
            bbox     = draw.textbbox((0, 0), text, font=font, stroke_width=STROKE)
            tw, th   = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x        = max(STROKE, (TARGET_W - tw) // 2)
            y        = int(TARGET_H * y_ratio) - th // 2
            draw.text(
                (x, y), text,
                font=font,
                fill=(r, g, b, 255),
                stroke_width=STROKE,
                stroke_fill=(0, 0, 0, 255),
            )
            overlays.append({**cue, "_overlay": overlay})
        return overlays

    @staticmethod
    def _composite_text(
        frame: _PIL_Image.Image,
        text_overlays: list,
        t: float,
    ) -> _PIL_Image.Image:
        """Composite active text overlays onto the frame at time t."""
        for cue in text_overlays:
            t_start = float(cue.get("t_start", 0.0))
            t_end   = float(cue.get("t_end",   0.0))
            overlay = cue.get("_overlay")
            if overlay is None or not (t_start <= t < t_end):
                continue

            # Simple fade-in over first 0.3 s (supported for "fade_in" animation)
            animation = cue.get("animation", "")
            alpha_mul = 1.0
            if animation == "fade_in":
                elapsed   = t - t_start
                alpha_mul = min(1.0, elapsed / 0.3)

            if alpha_mul < 1.0:
                r, g, b, a = overlay.split()
                a_scaled   = a.point(lambda px: int(px * alpha_mul))
                overlay    = _PIL_Image.merge("RGBA", (r, g, b, a_scaled))

            frame = _PIL_Image.alpha_composite(frame.convert("RGBA"), overlay)
        return frame.convert("RGBA")

    # =========================================================
    # AUDIO MIX
    # =========================================================

    def _build_audio_mix(
        self,
        audio_segs: list,
        sfx_entries: list,
        voiceover_path: str,
        total_dur: float,
    ) -> CompositeAudioClip | AudioFileClip | None:
        clips = []

        # ── Voiceover (from audio_segs or direct path) ────────
        vo_path = self._find_audio_asset(audio_segs, "voiceover", voiceover_path)
        if vo_path and Path(vo_path).exists():
            try:
                vo = AudioFileClip(str(vo_path))
                if vo.duration > total_dur:
                    vo = vo.subclipped(0, total_dur)
                clips.append(vo)
            except Exception as e:
                logger.warning("โหลด voiceover ล้มเหลว: %s", e)

        # ── BGM ──────────────────────────────────────────────
        bgm_asset = self._find_audio_asset(audio_segs, "bgm", None)
        if bgm_asset is None:
            bgm_asset = self._ensure_bgm()
        if bgm_asset and Path(bgm_asset).exists():
            try:
                bgm_vol = self._find_audio_volume(audio_segs, "bgm", 0.12)
                bgm = AudioFileClip(str(bgm_asset))
                if bgm.duration < total_dur:
                    repeats = int(total_dur / bgm.duration) + 2
                    bgm     = concatenate_audioclips([bgm] * repeats).subclipped(0, total_dur)
                else:
                    bgm = bgm.subclipped(0, total_dur)
                bgm = self._set_volume(bgm, bgm_vol)
                clips.append(bgm)
            except Exception as e:
                logger.warning("BGM ล้มเหลว: %s", e)

        # ── SFX ──────────────────────────────────────────────
        for sfx in sfx_entries:
            asset   = sfx.get("asset")
            t_start = float(sfx.get("t_start", 0.0))
            vol     = float(sfx.get("volume",  0.6))
            if asset and Path(asset).exists():
                try:
                    sfx_clip = AudioFileClip(str(asset))
                    sfx_clip = self._set_volume(sfx_clip, vol)
                    # Offset the SFX clip to start at t_start
                    from moviepy import AudioClip
                    padded = AudioClip(
                        lambda t, clip=sfx_clip, offset=t_start: (
                            clip.get_frame(t - offset)
                            if 0 <= (t - offset) < clip.duration
                            else np.zeros(2)
                        ),
                        duration=total_dur,
                        fps=44100,
                    )
                    clips.append(padded)
                except Exception as e:
                    logger.debug("SFX '%s' ข้าม: %s", sfx.get("type"), e)

        if not clips:
            return None
        if len(clips) == 1:
            return clips[0]
        return CompositeAudioClip(clips)

    @staticmethod
    def _find_audio_asset(audio_segs: list, atype: str, default) -> str | None:
        for seg in audio_segs:
            if seg.get("type") == atype:
                asset = seg.get("asset")
                if asset and Path(asset).exists():
                    return asset
        return default

    @staticmethod
    def _find_audio_volume(audio_segs: list, atype: str, default: float) -> float:
        for seg in audio_segs:
            if seg.get("type") == atype:
                return float(seg.get("volume", default))
        return default

    @staticmethod
    def _set_volume(clip, volume: float):
        """Reduce clip volume — compatible with MoviePy 1.x and 2.x."""
        for method in ("volumex", "multiply_volume", "with_multiply_volume"):
            fn = getattr(clip, method, None)
            if fn:
                try:
                    return fn(volume)
                except Exception:
                    continue
        return clip  # return unchanged if no volume method works

    @staticmethod
    def _ensure_bgm() -> str | None:
        """Download BGM if local cache doesn't exist yet."""
        if BGM_PATH.exists():
            return str(BGM_PATH)
        import requests as _req
        try:
            BGM_PATH.parent.mkdir(parents=True, exist_ok=True)
            r = _req.get(BGM_URL, timeout=20)
            r.raise_for_status()
            BGM_PATH.write_bytes(r.content)
            return str(BGM_PATH)
        except Exception as e:
            logger.warning("ดาวน์โหลด BGM ล้มเหลว: %s", e)
            return None
