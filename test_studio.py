import asyncio
from media_studio import audio_maker, video_maker
import os
import urllib.request

# ==========================================
# ⚙️ PROFESSIONAL MOCK RESOURCES
# ==========================================

# 1. สคริปต์ป้ายยาระดับมืออาชีพ (ฮุกแรง -> ปัญหา -> ทางออก -> CTA)
PROFESSIONAL_SCRIPT = (
    "หยุดดูก่อน! ถ้าไม่อยากหน้าพังไปตลอดชีวิต! "
    "รู้ไหมครับว่า ครีมกันแดดที่คุณใช้อยู่ อาจจะกำลังทำร้ายผิวคุณแบบไม่รู้ตัว "
    "กว่าผมจะเจอตัวนี้ ลองผิดลองถูกมาเยอะมาก... เซรั่มกันแดดเนื้อน้ำ บางเบาสุดๆ "
    "ไม่เหนียวเหนอะหนะ แถมคุมมันได้ทั้งวัน เชื่อผมเถอะ... ไปกดที่ตะกร้าด่วน ก่อนของจะหมด!"
)

# 2. ฟังก์ชันดาวน์โหลดรูปภาพตัวอย่างแบบสวยงาม
def setup_professional_mock_image():
    image_dir = "data/images"
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, "pro_test_product.jpg")
    
    print("📥 กำลังเตรียมรูปภาพสินค้าตัวอย่างระดับ Pro...")
    
    # โหลดรูปขวดสกินแคร์สวยๆ จาก Unsplash (ฟรีลิขสิทธิ์)
    image_url = "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?q=80&w=1080&auto=format&fit=crop"
    
    # เช็คก่อนว่ามีรูปแล้วหรือยัง จะได้ไม่ต้องโหลดใหม่ให้เสียเวลา
    if not os.path.exists(image_path):
        urllib.request.urlretrieve(image_url, image_path)
        print("✅ ดาวน์โหลดรูปภาพสำเร็จ!")
    else:
        print("✅ มีรูปภาพตัวอย่างอยู่แล้ว (ใช้รูปเดิม)")
        
    return image_path

# ==========================================
# 🎬 THE STUDIO WORKFLOW
# ==========================================

async def run_professional_test():
    print("🎬 เริ่มการทดสอบสตูดิโอระดับ PROFESSIONAL...")
    
    # Step 1: เตรียมรูปภาพ
    mock_image_path = setup_professional_mock_image()
    
    # Step 2: สร้างเสียงพากย์ (ใช้เสียงผู้ชายทุ้ม นุ่มลึก ดูน่าเชื่อถือ)
    print("\n🎙️ กำลังสร้างเสียงพากย์ระดับมืออาชีพ...")
    audio_path = await audio_maker.generate_voiceover(
        text=PROFESSIONAL_SCRIPT,
        mode="production"
    )
    
    # Step 3: เรนเดอร์วิดีโอ (🟢 แก้ไข: เติม await ให้เรียบร้อยแล้ว!)
    print("\n🎞️ กำลังเรนเดอร์วิดีโอและซับไตเติ้ล...")
    final_video = await video_maker.create_video(
        script_text=PROFESSIONAL_SCRIPT,
        image_path=mock_image_path,
        audio_path=audio_path,
        mode="production" 
    )
    
    print(f"\n✅ การทดสอบเสร็จสมบูรณ์! เช็คผลงานได้ที่: {final_video}")

if __name__ == "__main__":
    asyncio.run(run_professional_test())