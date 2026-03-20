# 🧟 PROJECT A.Z.E. — Autonomous Zombie Empire
## The Ultimate 100% Automated Affiliate Marketing System

> **Mission:** สร้างและโพสต์คลิป TikTok ป้ายยาสินค้าระดับ World-Class อัตโนมัติ 100% งบ ฿0/เดือน
> **Stack:** Python 3.12 · Playwright · Gemini AI · MoviePy · gTTS · FastAPI Dashboard

---

## ⚠️ สำหรับ AI Agent ที่เพิ่งเข้ามาในโปรเจกต์นี้

**อ่านไฟล์เหล่านี้ก่อนทำอะไรทั้งนั้น:**
1. `README.md` (ไฟล์นี้) — สถานะปัจจุบันและเป้าหมายถัดไป
2. `TEAM_MANIFESTO.md` — Architecture, Agent Roles, Pipeline ทั้งหมด
3. `AGI_BENCHMARK.md` — มาตรฐานการทำงาน (โค้ดทุกชิ้นต้องผ่าน 100/100)

เมื่ออ่านครบแล้ว ให้เริ่มต้นด้วย: **"อ่านพิมพ์เขียวโปรเจกต์เรียบร้อยแล้วครับบอส! 🫡"**

---

## 📊 Current Project State
*อัปเดต: 20 March 2026*

### ✅ เสร็จสมบูรณ์ (Production-Ready)

| ระบบ | ไฟล์หลัก | สถานะ | หมายเหตุ |
|---|---|---|---|
| **Scraper (TIGER)** | `scrapers/shopee_scraper.py` | ✅ Done | Playwright + Bot Evasion v2.0 + Fallback Mock |
| **Content Gen (ZOMB)** | `ai_agents/generator_agent.py` | ✅ Done | Gemini 2.5 Flash + Mock Mode |
| **QC Agent (ZOMB-QC)** | `ai_agents/qc_agent.py` | ✅ Done | Auto Approve/Reject |
| **TTS (BLADE)** | `media_studio/audio_maker.py` | ✅ Done | gTTS Thai voice |
| **Image Proc (BLADE)** | `media_studio/image_processor.py` | ✅ Done | Pillow 9:16 crop |
| **Video Studio (BLADE)** | `media_studio/video_maker.py` | ✅ **LOCKED** | Subtitle v3.0 · Score 100/100 · **⛔ ห้ามแก้** |
| **Visual QA (INSPECTOR)** | `ai_agents/visual_qc.py` | ✅ **LOCKED** | Gemini Vision · **⛔ ห้ามแก้** |
| **Auto-Fix Loop** | `vibe_coding_loop.py` | ✅ Done | AI แก้โค้ดตัวเอง max 5 รอบ |

### 🔧 กำลังพัฒนา

| ระบบ | ไฟล์หลัก | สถานะ |
|---|---|---|
| **Orchestrator (BOSS)** | `main.py` | 🔧 Pipeline ทำงานได้ แต่ TikTok poster ยัง mock-only |
| **TikTok Poster** | `publishers/tiktok_poster.py` | 🔧 Mock mode — ยังไม่ upload จริง |
| **Dashboard** | `dashboard/app.py` | 🔧 FastAPI ระหว่างพัฒนา |

### 📋 รอการพัฒนา

| ระบบ | Codename | ไฟล์ที่จะสร้าง |
|---|---|---|
| **Trend Analyst** | ORACLE | `ai_agents/trend_analyst.py` |
| **SEO & Growth** | GROWTH | `ai_agents/seo_agent.py` |

---

## 🎯 Next Milestone
*เป้าหมายปัจจุบัน: เชื่อม Pipeline ให้ครบ End-to-End*

### Priority 1 — เชื่อม Scraper → Content → Video (End-to-End Pipeline)
- [ ] ทดสอบ `main.py` รัน full pipeline ใน mock mode จาก cold start
- [ ] ยืนยัน `raw_data.json` → `approved_script.txt` → `final_video.mp4` ไหลครบ
- [ ] ทดสอบ LINE Notify แจ้งผลเมื่อ pipeline สำเร็จ

### Priority 2 — TikTok Poster (Production Mode)
- [ ] `publishers/tiktok_poster.py` — Playwright upload จริงบน TikTok Web
- [ ] ทดสอบ upload draft video (ไม่ publish จริง) เพื่อ verify flow

