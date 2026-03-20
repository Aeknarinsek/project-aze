import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# NOTE: genai.Client ถูกสร้างแบบ Lazy — เฟ้า production mode เท่านั้น
# ไม่มีการเชื่อมต่อ Google API ใดๆ ในโหมด mock

def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_script(file_path, script):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(script)

# =========================================================
# ZOMB PERSONA — System Prompt สำหรับ Production
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

MOCK_SCRIPT = """\
[Hook]
รู้มั้ย... ซอมบี้ที่แข็งแกร่งที่สุดในโลกหลังความตาย [Pause] ไม่กลัวอะไรเลย

[Plot Twist]
...ยกเว้นแดดตอนบ่ายสามโมง [Pause] เฮียเลยใช้ร่มกันแดดซอมบี้ ราคา 199 กันแดดได้ 100% เชื่อเฮีย

[Call to Action]
พวกมนุษย์ [Pause] ไปกดซะ ก่อนเฮียจะตามไปถึงบ้าน 🧟 #ซอมบี้รีวิว #ร่มกันแดด
"""


def generate_script(product_data, mode: str = "mock"):
    # =========================================================
    # MOCK MODE — ไม่เรียก Gemini API ประหยัดโควต้า
    # =========================================================
    if mode == "mock":
        print("✍️ [MOCK] เขียนสคริปต์ Zomb จำลองสำเร็จ — ไม่เรียก Gemini API")
        return MOCK_SCRIPT

    # =========================================================
    # PRODUCTION MODE — ส่ง Zomb Persona Prompt ไปยัง Gemini
    # =========================================================
    from google import genai as _genai  # Lazy import — โหลดเฉพาะตอนใช้งานจริง
    client = _genai.Client(api_key=GEMINI_API_KEY)
    product_json = json.dumps(product_data, ensure_ascii=False, indent=2)
    full_prompt = ZOMB_SYSTEM_PROMPT.format(product_data=product_json)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )
        script = response.text
        print("✍️ [PRODUCTION] Zomb เขียนสคริปต์สำเร็จ!")
        return script
    except Exception as e:
        print(f"❌ Gemini API Error: {e} — Fallback สคริปต์จำลอง")
        return MOCK_SCRIPT


def main(mode: str = "mock"):
    product_data = read_json("data/raw_data.json")
    script = generate_script(product_data, mode=mode)
    save_script("data/generated_script.txt", script)
    print(f"💾 บันทึกสคริปต์ไปที่ data/generated_script.txt แล้ว")

if __name__ == "__main__":
    main()