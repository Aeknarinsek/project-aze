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

# ── Timeline Blueprint Prompts (Human-Like Pro Editor) ──────────────────
PLATFORM_TIMELINE_PROMPTS = {
    "tiktok": PROMPTS_DIR / "tiktok_timeline.txt",
    "shorts": PROMPTS_DIR / "shorts_timeline.txt",
    "reels":  PROMPTS_DIR / "reels_timeline.txt",
}

# ── Blueprint JSON Schema (used for validation) ─────────────────────────
BLUEPRINT_REQUIRED_KEYS = {"meta", "video_track", "audio_track", "sfx_track",
                            "text_track", "timing_events", "color_grade_map"}

# ── Mock Blueprint (TikTok 30s) — used when mode="mock" or Gemini falls back ──
import datetime as _dt
MOCK_TIMELINE: dict = {
    "meta": {
        "platform":       "tiktok",
        "total_duration": 30.0,
        "product_name":   "ร่มกันแดด UV",
        "mood_baseline":  "comedic",
        "created_at":     _dt.datetime.utcnow().isoformat(),
    },
    "video_track": [
        {"id": "v1", "t_start": 0.0,  "t_end": 5.0,  "type": "product_image",
         "asset": "data/images/processed_product.jpg",
         "effect": "ken_burns",  "scale_start": 1.0, "scale_end": 1.05, "color_grade": "desaturated_dark"},
        {"id": "v2", "t_start": 5.0,  "t_end": 9.0,  "type": "product_image",
         "asset": "data/images/processed_product.jpg",
         "effect": "jump_cut",   "scale_start": 1.0, "scale_end": 1.08, "color_grade": "vivid_pop"},
        {"id": "v3", "t_start": 9.0,  "t_end": 13.0, "type": "product_image",
         "asset": "data/images/processed_product.jpg",
         "effect": "zoom_in",    "scale_start": 1.0, "scale_end": 1.15, "color_grade": "vivid_pop"},
        {"id": "v4", "t_start": 13.0, "t_end": 20.0, "type": "product_image",
         "asset": "data/images/processed_product.jpg",
         "effect": "ken_burns",  "scale_start": 1.0, "scale_end": 1.08, "color_grade": "warm_bright"},
        {"id": "v5", "t_start": 20.0, "t_end": 26.0, "type": "product_image",
         "asset": "data/images/processed_product.jpg",
         "effect": "jump_cut",   "scale_start": 1.05, "scale_end": 1.1, "color_grade": "vivid_pop"},
        {"id": "v6", "t_start": 26.0, "t_end": 30.0, "type": "product_image",
         "asset": "data/images/processed_product.jpg",
         "effect": "zoom_in",    "scale_start": 1.0, "scale_end": 1.2,  "color_grade": "warm_bright"},
    ],
    "audio_track": [
        {"id": "a1", "t_start": 0.0, "t_end": 30.0,
         "type": "voiceover", "asset": "data/voiceover.mp3",  "volume": 1.0, "loop": False},
        {"id": "a2", "t_start": 0.0, "t_end": 30.0,
         "type": "bgm",       "asset": "data/bgm.mp3",        "volume": 0.12, "loop": True},
    ],
    "sfx_track": [
        {"id": "s1", "t_start": 5.0,  "type": "whoosh",        "asset": None, "volume": 0.6, "trigger": "jump_cut"},
        {"id": "s2", "t_start": 9.5,  "type": "ding",          "asset": None, "volume": 0.7, "trigger": "punchline"},
        {"id": "s3", "t_start": 20.0, "type": "whoosh",        "asset": None, "volume": 0.5, "trigger": "jump_cut"},
        {"id": "s4", "t_start": 26.5, "type": "cash_register", "asset": None, "volume": 0.8, "trigger": "cta"},
    ],
    "text_track": [
        {"id": "tx1", "t_start": 0.0,  "t_end": 4.0,  "text": "สิ่งที่ซอมบี้กลัวที่สุด...",
         "style": "hook",     "font_size": 95, "color": "#FFE600", "position": "bottom", "animation": "fade_in"},
        {"id": "tx2", "t_start": 4.0,  "t_end": 5.0,  "text": "",
         "style": "pause",    "font_size": 0,  "color": "#000000", "position": "center", "animation": "none"},
        {"id": "tx3", "t_start": 5.0,  "t_end": 9.0,  "text": "ไม่ใช่ garlic นะ!",
         "style": "reveal",   "font_size": 95, "color": "#FFFFFF", "position": "bottom", "animation": "pop"},
        {"id": "tx4", "t_start": 9.0,  "t_end": 13.0, "text": "คือแดดตอนบ่ายสามโมง",
         "style": "body",     "font_size": 85, "color": "#FFE600", "position": "bottom", "animation": "slide_up"},
        {"id": "tx5", "t_start": 13.0, "t_end": 20.0, "text": "ร่มกันแดด UV ราคา 199",
         "style": "product",  "font_size": 95, "color": "#FFFFFF", "position": "bottom", "animation": "fade_in"},
        {"id": "tx6", "t_start": 20.0, "t_end": 26.0, "text": "กันแดดได้ 100%",
         "style": "highlight","font_size": 100,"color": "#FF6B35", "position": "center", "animation": "pop"},
        {"id": "tx7", "t_start": 26.0, "t_end": 30.0, "text": "กดตะกร้าเหลืองด้านล่าง!",
         "style": "cta",      "font_size": 90, "color": "#FFE600", "position": "bottom", "animation": "pulse"},
    ],
    "timing_events": [
        {"t": 5.0,  "event": "jump_cut",  "duration": 0.0, "notes": "Hard cut to reveal"},
        {"t": 9.5,  "event": "punchline", "duration": 0.5, "notes": "ดราม่า peak"},
        {"t": 20.0, "event": "jump_cut",  "duration": 0.0, "notes": "Energy boost ก่อน CTA"},
        {"t": 26.5, "event": "cta",       "duration": 3.5, "notes": "กดลิงก์ใน bio"},
    ],
    "color_grade_map": {
        "vivid_pop":        {"saturation": 1.4, "brightness": 1.1,  "contrast": 1.2, "hue_shift": 0},
        "warm_bright":      {"saturation": 1.2, "brightness": 1.15, "contrast": 1.1, "hue_shift": 10},
        "desaturated_dark": {"saturation": 0.4, "brightness": 0.7,  "contrast": 1.3, "hue_shift": 0},
        "bw_sad":           {"saturation": 0.0, "brightness": 0.85, "contrast": 1.1, "hue_shift": 0},
    },
}


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

    # ─── Gemini Key Rotation (Feature 7) ─────────────────
    try:
        from core.resource_manager import GeminiKeyRotator, AllKeysExhaustedError
        rotator = GeminiKeyRotator()
        model   = rotator.get_gemini_model()
        script  = rotator.call_with_rotation(model, full_prompt)
        print(f"✍️ [PRODUCTION] Zomb เขียนสคริปต์ {platform.upper()} สำเร็จ!")
        return script
    except AllKeysExhaustedError as e:
        print(f"🔴 ทุก Gemini key หมด quota: {e} — Fallback สคริปต์จำลอง")
        return MOCK_SCRIPTS.get(platform, MOCK_SCRIPTS["tiktok"])
    except Exception as e:
        print(f"❌ Gemini API Error ({platform}): {e} — Fallback สคริปต์จำลอง")
        return MOCK_SCRIPTS.get(platform, MOCK_SCRIPTS["tiktok"])


