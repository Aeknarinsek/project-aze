from pathlib import Path
from PIL import Image, ImageOps

# =========================================================
# CONFIG
# =========================================================
IMAGES_DIR       = Path("data/images")
MOCK_IMAGE_PATH  = "data/images/mock_product.jpg"

# ขนาดกรอบสินค้า (สี่เหลี่ยมจัตุรัสตรงกลางจอแนวตั้ง)
PRODUCT_FRAME_SIZE = (1080, 1080)   # crop/pad ให้พอดี
VIDEO_SIZE         = (1080, 1920)   # จอแนวตั้ง TikTok

# ตำแหน่งวางสินค้ากลางจอ (เริ่มที่แถว Y=420 เพื่อเว้นพื้นที่ข้อความบน-ล่าง)
PRODUCT_PASTE_Y = 420


def process_product_image(image_path: str, mode: str = "mock") -> str:
    """
    โหลดรูปสินค้า → Resize/Pad ให้พอดีกรอบ 1080x1080
    แล้ววางลงบนพื้นหลังดำ 1080x1920 สำหรับวิดีโอแนวตั้ง

    Args:
        image_path: path ของรูปภาพสินค้าต้นทาง
        mode      : "mock" = คืน path จำลอง | "production" = ประมวลผลจริง
    Returns:
        path ของภาพที่ประมวลผลแล้ว (พร้อมส่ง video_maker)
    """

    # =========================================================
    # MOCK MODE
    # =========================================================
    if mode == "mock":
        print("🖼️ [MOCK] ประมวลผลภาพจำลองสำเร็จ — ข้าม Pillow processing")
        return MOCK_IMAGE_PATH

    # =========================================================
    # PRODUCTION MODE
    # =========================================================
    try:
        src = Path(image_path)
        if not src.exists():
            raise FileNotFoundError(f"ไม่พบไฟล์รูปภาพ: {image_path}")

        with Image.open(src) as img:
            img = img.convert("RGB")

            # --- Step 1: Crop/Pad ให้เป็นสี่เหลี่ยมจัตุรัส 1080x1080 ---
            product_frame = ImageOps.fit(
                img,
                PRODUCT_FRAME_SIZE,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5)
            )

            # --- Step 2: สร้างพื้นหลังดำ 1080x1920 ---
            background = Image.new("RGB", VIDEO_SIZE, color=(10, 10, 10))

            # --- Step 3: วางสินค้าตรงกลางแนวนอน ที่ Y=PRODUCT_PASTE_Y ---
            paste_x = (VIDEO_SIZE[0] - PRODUCT_FRAME_SIZE[0]) // 2  # = 0 (กว้างเท่ากัน)
            background.paste(product_frame, (paste_x, PRODUCT_PASTE_Y))

            # --- Step 4: บันทึกผลลัพธ์ ---
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            output_path = IMAGES_DIR / "processed_product.jpg"
            background.save(output_path, "JPEG", quality=90)

        print(f"🖼️ [PRODUCTION] ประมวลผลภาพสำเร็จ → {output_path}")
        return str(output_path)

    except Exception as e:
        print(f"❌ image_processor error: {e}")
        print("⚠️  Fallback → คืน path จำลอง")
        return MOCK_IMAGE_PATH


if __name__ == "__main__":
    result = process_product_image("data/images/image_1.jpg", mode="production")
    print(f"ผลลัพธ์: {result}")
