import asyncio
from pathlib import Path

# =========================================================
# CONFIG
# =========================================================
VOICEOVER_PATH = Path("data/voiceover.mp3")
MOCK_VOICEOVER_PATH = "data/mock_voiceover.mp3"

# เสียงซอมบ์ — ผู้ชายทุ้มลึก ภาษาไทย
ZOMB_VOICE = "th-TH-NiwatNeural"
ZOMB_RATE  = "-10%"   # ช้าลงนิดนึง ให้หล่อเท่


async def generate_voiceover(text: str, mode: str = "mock") -> str:
    """
    แปลง text เป็นเสียงพากย์ซอมบ์

    Args:
        text: สคริปต์ที่ต้องการแปลงเป็นเสียง
        mode: "mock" = ข้ามการสร้างเสียง | "production" = สร้างเสียงจริง
    Returns:
        path ของไฟล์ .mp3
    """

    # =========================================================
    # MOCK MODE — ไม่รัน edge-tts ประหยัดเวลา
    # =========================================================
    if mode == "mock":
        print("🎙️ [MOCK] สร้างเสียงพากย์จำลองสำเร็จ — ข้าม edge-tts")
        return MOCK_VOICEOVER_PATH

    # =========================================================
    # PRODUCTION MODE — ใช้ edge-tts สร้างเสียงซอมบ์
    # =========================================================
    try:
        import edge_tts  # import ตรงนี้เพื่อไม่ให้ mock mode โหลดโมดูลโดยเปล่าประโยชน์

        VOICEOVER_PATH.parent.mkdir(parents=True, exist_ok=True)

        # ตัด tag เช่น [Hook], [Pause], [Plot Twist] ออกก่อนส่งเสียง
        clean_text = _strip_stage_directions(text)

        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=ZOMB_VOICE,
            rate=ZOMB_RATE
        )
        await communicate.save(str(VOICEOVER_PATH))

        print(f"🎙️ [PRODUCTION] สร้างเสียงพากย์ซอมบ์สำเร็จ → {VOICEOVER_PATH}")
        return str(VOICEOVER_PATH)

    except Exception as e:
        print(f"❌ edge-tts error (อาจเน็ตหลุด): {e}")
        print("⚠️  Fallback → ใช้ path จำลองเพื่อไม่ให้ระบบหยุดชะงัก")
        return MOCK_VOICEOVER_PATH


def _strip_stage_directions(text: str) -> str:
    """ตัด tag เช่น [Hook], [Pause], [Plot Twist], [Call to Action] ออกจากสคริปต์"""
    import re
    # ลบ [ข้อความในวงเล็บเหลี่ยม] ทั้งหมด
    cleaned = re.sub(r"\[.*?\]", "", text)
    # ยุบ whitespace ซ้ำๆ
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


if __name__ == "__main__":
    sample = """
[Hook]
รู้มั้ย... ซอมบี้ที่แข็งแกร่งที่สุดในโลกหลังความตาย [Pause] ไม่กลัวอะไรเลย

[Plot Twist]
...ยกเว้นแดดตอนบ่ายสามโมง [Pause] เฮียเลยใช้ร่มกันแดดซอมบี้ ราคา 199 เชื่อเฮีย

[Call to Action]
พวกมนุษย์ [Pause] ไปกดซะ ก่อนเฮียจะตามไปถึงบ้าน
"""
    asyncio.run(generate_voiceover(sample, mode="production"))
