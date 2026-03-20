"""
Vibe Coding Loop — Self-Healing Studio Orchestrator
วนลูปสูงสุด MAX_LOOPS รอบ:
  A → สร้างวิดีโอ (test_studio.py)
  B → Visual QC (Gemini Vision)
  C → PASS  → หยุด ฉลอง! 🎉
  D → FAIL  → พิมพ์ feedback แล้วหยุดรอให้ AI แก้โค้ด
"""
import asyncio
import subprocess
import sys
from pathlib import Path

MAX_LOOPS = 5
DIVIDER   = "=" * 65


# =========================================================
# STEP A — สร้างวิดีโอ (เรียก test_studio.py เป็น subprocess)
# =========================================================

def run_studio() -> bool:
    """รัน test_studio.py แล้วคืน True ถ้าสำเร็จ"""
    print(f"\n▶  Step A — กำลังเรนเดอร์วิดีโอ (test_studio.py)...")
    result = subprocess.run(
        [sys.executable, "test_studio.py"],
        cwd=str(Path(__file__).parent),
    )
    if result.returncode != 0:
        print(f"❌ test_studio.py ออกด้วย exit code {result.returncode}")
        return False
    return True


# =========================================================
# STEP B — Visual QC
# =========================================================

def run_qc() -> tuple[str, str]:
    """รัน Gemini Vision QC คืน (status, feedback)"""
    print(f"\n▶  Step B — Visual QC กำลังตรวจภาพ...")
    from ai_agents.visual_qc import run_visual_qc
    return run_visual_qc()


# =========================================================
# MAIN LOOP
# =========================================================

def main():
    print(f"\n{'🧟 VIBE CODING LOOP — Self-Healing Studio':^{len(DIVIDER)}}")
    print(DIVIDER)
    print(f"  สูงสุด {MAX_LOOPS} รอบ | จะหยุดเมื่อ Gemini ให้ PASS")
    print(DIVIDER)

    for iteration in range(1, MAX_LOOPS + 1):
        print(f"\n\n{'─'*65}")
        print(f"  🔄  รอบที่ {iteration} / {MAX_LOOPS}")
        print(f"{'─'*65}")

        # A — สร้างวิดีโอ
        if not run_studio():
            print("⛔ หยุดลูปเพราะ test_studio.py ล้มเหลว")
            break

        # B — Visual QC
        status, feedback = run_qc()

        print(f"\n{DIVIDER}")
        print(f"  📊 ผลรอบที่ {iteration}: {status}")
        print(DIVIDER)
        print(feedback)
        print(DIVIDER)

        # C — PASS
        if status == "PASS":
            print(f"\n🎉🎉🎉  PASS! วิดีโอสมบูรณ์แบบสไตล์ TikTok Pro แล้ว! 🎉🎉🎉")
            print(f"  ✅ ไฟล์วิดีโอ: data/final_video.mp4")
            break

        # D — FAIL
        if status == "FAIL":
            print(f"\n⚠️   FAIL รอบที่ {iteration} — อ่าน Feedback ด้านบนและรอ AI แก้โค้ดก่อนรอบถัดไป")
            if iteration < MAX_LOOPS:
                print(f"      ▶  เริ่มรอบที่ {iteration + 1} อัตโนมัติ...")
            continue

        # SKIP (ไม่มี API key หรือไม่มีวิดีโอ)
        if status == "SKIP":
            print(f"\n⏭️   SKIP — ตรวจภาพไม่ได้ ดูรายละเอียดด้านบน")
            break

    else:
        print(f"\n⏹️  ครบ {MAX_LOOPS} รอบแล้ว ยังไม่ได้ PASS — ตรวจสอบ feedback และแก้โค้ดให้มากขึ้น")

    print(f"\n{DIVIDER}\n")


if __name__ == "__main__":
    main()