def generate_timeline(
    product_data,
    mode: str = "mock",
    platform: str = "tiktok",
) -> dict:
    """
    สร้าง JSON Blueprint (Timeline) สำหรับ Human-Like Pro Editor

    Args:
        product_data : list/dict ข้อมูลสินค้าจาก raw_data.json
        mode         : "mock"       = คืน MOCK_TIMELINE ทันที
                       "production" = ส่ง prompt ไปยัง Gemini → parse JSON
        platform     : "tiktok" | "shorts" | "reels"
    Returns:
        dict — valid blueprint ที่ TimelineRenderer รองรับ
    """
    import copy
    import datetime

    # ── MOCK MODE ────────────────────────────────────────────
    if mode == "mock":
        bp = copy.deepcopy(MOCK_TIMELINE)
        bp["meta"]["platform"]   = platform
        bp["meta"]["created_at"] = datetime.datetime.utcnow().isoformat()
        print(f"🎬 [MOCK] Timeline Blueprint ({platform.upper()}) จำลองสำเร็จ — ไม่เรียก Gemini")
        return bp

    # ── PRODUCTION MODE ──────────────────────────────────────
    prompt_file = PLATFORM_TIMELINE_PROMPTS.get(platform.lower())
    if not prompt_file or not Path(prompt_file).exists():
        print(f"⚠️  ไม่พบ timeline prompt สำหรับ {platform} — Fallback mock")
        return copy.deepcopy(MOCK_TIMELINE)

    trend_ctx    = _load_context_file("data/trend_report.json",    default="")
    adaptive_ctx = _load_context_file("data/winning_patterns.json", default="")
    product_json = json.dumps(product_data, ensure_ascii=False, indent=2)

    full_prompt = Path(prompt_file).read_text(encoding="utf-8").format(
        product_data     = product_json,
        trend_context    = f"=== TREND DATA ===\n{trend_ctx}"       if trend_ctx    else "",
        adaptive_context = f"=== WINNING PATTERNS ===\n{adaptive_ctx}" if adaptive_ctx else "",
    )

    try:
        from core.resource_manager import GeminiKeyRotator, AllKeysExhaustedError
        rotator  = GeminiKeyRotator()
        model    = rotator.get_gemini_model()
        raw_text = rotator.call_with_rotation(model, full_prompt)

        # Strip markdown fences if Gemini wraps in ```json ... ```
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1]
            raw_text = raw_text.rsplit("```", 1)[0]

        blueprint = json.loads(raw_text)

        # Basic schema validation
        missing = BLUEPRINT_REQUIRED_KEYS - set(blueprint.keys())
        if missing:
            print(f"⚠️  Blueprint ขาด keys: {missing} — Fallback mock")
            return copy.deepcopy(MOCK_TIMELINE)

        blueprint["meta"]["platform"]   = platform
        blueprint["meta"]["created_at"] = datetime.datetime.utcnow().isoformat()
        print(f"🎬 [PRODUCTION] Zomb สร้าง Timeline Blueprint {platform.upper()} สำเร็จ!")
        return blueprint

    except json.JSONDecodeError as e:
        print(f"❌ Gemini คืน JSON ไม่ valid ({platform}): {e} — Fallback mock")
    except Exception as e:
        print(f"❌ Gemini API Error timeline ({platform}): {e} — Fallback mock")

    return copy.deepcopy(MOCK_TIMELINE)


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