### Priority 3 — Trend Analyst (ORACLE Agent)
- [ ] `ai_agents/trend_analyst.py` — pytrends + Shopee keyword scoring
- [ ] Output: `data/trend_queue.json` → keyword list สำหรับ TIGER

---

## 🔄 Pipeline Flow

```
[ORACLE] → trend_queue.json
    ↓
[TIGER: Scrape Shopee] → raw_data.json + image_1.jpg
    ↓
[ZOMB: Write Script] → [ZOMB-QC: Approve] → approved_script.txt
    ↓
[BLADE: TTS + Image + Video Render] → final_video.mp4
    ↓
[INSPECTOR: Visual QC] → PASS / FAIL (max 5 auto-fix retries)
    ↓ PASS
[GROWTH: SEO Caption + Hashtag]
    ↓
[BOSS: TikTok Upload + LINE Notify ✅]
    ↓
[GROWTH: A/B Test + Performance Track]
```

---

## 🏗️ Tech Stack

| Component | Tool | Cost |
|---|---|---|
| Scraping | Playwright + Stealth CDP | ฟรี |
| AI Content | Google Gemini 2.5 Flash (free tier) | ฟรี |
| TTS | gTTS (Google Text-to-Speech) | ฟรี |
| Video Render | MoviePy + FFmpeg | ฟรี |
| Thai Font Render | Pillow (PIL) | ฟรี |
| Thai NLP | PyThaiNLP (newmm tokenizer) | ฟรี |
| Cloud Run | GitHub Actions (2,000 min/month) | ฟรี |
| **รวม** | | **฿0 / เดือน** |

---

## 📁 Project Structure

```
AZE_Project/
├── main.py                      # CEO Orchestrator (Pipeline entry point)
├── vibe_coding_loop.py          # Auto-fix QC loop (max 5 retries)
├── requirements.txt
├── .env                         # API keys (GEMINI_API_KEY, LINE_TOKEN, etc.)
├── .clinerules                  # AI Governance rules (Cline)
├── .cursorrules                 # AI Governance rules (Cursor)
├── AGI_BENCHMARK.md             # รัฐธรรมนูญโปรเจกต์ — มาตรฐาน 100/100
├── TEAM_MANIFESTO.md            # Agent Architecture + Roles
├── ai_agents/
│   ├── generator_agent.py       # ZOMB: Content generation
│   ├── qc_agent.py              # ZOMB-QC: Script quality check
│   └── visual_qc.py             # INSPECTOR: Video frame QC (Gemini Vision) ⛔
├── core/
│   ├── config.py                # Environment switcher
│   └── notifier.py              # LINE Notify
├── dashboard/
│   └── app.py                   # FastAPI monitoring dashboard
├── data/                        # I/O data (raw_data, scripts, video output)
├── logs/                        # Error & crash logs
├── media_studio/
│   ├── audio_maker.py           # BLADE: gTTS voiceover
│   ├── image_processor.py       # BLADE: Image crop + resize
│   └── video_maker.py           # BLADE: Full video render ⛔ LOCKED
├── prompts/                     # LLM prompt templates
├── publishers/
│   └── tiktok_poster.py         # BOSS: TikTok upload (Playwright)
└── scrapers/
    └── shopee_scraper.py        # TIGER: Shopee data scraper ⛔
```

---

## ⚡ Quick Start

```bash
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Install dependencies (first time only)
pip install -r requirements.txt

# 3. Run in mock mode (safe — no real API calls)
python main.py

# 4. Run in production mode (requires .env keys)
# Set ENVIRONMENT=production in .env first
python main.py
```

---

## ⚠️ CEO Directives

> **ประกาศ:** ห้าม AI ตนใดแก้ไขระบบ Media Studio (`video_maker.py`) และ Visual QA (`visual_qc.py`) โดยพลการ เนื่องจากระบบเหล่านี้ถูก Calibrate จนสมบูรณ์แบบแล้ว (AGI Benchmark Score: 100/100) การแก้ใดๆ ต้องได้รับอนุญาตจาก CEO เท่านั้น

---

*Project A.Z.E. | README v1.0 | 20 March 2026*
