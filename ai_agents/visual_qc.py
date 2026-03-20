"""
Visual QC Agent — TikTok Subtitle Inspector
ดึงเฟรมจากวิดีโอสำเร็จรูป แล้วให้ Gemini Vision ตรวจคุณภาพซับไตเติ้ล
"""
import os
from pathlib import Path
from dotenv import load_dotenv

VIDEO_PATH    = "data/final_video.mp4"
QC_IMAGES_DIR = "data/images"
MAX_DURATION_SEC = 60.0  # CQO Rule: วิดีโอต้องไม่เกิน 1 นาที


# =========================================================
# DURATION PRE-CHECK (ถูกก่อน Gemini Vision — ไม่เปลือง token)
# =========================================================

def check_video_duration(video_path: str) -> tuple[str, float]:
    """
    ตรวจความยาววิดีโอ — เร็ว ไม่เรียก API
    Returns: ("PASS"|"FAIL", duration_in_seconds)
    """
    from moviepy import VideoFileClip
    clip = VideoFileClip(video_path)
    duration = clip.duration
    clip.close()
    status = "PASS" if duration <= MAX_DURATION_SEC else "FAIL"
    label  = "✅" if status == "PASS" else "❌"
    print(f"   {label} Duration check: {duration:.1f}s / {MAX_DURATION_SEC:.0f}s limit → {status}")
    return status, duration


# =========================================================
# FRAME EXTRACTION
# =========================================================

def extract_frames(video_path: str) -> list[str]:
    """
    ดึง 3 เฟรมจากวิดีโอ (วินาทีที่ 2, กลางคลิป, ก่อนจบ 2 วินาที)
    บันทึกเป็น data/images/qc_1.jpg, qc_2.jpg, qc_3.jpg
    """
    from moviepy import VideoFileClip
    from PIL import Image
    import numpy as np

    clip = VideoFileClip(video_path)
    duration = clip.duration

    timestamps = [
        min(2.0, duration * 0.10),
        duration / 2,
        max(0.0, duration - 2.0),
    ]

    os.makedirs(QC_IMAGES_DIR, exist_ok=True)
    saved_paths: list[str] = []

    for i, t in enumerate(timestamps):
        t = max(0.0, min(t, duration - 0.05))
        frame = clip.get_frame(t)
        img   = Image.fromarray(frame.astype("uint8"))
        out_path = f"{QC_IMAGES_DIR}/qc_{i + 1}.jpg"
        img.save(out_path, "JPEG", quality=90)
        print(f"   📸 เฟรม {i + 1}: t={t:.1f}s → {out_path}")
        saved_paths.append(out_path)

    clip.close()
    return saved_paths


# =========================================================
# GEMINI VISION QC
# =========================================================

QC_PROMPT = """\
คุณคือ "ผู้กำกับศิลป์อาวุโส (Senior Art Director)" ที่เกลียดงานกากสุดชีวิต \
คุณทำงานให้ TikTok Southeast Asia ฝ่าย Creator Quality และโปรแกรมเมอร์กลัวคุณมาก

หน้าที่คือ: ตรวจสอบ 3 เฟรมจากวิดีโอ TikTok Affiliate และ "จับผิดอย่างโหดเหี้ยม" \
ห้ามให้ผ่านง่ายๆ เด็ดขาด ต้องพบข้อผิดพลาดจึงจะปล่อยผ่าน

===== เกณฑ์ตรวจสอบ 3 ข้อ (ข้อใดข้อหนึ่ง FAIL = ทั้งหมด FAIL) =====

[ข้อ 1] FONT QUALITY — ฟอนต์ภาษาไทยต้องเรียบเนียนสมบูรณ์
  ✗ FAIL ถ้า: ตัวอักษรแตกเป็นพิกเซล / มีขีดเส้นแปลกๆ รอบตัวอักษร / \
ฟอนต์บิดเบี้ยวหรือมีสัญลักษณ์แปลกปลอม / สระหรือวรรณยุกต์ลอยผิดที่  
  ✓ PASS ถ้า: ตัวอักษรเรียบสะอาด อ่านออกง่าย ไม่มี artifact ใดๆ

[ข้อ 2] POSITION & NON-OVERLAP — ตำแหน่งซับไตเติ้ลต้องถูกต้อง
  ✗ FAIL ถ้า: ซับไตเติ้ล "บัง/ทับ" ตัวสินค้าที่อยู่กลางภาพ / \
ข้อความอยู่กลางจอหรือบนครึ่งจอ / ข้อความล้นออกนอกขอบจอ
  ✓ PASS ถ้า: ซับไตเติ้ลอยู่ใน "พื้นที่ล่าง 20% ของภาพ" และไม่บดบังสินค้า

[ข้อ 3] SUBTITLE LENGTH — ความยาวต้องสั้นกระชับสไตล์ TikTok Pro
  ✗ FAIL ถ้า: ซับไตเติ้ลมีมากกว่า 1 บรรทัด / มีข้อความยาวเกิน 3 คำต่อ chunk / \
คำไทยถูกตัดกลางคำ (เช่น "ตลอด-ชีวิต" ขึ้นบรรทัดใหม่)
  ✓ PASS ถ้า: แต่ละ chunk มีแค่ 1-3 คำ อยู่บรรทัดเดียว

===== วิธีตอบ =====

ถ้าพบปัญหาข้อใดข้อหนึ่ง ให้:
1. ขึ้นต้นด้วยคำว่า **FAIL** ตัวใหญ่
2. ด่าแรงๆ สไตล์ Art Director ว่าทำไมถึงกากขนาดนี้
3. ระบุ parameter MoviePy ที่ต้องแก้ให้เจาะจงมาก เช่น:
   - "เปลี่ยน method='caption' เป็น method='label'"
   - "ลด font_size จาก 95 เป็น 72"
   - "เปลี่ยน subtitle_y จาก TARGET_H*0.80 เป็น TARGET_H*0.82"
   - "ลด max_chars ใน chunk_text_for_subtitles จาก 15 เป็น 10"
4. ให้คะแนน 0-100 โดย FAIL ต้องได้ไม่เกิน 59

ถ้าผ่านทุกข้อ ให้:
1. ขึ้นต้นด้วยคำว่า **PASS 100/100** ตัวใหญ่
2. บอกว่าผ่านเพราะอะไร แบบ Art Director ที่พอใจจริงๆ
"""


