import re
import logging
import numpy as np
import requests
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
from PIL import Image as _PIL_Image

logger = logging.getLogger("AZE.video_maker")

from moviepy import (
    VideoClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_audioclips,
)

# =========================================================
# CONFIG
# =========================================================
FINAL_VIDEO_PATH = Path("data/final_video.mp4")
MOCK_VIDEO_PATH  = "data/mock_final_video.mp4"
BGM_PATH         = Path("data/bgm.mp3")
# Royalty-free test music (SoundHelix — free for development use)
BGM_URL          = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

TARGET_W, TARGET_H = 1080, 1920
# Kanit Bold — Google Thai Font (modern, crisp on FreeType/RAQM)
_FONT_DIR       = Path(__file__).resolve().parent.parent / "data" / "fonts"
THAI_FONT       = str(_FONT_DIR / "kanit.ttf")
THAI_FONT_FALLBACK = "C:/Windows/Fonts/tahoma.ttf"
BGM_VOLUME = 0.12   # 12% — ไม่กลบเสียงพากย์
MAX_VIDEO_DURATION = 55.0  # วินาที — CQO บังคับ: วิดีโอต้องไม่เกิน 60s (เผื่อ buffer 5s)


def _load_thai_font(size: int) -> ImageFont.FreeTypeFont:
    """
    โหลด Kanit Bold พร้อม RAQM layout engine (proper Thai vowel shaping).
    Fallback chain: Kanit+RAQM → Kanit+FreeType → Tahoma → default
    """
    import warnings
    for font_path in [THAI_FONT, THAI_FONT_FALLBACK]:
        # ลอง RAQM ก่อน (suppress UserWarning เมื่อ libraqm ไม่ได้ติดตั้ง)
        for use_raqm in [True, False]:
            try:
                kwargs = {"layout_engine": ImageFont.Layout.RAQM} if use_raqm else {}
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    fnt = ImageFont.truetype(font_path, size, **kwargs)
                raqm_ok = use_raqm and not any("Raqm" in str(w.message) for w in caught)
                engine_label = "RAQM" if raqm_ok else "FreeType"
                print(f"   ✅ Font: {Path(font_path).name} [{engine_label}]")
                return fnt
            except Exception:
                continue
    print("   ⚠️  ใช้ default font (Kanit/Tahoma ไม่พบ)")
    return ImageFont.load_default()


# =========================================================
# HELPERS
# =========================================================

def _strip_tags_and_emojis(text: str) -> str:
    """ลบ [stage direction] และ Emoji ออกจากสคริปต์"""
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"[^\u0000-\u07FF\u0E00-\u0E7F\u200B-\u200D!?.,\- ]", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def chunk_text_for_subtitles(script_text: str, max_chars: int = 10) -> list:
    """
    หั่นสคริปต์เป็นซับไตเติ้ลสั้นสไตล์ Alex Hormozi / TikTok Pro
    - ใช้ pythainlp ตัดคำภาษาไทยอย่างถูกต้อง (ไม่ตัดกลางคำ)
    - สะสมคำจนถึง max_chars (default 15) แล้วขึ้น chunk ใหม่
    - ข้อความแต่ละ chunk สั้น อยู่บรรทัดเดียวกลางจอได้สบาย
    Returns: list of str
    """
    try:
        from pythainlp.tokenize import word_tokenize
        clean = _strip_tags_and_emojis(script_text)
        # newmm engine — แม่นยำสูง, รองรับคำสแลงวัยรุ่น
        words = word_tokenize(clean, engine="newmm", keep_whitespace=False)
        words = [w.strip() for w in words if w.strip()]
    except Exception:
        # Fallback: แบ่งด้วย whitespace ธรรมดาถ้า pythainlp พัง
        clean = _strip_tags_and_emojis(script_text)
        words = clean.split()

    chunks: list = []
    current = ""
    for word in words:
        candidate = current + word if current else word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            # คำเดียวยาวเกิน max_chars → เป็น chunk ของตัวเองทั้งคำ (ไม่ตัดกลาง)
            current = word
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if c]


