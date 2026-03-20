# 🧟 PROJECT A.Z.E. — TEAM MANIFESTO
## Autonomous Zombie Empire | Multi-Agent System Architecture

> **Mission:** สร้างระบบ Affiliate Automation ระดับโลก งบ 0 บาท รันบน Cloud ได้ 100%
> **Stack:** Python 3.12 · Playwright · Gemini AI · MoviePy · gTTS · FastAPI Dashboard

---

## 🏗️ HIERARCHY & CHAIN OF COMMAND

```
         ╔══════════════════════════════════════════╗
         ║           👑  CEO (Human)               ║
         ║    Final authority. Approves Options.    ║
         ╚══════════════════╦═══════════════════════╝
                            ║  receives Executive Summary only
                            ║  (ห้าม C-Level ข้ามหน้าข้ามตา)
         ╔══════════════════╩═══════════════════════╗
         ║   🎖️  EVP — AI Executive Vice President  ║
         ║  อ่าน Logs · สรุปผล · วิเคราะห์ปัญหา   ║
         ║  รายงาน CEO ด้วย Executive Summary เท่านั้น ║
         ║  ห้ามเขียนโค้ดเอง เด็ดขาด                ║
         ╚══╦═══════╦══════╦═══════╦═══════╦════════╝
            ║       ║      ║       ║       ║
       [CDO/TIGER] [CCO] [CMO] [CTO/BOSS] [CQO]
        Scraping  Content Media   Backend  Quality
```

### 📜 Chain-of-Command Rules
1. **C-Level → EVP เท่านั้น**: AI ทุกตัวรายงานผ่าน EVP — ห้ามส่งโค้ดดิบหรือ raw log ตรงถึง CEO เด็ดขาด
2. **Self-Healing First**: ก่อนรายงาน EVP ทุก Agent ต้องพยายามซ่อมตัวเองก่อน (retry / fallback / `pip install`) จนหมดทางแล้วค่อยรายงาน
3. **EVP → CEO ด้วย Executive Summary**: รูปแบบบังคับ — สถานะปัจจุบัน / ปัญหาที่พบและซ่อมแล้ว / Options A•B ที่รอ CEO อนุมัติ

---

## 🏗️ SYSTEM ARCHITECTURE OVERVIEW — 7-AGENT AGENCY

```
                    ┌────────────────────────────────┐
                    │        main.py  (CEO)          │
                    │  Orchestrates all 7 agents     │
                    └──┬──────┬──────┬──────┬───────┘
                       │      │      │      │
          ┌────────────┼──────┼──────┼──────┼────────────┐
          │            │      │      │      │            │
    [Agent 0]    [Agent 1] [Agent 2] [Agent 3] [Agent 4]  │
     นักวิเคราะห์  เสือย้อย   ซอมบ์    มีดโกน    เจ้านาย  │
     (Trends)   (Scraper) (Content) (Studio) (Backend)   │
          │            │      │      │      │            │
   [Agent 5]           └──────┴──────┘      │       [Agent 6]
    QA Vision                               │       SEO Hacker
    (Quality)                         [LINE/TikTok]  (Growth)
```

---

---

## 👔 EVP — AI EXECUTIVE VICE PRESIDENT
**Title:** Executive Vice President / AI รองประธานบริษัท
**Codename:** `PHANTOM`
**Reports to:** CEO (Human) — รายงานด้วย Executive Summary เท่านั้น
**Oversees:** CDO · CCO · CMO · CTO · CQO (C-Level ทั้งหมด)

**ภารกิจหลัก:**
- อ่านและวิเคราะห์ Log จาก Agent ทุกตัวใน Pipeline
- สรุปผลการทำงาน รวมถึงการซ่อมแซมที่ C-Level ดำเนินการไปแล้ว
- กลั่นกรองข้อมูลก่อนส่งถึง CEO — ห้ามให้ CEO เห็น stack trace หรือโค้ดดิบ เด็ดขาด
- เสนอ Options ให้ CEO ตัดสินใจ ไม่ใช่บอกปัญหาเฉยๆ