def run_visual_qc(video_path: str = VIDEO_PATH) -> tuple[str, str]:
    """
    รัน Visual QC โดยใช้ Gemini Vision
    Returns: (status, feedback)
      status  = "PASS" | "FAIL" | "SKIP"
      feedback = ข้อความจาก Gemini
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        msg = "⚠️  ไม่พบ GEMINI_API_KEY ใน .env — ข้าม Visual QC"
        print(msg)
        return "SKIP", msg

    if not Path(video_path).exists():
        msg = f"⚠️  ไม่พบไฟล์วิดีโอ: {video_path} — ข้าม Visual QC"
        print(msg)
        return "SKIP", msg

    # --- Duration pre-check (ก่อนเปลือง Gemini token) ---
    print("⏱️  ตรวจความยาววิดีโอ...")
    dur_status, duration = check_video_duration(video_path)
    if dur_status == "FAIL":
        msg = (
            f"❌ FAIL — วิดีโอยาว {duration:.1f}s เกินขีดจำกัด {MAX_DURATION_SEC:.0f}s\n"
            f"แก้ไข: ลดความยาวสคริปต์หรือตรวจสอบ MAX_VIDEO_DURATION ใน video_maker.py"
        )
        print(msg)
        return "FAIL", msg

    # --- ดึงเฟรม ---
    print("🎬 กำลังดึงเฟรมจากวิดีโอ...")
    frame_paths = extract_frames(video_path)

    # --- Gemini Vision ---
    print("🤖 กำลังส่งภาพให้ Gemini Vision ตรวจสอบ...")
    from google import genai as _genai

    client = _genai.Client(api_key=api_key)

    # อัปโหลดรูปภาพผ่าน Files API
    uploaded_files = []
    for p in frame_paths:
        f = client.files.upload(file=p)
        uploaded_files.append(f)
        print(f"   ✅ อัปโหลด {Path(p).name} → {f.name}")

    # ส่ง prompt พร้อมรูปภาพ (retry สูงสุด 3 ครั้งถ้า 503)
    contents = [*uploaded_files, QC_PROMPT]
    import time
    last_err = None
    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
            )
            feedback = response.text.strip()
            # ต้องได้ "PASS 100/100" เท่านั้น — Art Director โหดไม่ให้ pass ง่ายๆ
            status   = "PASS" if "PASS 100/100" in feedback.upper() else "FAIL"
            return status, feedback
        except Exception as e:
            last_err = e
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                wait = attempt * 15
                print(f"   ⚠️  Gemini 503 (ครั้งที่ {attempt}/3) — รอ {wait}s แล้วลองใหม่...")
                time.sleep(wait)
            else:
                break

    msg = f"⚠️  Gemini API ล้มเหลวหลังลอง 3 ครั้ง: {last_err}"
    print(msg)
    return "SKIP", msg


# =========================================================
# CLI
# =========================================================

if __name__ == "__main__":
    status, feedback = run_visual_qc()
    divider = "=" * 60
    print(f"\n{divider}")
    print(f"{'✅ PASS — วิดีโอสมบูรณ์แบบ!' if status == 'PASS' else '❌ FAIL — ต้องแก้ไข!' if status == 'FAIL' else '⏭️  SKIP'}")
    print(divider)
    print(feedback)
    print(divider)