def _make_video_with_subtitles(
    img_array: np.ndarray,
    duration: float,
    chunks: list,
    subtitle_y_ratio: float = 0.85,
    font_size: int = 95,
) -> VideoClip:
    """
    Ken Burns + Kanit Bold PIL Subtitles ใน pass เดียว
    - Kanit Bold Google Font (Thai-optimised)
    - RAQM layout engine → สระไม่ทับซ้อน
    - Native Pillow stroke_width → anti-aliased outline
    - subtitle_y_ratio=0.85 → bottom 15% ไม่บังสินค้า
    """
    h, w = img_array.shape[:2]
    pil_src = _PIL_Image.fromarray(img_array)

    font = _load_thai_font(font_size)
    chunk_dur = (duration / len(chunks)) if chunks else duration
    stroke_px = 6

    # Pre-render RGBA overlay per chunk — ครั้งเดียว ไม่ซ้ำใน hot loop
    subtitle_overlays: list = []
    for i, text in enumerate(chunks):
        overlay = _PIL_Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
        draw    = ImageDraw.Draw(overlay)
        fill    = (255, 230, 0, 255) if i % 2 == 0 else (255, 255, 255, 255)
        # วัดขนาดข้อความ (รวม stroke)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_px)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]
        x    = max(stroke_px, (TARGET_W - tw) // 2)
        y    = int(TARGET_H * subtitle_y_ratio) - th // 2
        # วาดข้อความพร้อม stroke ในคำสั่งเดียว (Pillow ≥9 native — anti-aliased)
        draw.text(
            (x, y), text,
            font=font,
            fill=fill,
            stroke_width=stroke_px,
            stroke_fill=(0, 0, 0, 255),
        )
        subtitle_overlays.append(overlay)

    def make_frame(t: float) -> np.ndarray:
        # Ken Burns slow zoom 100 % → 108 %
        progress = t / duration if duration > 0 else 0
        scale    = 1.0 + 0.08 * progress
        crop_w   = int(w / scale)
        crop_h   = int(h / scale)
        x1 = (w - crop_w) // 2
        y1 = (h - crop_h) // 2
        frame = pil_src.crop((x1, y1, x1 + crop_w, y1 + crop_h))
        frame = frame.resize((TARGET_W, TARGET_H), _PIL_Image.Resampling.LANCZOS).convert("RGBA")
        if subtitle_overlays and chunk_dur > 0:
            idx   = min(int(t / chunk_dur), len(subtitle_overlays) - 1)
            frame = _PIL_Image.alpha_composite(frame, subtitle_overlays[idx])
        return np.array(frame.convert("RGB"))

    return VideoClip(make_frame, duration=duration).with_fps(24)


def _download_bgm() -> str | None:
    """ดาวน์โหลด BGM ครั้งแรก บันทึก cache ที่ data/bgm.mp3"""
    if BGM_PATH.exists():
        print(f"   BGM cache พบแล้ว: {BGM_PATH}")
        return str(BGM_PATH)
    try:
        print("   กำลังดาวน์โหลด Background Music...")
        BGM_PATH.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(BGM_URL, timeout=20)
        r.raise_for_status()
        BGM_PATH.write_bytes(r.content)
        print(f"   ดาวน์โหลด BGM สำเร็จ → {BGM_PATH}")
        return str(BGM_PATH)
    except Exception as e:
        print(f"   ดาวน์โหลด BGM ล้มเหลว: {e} — ข้าม BGM")
        return None


# =========================================================
# MAIN
# =========================================================

async def create_video(
    script_text: str = "",
    image_path: str  = "data/images/processed_product.jpg",
    audio_path: str  = "data/voiceover.mp3",
    mode: str        = "mock",
) -> str:
    """
    ประกอบร่างวิดีโอ TikTok Affiliate มาตรฐาน:
      - Ken Burns zoom effect
      - Dynamic captions (สั้นๆ ทีละท่อน สลับเหลือง/ขาว)
      - BGM ผสมเสียงพากย์ที่ระดับ 12%
    """

    # =========================================================
    # MOCK MODE
    # =========================================================
    if mode == "mock":
        print("🎬 [MOCK] ตัดต่อวิดีโอจำลองสำเร็จ ประหยัดเวลา 100%")
        return MOCK_VIDEO_PATH

    # =========================================================
    # PRODUCTION MODE
    # =========================================================
    print("🎬 [PRODUCTION] ผลิตคลิป TikTok Affiliate ระดับมืออาชีพ...")
    audio_clip = None
    final_clip = None

    try:
        # --- 1. โหลดเสียงพากย์ ---
        audio_src = Path(audio_path)
        if not audio_src.exists():
            raise FileNotFoundError(f"ไม่พบไฟล์เสียง: {audio_path}")
        audio_clip    = AudioFileClip(str(audio_src))
        total_duration = audio_clip.duration
        print(f"   เสียงพากย์: {total_duration:.2f} วินาที")

        # CQO Rule: วิดีโอต้องไม่เกิน 60 วินาที → ตัด hard ที่ 55s
        if total_duration > MAX_VIDEO_DURATION:
            print(f"   ⚠️  เสียงยาวเกิน ({total_duration:.1f}s) → ตัดให้พอดี {MAX_VIDEO_DURATION}s (CQO mandate)")
            audio_clip     = audio_clip.subclipped(0, MAX_VIDEO_DURATION)
            total_duration = MAX_VIDEO_DURATION

        # --- 2. Ken Burns Zoom Effect ---
        img_src = Path(image_path)
        if not img_src.exists():
            raise FileNotFoundError(f"ไม่พบไฟล์รูปภาพ: {image_path}")

        with Image.open(img_src) as img:
            img_rgb = img.convert("RGB")
            if img_rgb.size != (TARGET_W, TARGET_H):
                img_rgb = ImageOps.fit(img_rgb, (TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
            bg_array = np.array(img_rgb)

        # --- 3. Ken Burns + PIL Subtitle Composite (ไม่ผ่าน ImageMagick) ---
        chunks = chunk_text_for_subtitles(script_text)
        print(f"   สร้าง Ken Burns + Kanit Captions {len(chunks)} ท่อน (RAQM shaping)...")
        final_clip = _make_video_with_subtitles(
            bg_array,
            total_duration,
            chunks,
            subtitle_y_ratio=0.85,
            font_size=95,
        )

        # --- 5. BGM + Voiceover Mix ---
        bgm_src = _download_bgm()
        if bgm_src and Path(bgm_src).exists():
            try:
                bgm = AudioFileClip(bgm_src)
                # Loop BGM ให้พอดีกับความยาวคลิป
                if bgm.duration < total_duration:
                    repeats  = int(total_duration / bgm.duration) + 2
                    bgm_loop = concatenate_audioclips([bgm] * repeats)
                    bgm      = bgm_loop.subclipped(0, total_duration)
                else:
                    bgm = bgm.subclipped(0, total_duration)
                # ลดระดับเสียง BGM ลงเหลือ 12% (รองรับทั้ง moviepy 1.x และ 2.x)
                try:
                    bgm = bgm.volumex(BGM_VOLUME)
                except AttributeError:
                    try:
                        bgm = bgm.multiply_volume(BGM_VOLUME)
                    except AttributeError:
                        pass  # ถ้าลดเสียงไม่ได้ก็ปล่อย BGM เต็มระดับไปก่อน
                mixed = CompositeAudioClip([audio_clip, bgm])
                final_clip = final_clip.with_audio(mixed)
                print(f"   BGM ผสมแล้ว (ระดับ {int(BGM_VOLUME*100)}%)")
            except Exception as e:
                print(f"   ผสม BGM ล้มเหลว: {e} — ใช้เสียงพากย์อย่างเดียว")
                final_clip = final_clip.with_audio(audio_clip)
        else:
            final_clip = final_clip.with_audio(audio_clip)

        # --- 6. Render ---
        FINAL_VIDEO_PATH.parent.mkdir(parents=True, exist_ok=True)
        print("⏳ Rendering... (fps=24, threads=4)")
        final_clip.write_videofile(
            str(FINAL_VIDEO_PATH),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None,
        )

        print(f"✅ คลิประดับมืออาชีพพร้อมแล้ว → {FINAL_VIDEO_PATH}")
        return str(FINAL_VIDEO_PATH)

    except Exception as e:
        logger.error(
            "video_maker failed",
            exc_info=True,
            extra={"image_path": image_path, "audio_path": audio_path},
        )
        return MOCK_VIDEO_PATH

    finally:
        if final_clip:
            final_clip.close()
        if audio_clip:
            audio_clip.close()


# =========================================================
# BLUEPRINT-BASED RENDER (Human-Like Pro Editor)
# =========================================================

async def create_video_from_blueprint(
    blueprint: dict,
    audio_path: str = "data/voiceover.mp3",
    output_path: str = str(FINAL_VIDEO_PATH),
    mode: str = "mock",
) -> str:
    """
    Render a finished MP4 from a Gemini-generated JSON blueprint.
    Falls back gracefully to create_video() if the renderer fails.

    Args:
        blueprint   : dict — JSON blueprint from generate_timeline()
        audio_path  : str  — path to the voiceover .mp3
        output_path : str  — where to save the output .mp4
        mode        : "mock" | "production"
    Returns:
        str — path to the rendered video
    """
    if mode == "mock":
        print("🎬 [MOCK] Blueprint render จำลองสำเร็จ — ข้าม TimelineRenderer")
        return MOCK_VIDEO_PATH

    try:
        from media_studio.asset_manager    import AssetManager
        from media_studio.timeline_renderer import TimelineRenderer

        print("🎬 [BLUEPRINT] Human-Like Pro Editor กำลัง render...")
        verified_bp = AssetManager().verify_blueprint_assets(blueprint)
        result      = TimelineRenderer().render(verified_bp, audio_path, output_path)
        return result

    except Exception as exc:
        logger.error("Blueprint render ล้มเหลว → fallback create_video(): %s", exc, exc_info=True)
        # Graceful fallback to legacy renderer
        script_text = ""
        for cue in blueprint.get("text_track", []):
            if cue.get("style") != "pause" and cue.get("text"):
                script_text += cue["text"] + " "
        return await create_video(
            script_text=script_text.strip(),
            image_path="data/images/processed_product.jpg",
            audio_path=audio_path,
            mode=mode,
        )