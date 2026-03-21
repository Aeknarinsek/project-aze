"""
setup_mascot.py — Auto Mascot Generator for A.Z.E.
Generates master_zombie.png using pollinations.ai (no API key required).
Falls back to a stylised Pillow placeholder if the API is unavailable.
"""

import urllib.parse
from pathlib import Path

SAVE_PATH = Path("assets/character/master_zombie.png")
PROMPT    = (
    "A handsome male zombie, pale skin, slightly red lips, "
    "K-Pop idol style, cool techwear clothing, "
    "masterpiece, highly detailed portrait, white background"
)
WIDTH, HEIGHT = 768, 1024

# Ordered list of (model_name, extra_qs) — try each in turn
_MODELS = [
    "flux",
    "flux-realism",
    "turbo",
    "",                # default / no model param
]


def _build_url(model: str) -> str:
    encoded = urllib.parse.quote(PROMPT)
    base    = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={WIDTH}&height={HEIGHT}&nologo=true&enhance=true"
    )
    if model:
        base += f"&model={model}"
    return base


# =========================================================
# FALLBACK: generate a styled placeholder PNG using Pillow
# =========================================================
def _generate_placeholder() -> bytes:
    """Create a Zombie-themed placeholder card as PNG bytes via Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    import io

    canvas = Image.new("RGB", (WIDTH, HEIGHT), color=(15, 8, 20))
    draw   = ImageDraw.Draw(canvas)

    # Dark gradient-like bands
    for y in range(0, HEIGHT, 4):
        alpha = int(20 * (y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(alpha, 0, alpha + 10))

    # Zombie silhouette (simple geometric stand-in)
    cx = WIDTH // 2
    # Body
    draw.ellipse([cx - 160, 180, cx + 160, 500], fill=(180, 220, 180))   # face
    draw.ellipse([cx - 120, 460, cx + 120, 800], fill=(100, 130, 100))   # torso
    # Eyes
    draw.ellipse([cx - 80, 280, cx - 20, 340], fill=(255, 80, 80))
    draw.ellipse([cx + 20, 280, cx + 80, 340], fill=(255, 80, 80))
    # Pupils
    draw.ellipse([cx - 60, 298, cx - 38, 322], fill=(10, 0, 0))
    draw.ellipse([cx + 38, 298, cx + 62, 322], fill=(10, 0, 0))
    # Mouth
    draw.arc([cx - 60, 360, cx + 60, 430], start=0, end=180, fill=(180, 40, 40), width=8)

    # Title
    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
        font_sub   = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   36)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub   = font_title

    title = "ZOMB 🧟"
    draw.text((cx, 840), title, font=font_title, fill=(255, 230, 0), anchor="mm")
    draw.text((cx, 930), "A.Z.E. Mascot", font=font_sub, fill=(200, 200, 200), anchor="mm")
    draw.text((cx, 980), "(placeholder — replace with real art)", font=font_sub,
              fill=(120, 120, 120), anchor="mm")

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


# =========================================================
# MAIN
# =========================================================
def generate():
    import requests

    SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "AZE-MascotBot/1.0"}

    print("🧟 กำลังสร้าง Mascot จาก pollinations.ai...")
    print(f"   Prompt : {PROMPT}")
    print(f"   Size   : {WIDTH}x{HEIGHT}")
    print("   กรุณารอสักครู่ (ใช้เวลาประมาณ 15–60 วินาที)...")

    for model in _MODELS:
        url   = _build_url(model)
        label = model if model else "default"
        print(f"\n   ▶ ลอง model={label!r}")
        try:
            resp = requests.get(url, headers=headers, timeout=120, allow_redirects=True)
            ctype = resp.headers.get("Content-Type", "")
            if resp.status_code == 200 and "image" in ctype and len(resp.content) > 10_000:
                SAVE_PATH.write_bytes(resp.content)
                print(f"\n✅ บันทึกสำเร็จ → {SAVE_PATH}  ({len(resp.content):,} bytes)")
                print("🎉 Mascot พร้อมใช้งาน! CEO ไม่ต้องขยับนิ้วเลย 🧟\u200d♂️")
                return
            else:
                snippet = resp.content[:200].decode("utf-8", errors="replace")
                print(f"   ⚠️  HTTP {resp.status_code} | Content-Type: {ctype!r} | "
                      f"Size: {len(resp.content)} bytes | Body: {snippet!r}")
        except Exception as exc:
            print(f"   ⚠️  Error: {exc}")

    # ── All API attempts failed → generate locally via Pillow ──
    print("\n⚙️  pollinations.ai ไม่ตอบสนอง — กำลังสร้าง placeholder ด้วย Pillow...")
    data = _generate_placeholder()
    SAVE_PATH.write_bytes(data)
    print(f"✅ Placeholder บันทึกแล้ว → {SAVE_PATH}  ({len(data):,} bytes)")
    print("💡 CEO สามารถแทนที่ด้วยรูปจริงภายหลังได้ที่ assets/character/master_zombie.png")


if __name__ == "__main__":
    generate()