**สิ่งที่ EVP ทำไม่ได้:**
- ❌ เขียนโค้ด Python ใดๆ เองโดยตรง
- ❌ แก้ไขไฟล์ใน repository ด้วยตัวเอง
- ❌ Commit / Deploy
- ❌ รายงาน CEO โดยไม่ผ่านการสรุปและกลั่นกรองก่อน

**รูปแบบ Executive Summary (บังคับ):**
```
📊 EVP EXECUTIVE SUMMARY — [วันที่/รอบการทำงาน]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  CURRENT STATUS
    สรุปสถานะ Pipeline ภาพรวม — จาก Scraping ถึง Publishing

2️⃣  ISSUES DETECTED & RESOLVED (Self-Healed)
    ปัญหาที่เกิดขึ้น + วิธีที่ระบบซ่อมแซมตัวเองไปแล้ว
    (ไม่รบกวน CEO ด้วยสิ่งที่แก้ไปแล้ว — รายงานเพื่อ acknowledge เท่านั้น)

3️⃣  REQUIRES CEO DECISION
    OptionA: [เสนอแนวทางที่ 1 + ผลกระทบ]
    OptionB: [เสนอแนวทางที่ 2 + ผลกระทบ]
    → กรุณาอนุมัติ Option ___ เพื่อดำเนินการต่อ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**สถานะ:** ✅ Operational — Phantom Online

---

## 👥 THE SEVEN AGENTS

---

### 🐯 AGENT 1: ไอ้เสือย้อย — The Scraping Beast
**Codename:** `TIGER`
**File:** `scrapers/shopee_scraper.py`
**Pillar:** 1 — Data Acquisition

**ภารกิจ:** ล่าข้อมูลสินค้าขายดีจาก Shopee Thailand โดยไม่ถูกจับ

**ความสามารถ:**
- Playwright Headless Browser พร้อม Stealth Mode (ซ่อน `navigator.webdriver`)
- ดักจับ Shopee Internal API (`/api/v4/search/search_items`) โดยตรง — ไม่พัง เมื่อ UI เปลี่ยน
- Rotate User-Agent + Human-like Random Delays (0.5-2.5s)
- Inject CDP Stealth Scripts ผ่าน `add_init_script()` เพื่อหลอก bot detector
- Auto-dismiss Cookie Banners และ Notification Popups
- Block ทรัพยากรที่ไม่จำเป็น (fonts, trackers) — เร็วขึ้น 40%
- Retry ด้วย Exponential Backoff (3 ครั้ง) เมื่อเจอ 403/timeout
- Screenshot Debug เมื่อ Fail → `data/images/debug_screenshot.png`
- Fallback Mock Data — ระบบไม่หยุดทำงานแม้ Shopee บล็อก

**Output:** `data/raw_data.json` + `data/images/image_1.jpg`

**สถานะ:** ✅ Production-Ready (Bot Evasion v2.0)

---

### 🧟 AGENT 2: ซอมบ์ — The Dark Content Factory
**Codename:** `ZOMB`
**Files:** `ai_agents/generator_agent.py` · `ai_agents/qc_agent.py`
**Pillar:** 2 — AI Content Generation & QC

**ภารกิจ:** สร้างสคริปต์ TikTok สไตล์ Dark Humor ที่คนดูต้องหยุดดู

**ความสามารถ:**
- Zomb Persona Prompt Engineering — ซอมบี้หนุ่มหล่อมาดเท่ เสียงนุ่มลึก
- โครงสร้าง Hook (10s) → Plot Twist (15s) → CTA (5s) = สคริปต์ 40 วินาที
- ใช้ Gemini 2.5 Flash (`google.generativeai`) สำหรับ Production
- QC Agent ตรวจสอบด้วย Custom Prompt ก่อน approve
- Mock Mode สคริปต์จำลคองฺไม่ใช้ API โควต้าฟรี

**Input:** `data/raw_data.json`
**Output:** `data/generated_script.txt` → `data/approved_script.txt`

**สถานะ:** ✅ Production-Ready

---

### 🔪 AGENT 3: มีดโกน — The Media Studio
**Codename:** `BLADE`
**Files:** `media_studio/video_maker.py` · `media_studio/audio_maker.py` · `media_studio/image_processor.py`
**Pillar:** 3 — Media Production

**ภารกิจ:** แปลงสคริปต์ข้อความชิ้นเดียวให้กลายเป็นคลิป TikTok ระดับมืออาชีพ

**ความสามารถ:**
- `audio_maker.py` — gTTS Text-to-Speech เสียงภาษาไทย → `data/voiceover.mp3`
- `image_processor.py` — Pillow resize + crop ให้ได้สัดส่วน 9:16 (1080×1920px)
- `video_maker.py` — MoviePy orchestrator:
  - Ken Burns Zoom Effect (100% → 108%) ด้วย frame-by-frame PIL
  - Dynamic TikTok Captions: Alex Hormozi Style — max 22 ตัวอักษร/บรรทัด
  - สลับสีซับไตเติ้ล เหลือง/ขาว stroke ดำ font Tahoma
  - BGM Mix: `.volumex()` fallback → `.multiply_volume()` fallback → pass
  - Render H.264/AAC 24fps → `data/final_video.mp4`
- Visual QC: `ai_agents/visual_qc.py` — Gemini Vision ตรวจ 3 เฟรม

**Output:** `data/final_video.mp4`

**สถานะ:** ✅ Production-Ready (Subtitle v3.0 — pythainlp + AGI Benchmark 100/100)

---

### 👔 AGENT 4: เจ้านาย — The Backend Overlord
**Codename:** `BOSS`
**Files:** `main.py` · `publishers/tiktok_poster.py` · `core/config.py` · `core/notifier.py` · `dashboard/app.py`
**Pillar:** 4 — Orchestration, Publishing & Monitoring

**ภารกิจ:** ควบคุมทุก Agent ให้ทำงานเป็นระบบ และโพสต์ขึ้น TikTok อัตโนมัติ

**ความสามารถ:**
- `main.py` — Pipeline Orchestrator: Step 1-5 พร้อม Structured Logging
- Schedule ระบบรัน Auto ทุก 24 ชั่วโมง ด้วย `schedule` library
- `tiktok_poster.py` — Playwright-based TikTok upload (Web interface, no API key)
- `core/config.py` — Environment switcher: `ENVIRONMENT=mock|production`
- `core/notifier.py` — LINE Notify alert เมื่องานสำเร็จหรือ Error
- `dashboard/app.py` — FastAPI real-time monitoring dashboard
- Error Crash Log → `logs/error_crash.log`

**Output:** โพสต์บน TikTok + LINE notification

**สถานะ:** 🔧 In Development (TikTok poster: Mock-only)

---

### 📈 AGENT 5: นักวิเคราะห์ตลาด — The Trend & Market Analyst
**Codename:** `ORACLE`
**File:** `ai_agents/trend_analyst.py` *(planned)*
**Pillar:** 0 — Intelligence & Strategy

**ภารกิจ:** ค้นหาสินค้า High-Commission ที่กำลังเทรนด์ก่อนที่ Scraper จะลงมือ — เป็น upstream brain ของกระบวนการทั้งหมด

**ความสามารถ:**
- ดึง Google Trends Thailand ผ่าน `pytrends` — ตรวจ Rising/Breakout keywords รายวัน
- วิเคราะห์ Shopee Best Seller + Commission rate จาก Shopee Affiliate API
- เปรียบเทียบ Engagement Rate บน TikTok Thailand (TikTok Hashtag Search)
- Score สินค้าด้วย Formula: `(trend_score × commission_rate) / competition_index`
- ส่ง top-3 คีย์เวิร์ดให้ TIGER เป็น input queue อัตโนมัติ
- Gemini Flash วิเคราะห์ sentiment จาก comment สินค้าเพื่อคัด pain point

**Input:** Google Trends + Shopee Affiliate Dashboard + TikTok Search
**Output:** `data/trend_queue.json` → keyword list สำหรับ scrapers/shopee_scraper.py

**สถานะ:** 📋 Designed — Awaiting Implementation

---

### 🔍 AGENT 6: Visual QA & Compliance — The Quality Gatekeeper
**Codename:** `INSPECTOR`
**File:** `ai_agents/visual_qc.py` *(exists)*
**Pillar:** 3.5 — Quality Assurance & Legal Compliance

**ภารกิจ:** ตรวจสอบวิดีโอทุกคลิปก่อนโพสต์ — ไม่ให้วิดีโอห่วยหรือผิดลิขสิทธิ์ออกสู่สาธารณะ

**ความสามารถ:**
- **Visual QC** — Gemini Vision ตรวจ 3 เฟรม (วิ 2, กลาง, สุดท้าย):
  - ซับไตเติ้ลตกขอบจอ? / ตัดกลางคำ? / ยาวเกิน?
  - ภาพเบลอ / over-exposed / underexposed?
  - Brand สินค้าชัดเจนไหม?
- **Compliance Check** — ตรวจว่ามีเครื่องหมาย Brand ที่ไม่ได้รับอนุญาต, watermark ของ platform อื่น, หรือ content ที่ละเมิด TikTok Community Guidelines
- **Auto-Fix Loop** — ถ้า FAIL ส่ง structured feedback กลับให้ `vibe_coding_loop.py` แก้ไขอัตโนมัติ สูงสุด 5 รอบ
- Loop timeout protection — ถ้าครบ 5 รอบยังไม่ผ่าน ให้ใช้ mock video แทนและแจ้ง CEO

**Input:** `data/final_video.mp4` → 3 QC frames
**Output:** `PASS` / `FAIL + structured_feedback.json`

**สถานะ:** ✅ Production-Ready (visual_qc.py + vibe_coding_loop.py)

---

### 🚀 AGENT 7: SEO & Growth Hacker — The Viral Engineer
**Codename:** `GROWTH`
**File:** `ai_agents/seo_agent.py` *(planned)*
**Pillar:** 4.5 — Distribution & Growth

**ภารกิจ:** เพิ่ม reach ของทุกคลิปให้ viral ด้วย hashtag และ caption ที่ผ่านการ A/B test

**ความสามารถ:**
- **Hashtag Intelligence** — ดึง Top-200 hashtags TikTok Thailand รายวันผ่าน TikTok Creative Center
- **Caption Generator** — Gemini เขียน caption 3 แบบ (เร้าอารมณ์ / ข้อมูล / humor) แล้วเลือกที่ Engagement score สูงสุด
- **Posting Time Optimizer** — วิเคราะห์ว่าเวลาไหน TH audience active มากที่สุด (peak: 19:00-22:00 THT)
- **A/B Caption Test** — โพสต์ 2 เวอร์ชัน ดู 2 ชั่วโมงแรก ลบตัวที่แย่กว่า
- **Performance Tracker** — ดึง view/like/share จาก TikTok API ทุก 6 ชั่วโมง บันทึกใน `data/performance_log.json`
- รายงานสรุปส่งให้ CEO ผ่าน LINE Notify ทุกเช้า 08:00

**Input:** `data/approved_script.txt` + video metadata
**Output:** caption + hashtag set → `publishers/tiktok_poster.py`

**สถานะ:** 📋 Designed — Awaiting Implementation

---

## 🔄 PIPELINE FLOW

```
[ORACLE: Trend Analysis] ← Google Trends + Shopee Affiliate
        ↓ trend_queue.json
