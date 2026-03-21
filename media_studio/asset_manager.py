"""
AssetManager — SFX & Meme Overlay Cache for A.Z.E. Timeline Renderer
Downloads and caches media assets referenced in JSON blueprints.
"""

import copy
import logging
import requests
from pathlib import Path

logger = logging.getLogger("AZE.asset_manager")

SFX_DIR  = Path("data/sfx")
MEME_DIR = Path("data/memes")

# =========================================================
# FREE CC0 SFX (Pixabay CDN — no API key required)
# =========================================================
_SFX_URLS: dict[str, str] = {
    "whoosh":        "https://cdn.pixabay.com/audio/2022/03/10/audio_270f30aff8.mp3",
    "ding":          "https://cdn.pixabay.com/audio/2021/08/04/audio_12b0c7443c.mp3",
    "cash_register": "https://cdn.pixabay.com/audio/2021/08/04/audio_c8834d57e0.mp3",
    "pop":           "https://cdn.pixabay.com/audio/2021/08/09/audio_dc39bede17.mp3",
    "swoosh":        "https://cdn.pixabay.com/audio/2022/03/10/audio_270f30aff8.mp3",
}

# Meme image slot → filename under data/memes/ (place files there manually)
_MEME_FILES: dict[str, str] = {
    "shocked_face": "shocked_face.png",
    "money_eyes":   "money_eyes.png",
    "zombie_flex":  "zombie_flex.png",
    "price_tag":    "price_tag.png",
}


class AssetManager:
    """Resolve, download, and cache SFX + meme overlay assets for the blueprint system."""

    def __init__(self):
        SFX_DIR.mkdir(parents=True, exist_ok=True)
        MEME_DIR.mkdir(parents=True, exist_ok=True)

    # =========================================================
    # SFX
    # =========================================================
    def resolve_sfx(self, sfx_type: str) -> Path | None:
        """
        Return cached local path for an SFX clip.
        Downloads on first use. Returns None on failure — caller must skip gracefully.
        """
        if not sfx_type:
            return None

        local = SFX_DIR / f"{sfx_type}.mp3"
        if local.exists():
            return local

        url = _SFX_URLS.get(sfx_type)
        if not url:
            logger.debug("SFX '%s' ไม่มี URL ในระบบ — ข้าม", sfx_type)
            return None

        try:
            logger.info("กำลังดาวน์โหลด SFX '%s' ...", sfx_type)
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            local.write_bytes(resp.content)
            logger.info("ดาวน์โหลด SFX '%s' สำเร็จ → %s", sfx_type, local)
            return local
        except Exception as exc:
            logger.warning("ดาวน์โหลด SFX '%s' ล้มเหลว: %s — ข้าม SFX นี้", sfx_type, exc)
            return None

    # =========================================================
    # MEME OVERLAYS
    # =========================================================
    def resolve_meme(self, name: str) -> Path | None:
        """Return local path for a meme overlay image, or None if not found."""
        if not name:
            return None
        filename = _MEME_FILES.get(name, f"{name}.png")
        local = MEME_DIR / filename
        if local.exists():
            return local
        logger.debug("Meme '%s' ไม่พบใน %s — ข้าม", name, MEME_DIR)
        return None

    # =========================================================
    # BLUEPRINT VERIFICATION
    # =========================================================
    def verify_blueprint_assets(self, blueprint: dict) -> dict:
        """
        Scan a blueprint for SFX and meme assets, resolving/downloading each.
        Returns a deep copy with asset paths filled in (or None for unavailable ones).
        Does NOT mutate the input.
        """
        bp = copy.deepcopy(blueprint)

        # Resolve SFX
        for seg in bp.get("sfx_track", []):
            sfx_type = seg.get("type", "")
            local    = self.resolve_sfx(sfx_type)
            seg["asset"] = str(local) if local else None

        # Resolve meme_overlay segments in video_track
        for seg in bp.get("video_track", []):
            if seg.get("type") == "meme_overlay":
                meme_name = seg.get("asset", "")
                local     = self.resolve_meme(meme_name)
                seg["asset"] = str(local) if local else None

        return bp
