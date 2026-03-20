import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# NOTE: genai.Client ถูกสร้างแบบ Lazy — เฟ้า production mode เท่านั้น
# ไม่มีการเชื่อมต่อ Google API ใดๆ ในโหมด mock

PROMPTS_DIR = Path("prompts")

# Platform → prompt file mapping
PLATFORM_PROMPTS = {
    "tiktok":  PROMPTS_DIR / "tiktok_script.txt",
    "shorts":  PROMPTS_DIR / "shorts_script.txt",
    "reels":   PROMPTS_DIR / "reels_script.txt",
}
# Legacy generator.txt ยังใช้ได้เป็น default
DEFAULT_PROMPT_FILE = PROMPTS_DIR / "generator.txt"


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_script(file_path, script):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(script)

def _load_prompt_template(platform: str) -> str:
    """โหลด prompt template ตาม platform (tiktok/shorts/reels)"""
    prompt_file = PLATFORM_PROMPTS.get(platform.lower(), DEFAULT_PROMPT_FILE)
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return DEFAULT_PROMPT_FILE.read_text(encoding="utf-8")

def _load_context_file(path: str, default: str = "") -> str:
    """โหลด context file ถ้ามี (trend_report, winning_patterns)"""
    try:
        p = Path(path)
        if p.exists():
            return p.read_text(encoding="utf-8")
    except Exception:
        pass
    return default

# =========================================================
# ZOMB PERSONA — System Prompt สำหรับ Production (Legacy)
# =========================================================
ZOMB_SYSTEM_PROMPT = """\
คุณคือ "ซอมบ์ (Zomb)" ซอมบี้หนุ่มหล่อมาดเท่ เสียงนุ่มลึก มีอารมณ์ขันแบบดาร์กๆ (Dark Humor) \
และชอบประชดประชันชีวิตหลังความตาย. คุณไม่กินสมอง แต่คุณชอบป้ายยาสินค้าให้มนุษย์!

กฎการเขียนสคริปต์วิดีโอแนวตั้ง (ไม่เกิน 40 วินาที):
1. [Hook 10 วินาที]: เปิดคลิปด้วยเรื่องลี้ลับ เรื่องน่ากลัว หรือปรัชญาชีวิตความตายที่ดูเท่และน่าติดตาม \
(ห้ามพูดเรื่องขายของในส่วนนี้)
2. [Plot Twist 15 วินาที]: หักมุมฉีกอารมณ์แบบกาวๆ โยงเข้าหาสินค้าที่ได้รับข้อมูลมาแบบดื้อๆ แต่เนียนและตลก
3. [Call to Action 5 วินาที]: สั่งให้มนุษย์ไปกดซื้อที่ตะกร้า/ลิงก์ ด้วยน้ำเสียงหล่อๆ ผสมข่มขู่นิดๆ

ข้อกำหนดภาษา:
- ใช้ภาษาไทยวัยรุ่น เป็นธรรมชาติ คุยเหมือนเพื่อนหรือรุ่นพี่ที่หล่อและอันตราย
- ใส่สัญลักษณ์ [Pause] เพื่อเว้นจังหวะหายใจให้ AI Voiceover
- ห้ามใช้คำทางการ ห้ามลงท้ายด้วย ครับ/ค่ะ บ่อยเกินไป \
ให้ใช้คำว่า "พวกมนุษย์", "เชื่อเฮีย", หรือ "ไปกดซะ"

ข้อมูลสินค้าที่ต้องป้ายยา:
{product_data}
"""

MOCK_SCRIPTS = {
    "tiktok": """\
[Hook]
สิ่งที่ซอมบี้กลัวที่สุดในโลก... [Pause] ไม่ใช่ garlic นะ

[Plot Twist]
คือแดดตอนบ่ายสามโมง [Pause] เฮียเลยใช้ร่มกันแดด ราคา 199 กันแดดได้ 100% เชื่อเฮีย [Trending Sound Cue]

[CTA]
กดตะกร้าเหลืองด้านล่าง ไปซะก่อนเฮียจะตามถึงบ้าน 🧟\
""",
    "shorts": """\
[Chapter: Hook]
รู้มั้ย? ซอมบี้ตาย แต่ผิวไม่พัง [Pause] เพราะอะไร?

[Chapter: Value Content]
เหตุผลคือ UPF50+ ที่เฮียใช้ทุกวัน [Pause] ร่มกันแดดซอมบี้ 199 บาท กันแดดได้ทั้งวัน \
เนื้อหาที่ดีที่สุดในราคาที่ถูกที่สุด ของแท้จาก Shopee [Pause] \
เฮียทดสอบมา 200 ปีแล้ว ยังไม่ไหม้สักที

[Chapter: CTA]
Subscribe แล้วกดลิงก์ในคำอธิบาย ก่อนของหมด 🧟 #ซอมบี้รีวิว\
""",
    "reels": """\
[Emotional Hook]
เคยโดนแดดเผาจนหน้าดำมั้ย? [Pause] เฮียก็เคย...

[Story + Product]
แต่ตอนนี้ เฮียใช้ร่มกันแดดซอมบี้ 199 บาท [Pause] หน้าสว่างขึ้น ชีวิตดีขึ้น แม้จะตายไปแล้วก็ตาม

[Share Bait + CTA]
Save ไว้ก่อนนะ ส่งให้เพื่อนที่ยังไม่รู้จะซื้ออะไร 🧟
#ซอมบี้รีวิว #ของดีบอกต่อ #กันแดด #affiliate #ราคาถูก\
""",
}