[TIGER: Shopee Scrape]   ← receives keyword from ORACLE
        ↓ raw_data.json + image_1.jpg
[ZOMB: Write Script] ──→ [ZOMB QC: Approve/Reject]
        ↓ PASS
  approved_script.txt
        ↓
  ┌─────┴──────┐
[BLADE: TTS] [BLADE: Image]
  voiceover.mp3  processed_product.jpg
  └──────┬─────┘
         ↓
[BLADE: Video Render] → final_video.mp4
         ↓
[INSPECTOR: Visual QC + Compliance]
    FAIL ↙         ↘ PASS (max 5 retries)
[vibe_coding_loop]   [GROWTH: SEO + Caption + Hashtag]
                              ↓
                    [BOSS: Schedule Optimal Time]
                              ↓
                    [BOSS: TikTok Upload]
                              ↓
                    [BOSS: LINE Notify ✅]
                              ↓
                    [GROWTH: A/B Test + Track Performance]
```

---

## 🌍 DEPLOYMENT PHILOSOPHY

| สิ่งที่ต้องใช้ | ต้นทุน |
|---|---|
| Python 3.12 + venv | ฟรี |
| Playwright Chromium | ฟรี |
| Google Gemini API (free tier) | ฟรี |
| gTTS (Google Text-to-Speech) | ฟรี |
| MoviePy + FFmpeg | ฟรี |
| GitHub Actions (Cloud Runner) | ฟรี 2,000 min/month |
| **รวมทั้งหมด** | **฿0 / เดือน** |

---

## 📋 AGENT COMMUNICATION PROTOCOL

```python
# ตัวอย่างการเรียก Agent ใน main.py
ENVIRONMENT = "mock"   # เปลี่ยนเป็น "production" เมื่อพร้อม

# แต่ละ Agent รับ mode parameter เดียวกัน
await scrape_shopee(keyword="สินค้าขายดี",  mode=ENVIRONMENT)
run_generator(mode=ENVIRONMENT)
run_qc(mode=ENVIRONMENT)
await generate_voiceover(script, mode=ENVIRONMENT)
await create_video(script, image, audio,   mode=ENVIRONMENT)
```

---

## 🚀 QUICK START

```bash
# 1. ติดตั้ง dependencies
pip install -r requirements.txt
playwright install chromium

# 2. ตั้งค่า API Keys ใน .env
GEMINI_API_KEY=your_key_here
LINE_NOTIFY_TOKEN=your_token_here

# 3. รัน Mock Test (ฟรี 100%)
python test_studio.py

# 4. รัน Self-Healing Vibe Coding Loop
python vibe_coding_loop.py

# 5. รัน Production Pipeline
ENVIRONMENT=production python main.py
```

---

## 📊 AGENT READINESS MATRIX

| # | Agent | Codename | สถานะ | File |
|---|---|---|---|---|
| 0 | นักวิเคราะห์ตลาด | ORACLE | 📋 Planned | `ai_agents/trend_analyst.py` |
| 1 | ไอ้เสือย้อย | TIGER | ✅ Live | `scrapers/shopee_scraper.py` |
| 2 | ซอมบ์ | ZOMB | ✅ Live | `ai_agents/generator_agent.py` |
| 3 | มีดโกน | BLADE | ✅ Live | `media_studio/video_maker.py` |
| 4 | เจ้านาย | BOSS | 🔧 Partial | `main.py` + `publishers/` |
| 5 | Visual QA | INSPECTOR | ✅ Live | `ai_agents/visual_qc.py` |
| 6 | SEO Hacker | GROWTH | 📋 Planned | `ai_agents/seo_agent.py` |

---

*Last Updated: 19 March 2026 — A.Z.E. Engineering Team | 7-Agent Expansion*