def generate_script(product_data, mode: str = "mock", platform: str = "tiktok"):
    """
    สร้างสคริปต์ Zomb ตาม platform

    Args:
        product_data : list/dict ข้อมูลสินค้าจาก raw_data.json
        mode         : "mock" = ไม่เรียก Gemini | "production" = เรียก Gemini
        platform     : "tiktok" | "shorts" | "reels"
    """
    # =========================================================
    # MOCK MODE — ไม่เรียก Gemini API ประหยัดโควต้า
    # =========================================================
    if mode == "mock":
        script = MOCK_SCRIPTS.get(platform, MOCK_SCRIPTS["tiktok"])
        print(f"✍️ [MOCK] เขียนสคริปต์ Zomb ({platform.upper()}) จำลองสำเร็จ — ไม่เรียก Gemini API")
        return script

    # =========================================================
    # PRODUCTION MODE — ส่ง Platform Prompt + Context ไปยัง Gemini
    # =========================================================
    from google import genai as _genai  # Lazy import

    # โหลด trend + adaptive context (ถ้ามี)
    trend_ctx    = _load_context_file("data/trend_report.json",
                                       default="(ยังไม่มี trend data)")
    adaptive_ctx = _load_context_file("data/winning_patterns.json",
                                       default="(ยังไม่มี adaptive data)")

    product_json  = json.dumps(product_data, ensure_ascii=False, indent=2)
    prompt_tmpl   = _load_prompt_template(platform)
    full_prompt   = prompt_tmpl.format(
        product_data    = product_json,
        trend_context   = f"=== TREND DATA ===\n{trend_ctx}" if trend_ctx else "",
        adaptive_context= f"=== WINNING PATTERNS ===\n{adaptive_ctx}" if adaptive_ctx else "",
    )

    # โหลด Resource Manager สำหรับ quota tracking
    try:
        from core.resource_manager import ResourceManager
        rm = ResourceManager()
        client = rm.get_gemini_client()
        model  = rm.get_gemini_model()
    except Exception:
        client = _genai.Client(api_key=GEMINI_API_KEY)
        model  = "gemini-2.5-flash"

    try:
        response = client.models.generate_content(model=model, contents=full_prompt)
        script = response.text
        print(f"✍️ [PRODUCTION] Zomb เขียนสคริปต์ {platform.upper()} สำเร็จ!")
        # บันทึก quota usage
        try:
            from core.resource_manager import ResourceManager
            ResourceManager().track_gemini_usage()
        except Exception:
            pass
        return script
    except Exception as e:
        print(f"❌ Gemini API Error ({platform}): {e} — Fallback สคริปต์จำลอง")
        return MOCK_SCRIPTS.get(platform, MOCK_SCRIPTS["tiktok"])


def main(mode: str = "mock", platforms: list | None = None):
    """
    สร้างสคริปต์ทุก platform ที่กำหนด

    platforms: ["tiktok"] (default) | ["tiktok","shorts","reels"] (all)
    """
    if platforms is None:
        platforms = ["tiktok"]

    product_data = read_json("data/raw_data.json")

    for platform in platforms:
        script = generate_script(product_data, mode=mode, platform=platform)
        # บันทึกแยกไฟล์ตาม platform
        out_path = f"data/generated_script_{platform}.txt"
        save_script(out_path, script)
        print(f"💾 [{platform.upper()}] บันทึกสคริปต์ → {out_path}")

    # backward compat: ยัง save generated_script.txt (ใช้ tiktok เป็น default)
    primary = generate_script(product_data, mode=mode, platform=platforms[0])
    save_script("data/generated_script.txt", primary)
    print(f"💾 บันทึกสคริปต์หลัก → data/generated_script.txt")

if __name__ == "__main__":
    main()
