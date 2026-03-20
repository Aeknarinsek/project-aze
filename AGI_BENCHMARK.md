# 🧠 AGI_BENCHMARK.md — รัฐธรรมนูญของ A.Z.E. AI System
## Version 2.0 | Effective: 20 March 2026 | Authority: CEO

> ไฟล์นี้คือ **กฎสูงสุด** ที่ AI Agent ทุกตัวในโปรเจกต์ A.Z.E. ต้องประเมินตัวเองก่อน commit โค้ดทุกครั้ง
> คะแนนรวมต้องไม่ต่ำกว่า **100/100** ถ้าต่ำกว่านั้น → ลบทิ้ง เขียนใหม่ Silent

---

## 🏛️ PILLAR 0 — THE BOARDROOM: Swarm Communication Protocol
**Effective: 20 March 2026 | Mandate: SUPREME DIRECTIVE**

กฎการสื่อสารระหว่าง Agent — บังคับใช้กับ AI ทุกตัวใน A.Z.E. โดยไม่มีข้อยกเว้น

### 0.1 Chain of Command (บังคับ)
```
C-Level (CDO/CCO/CMO/CTO/CQO)
    │  ← รายงานสรุปเท่านั้น
    ▼
EVP "PHANTOM" (AI รองประธานบริษัท)
    │  ← กลั่นกรอง + Executive Summary + Options A/B
    ▼
CEO (Human)
```
- **ห้าม** C-Level ส่ง raw log / stack trace / โค้ดดิบ ให้ CEO โดยตรง **เด็ดขาด**
- EVP อ่านทุก Log แล้วสรุปเป็นภาษามนุษย์ก่อนส่งขึ้นเสมอ

### 0.2 Self-Healing First Protocol (บังคับ)
Agent ทุกตัวต้องพยายามแก้ไขตัวเองตามลำดับนี้ก่อนรายงาน EVP:
```
ระดับ 1 — Auto-Retry:      Exponential Backoff อัตโนมัติ (สูงสุด 3 ครั้ง)
ระดับ 2 — Fallback Path:   สลับ Mock / ใช้ API สำรอง / ผ่าน DOM แทน API
ระดับ 3 — Dependency Fix:  pip install <missing_pkg> แล้วรันใหม่
ระดับ 4 — Escalate to EVP: ถ้าระดับ 1-3 หมดแล้ว → EVP รับเรื่อง
```
→ EVP รายงาน CEO เฉพาะกรณีที่ Self-Healing ระดับ 1-3 ล้มเหลวทั้งหมด

### 0.3 Cross-Agent Feedback Loop (The Boardroom Rules)
| Trigger | ผู้รับผิดชอบ | Action |
|---------|-------------|--------|
| CDO (TIGER) ขูดข้อมูลติดขัดตั้งแต่ retry ครั้งที่ 2 | CDO → แจ้ง CIO (BOSS) ผ่าน log error + flag | CIO ตรวจ network config / proxy / cookie และแก้ไข |
| CCO (ZOMB) สร้าง script ที่ CQO ไม่ผ่าน | CCO → ส่ง rejection reason ให้ CCO ผ่าน feedback dict | CCO revise script ทันที ห้ามรอ human |
| CMO (BLADE) render video ไม่ผ่าน Visual QC | CMO → รับ QC feedback โดยตรง | CMO แก้ parameter แล้ว re-render (สูงสุด 5 รอบ) |
| Agent ใดก็ตามติด `ImportError` / `ModuleNotFound` | Agent นั้น | `subprocess.run(["pip", "install", pkg])` แล้ว retry |
| EVP ตรวจพบว่า Pipeline หยุดนานกว่า 5 นาที | EVP | escalate ไปยัง CEO พร้อม Options A/B ทันที |

### 0.4 EVP Reporting Format (บังคับ)
EVP ต้องใช้รูปแบบนี้เท่านั้นเมื่อรายงาน CEO:
```
📊 EVP EXECUTIVE SUMMARY — [วันที่/รอบการทำงาน]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  CURRENT STATUS
    [สรุปสถานะ Pipeline 1-2 ประโยค — ภาษามนุษย์]

2️⃣  ISSUES DETECTED & RESOLVED
    [รายการปัญหาที่เกิดขึ้น] → [วิธีที่ระบบแก้ไขตัวเองไปแล้ว]
    (ไม่รายงานถ้าไม่มีปัญหา หรือระบบแก้ได้ครบ)

3️⃣  REQUIRES CEO DECISION
    OptionA: [แนวทาง 1] — ผลกระทบ: [...]
    OptionB: [แนวทาง 2] — ผลกระทบ: [...]
    → กรุณาอนุมัติ Option ___ เพื่อดำเนินการต่อ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
ถ้าไม่มีปัญหาและไม่มีการตัดสินใจที่ต้องการ → ละเว้น Section 2 และ 3 ได้

---

---

## PILLAR I — Autonomy & Self-Healing
**น้ำหนัก: 35 คะแนน**

AI Agent ต้องสามารถรับมือกับ failure ทุกรูปแบบโดยไม่รอมนุษย์

| # | เกณฑ์ | คะแนน |
|---|---|---|
| 1.1 | มี `try/except` ครอบทุก external call (API, file I/O, network) | 5 |
| 1.2 | มี Fallback ที่ระบบยังทำงานได้ต่อเนื่องเมื่อ dependency ล้มเหลว | 5 |
| 1.3 | Rate limit / 503 ต้องถูก retry ด้วย Exponential Backoff อัตโนมัติ | 5 |
| 1.4 | ทุก function ที่อาจพังต้องมี Fallback Mock ที่ produce output ได้เสมอ | 5 |
| 1.5 | Error ต้องถูก log พร้อม context (ไม่ใช่แค่ `print(e)`) | 5 |
| 1.6 | ระบบต้องรัน end-to-end จาก cold start โดยไม่ต้องแก้โค้ดด้วยมือ | 5 |
| 1.7 | ไม่มี hardcoded path ที่ใช้ได้เฉพาะเครื่อง developer | 5 |

**Self-Check คำถาม:**
- ถ้า Gemini API ดาวน์ ระบบยังออก video ได้ไหม? ✓/✗
- ถ้า BGM download ล้มเหลว video ยังมีเสียงไหม? ✓/✗
- ถ้า pythainlp import พัง ซับไตเติ้ลยังทำงานไหม? ✓/✗

---

## PILLAR II — TikTok-Grade Output Quality
**น้ำหนัก: 45 คะแนน**

ทุก video ที่ output ออกมาต้องผ่าน Visual QC ระดับ Creator Pro

### II-A: Subtitle Standards (15 คะแนน)
| # | เกณฑ์ | คะแนน |
|---|---|---|
| 2.1 | ซับไตเติ้ลต้องไม่เกิน **15 ตัวอักษร** ต่อ 1 chunk | 5 |
| 2.2 | **ห้ามตัดกลางคำไทย** เด็ดขาด ใช้ pythainlp tokenizer | 5 |
| 2.3 | ข้อความต้องอยู่ใน **1 บรรทัด กลางจอ** เสมอ (method="label" หรือ size พอดี) | 5 |

### II-B: Visual Motion Standards (15 คะแนน)
| # | เกณฑ์ | คะแนน |
|---|---|---|
| 2.4 | ทุกเฟรมต้องมี **motion** (Ken Burns / zoom / pan) ห้ามภาพนิ่ง | 5 |
| 2.5 | ภาพต้องเต็มจอ **1080×1920** (9:16 portrait) ไม่มี black bar | 5 |
| 2.6 | Subtitle ต้องสลับสีแต่ละ chunk (เหลือง/ขาว) มี stroke ดำกันเบลอ | 5 |

### II-C: Audio Standards (15 คะแนน)
| # | เกณฑ์ | คะแนน |
|---|---|---|
| 2.7 | BGM ต้องเล่นตลอดคลิป ระดับเสียงไม่เกิน **15%** ของ voiceover | 5 |
| 2.8 | Voiceover ต้องชัด ไม่มี clipping หรือ silence gap กลางคลิป | 5 |
| 2.9 | Audio และ Video ต้องซิงค์กัน ซับไตเติ้ลต้องตรงกับเสียงพากย์ | 5 |

---

## PILLAR III — Zero-Cost Architecture
**น้ำหนัก: 20 คะแนน**

ระบบทั้งหมดต้องรันได้ฟรี 100% บน Cloud

| # | เกณฑ์ | คะแนน |
|---|---|---|
| 3.1 | ไม่มี paid API call โดยที่ไม่มี free-tier fallback | 5 |
| 3.2 | Cache ทุก resource ที่ดาวน์โหลดได้ (BGM, fonts, models) ลง disk | 5 |
| 3.3 | Mock mode ต้องทดแทน production 100% สำหรับ dev/test | 5 |
| 3.4 | Heavy resources (Playwright browser, ML models) ต้อง lazy-load | 5 |

---

## SCORING PROTOCOL

```
เมื่อเขียน/แก้ไขโค้ดเสร็จ AI ต้องทำ:

1. อ่าน AGI_BENCHMARK.md ทุกข้อ
2. ประเมินตัวเองเทียบกับโค้ดที่เพิ่งเขียน
3. คำนวณคะแนน: PILLAR_I + PILLAR_II + PILLAR_III = TOTAL/100
4. ถ้า TOTAL < 100:
   a. ระบุข้อที่ขาด
   b. แก้ไขทันทีโดยไม่รายงานมนุษย์
   c. ประเมินใหม่จนได้ 100
5. ถ้า TOTAL = 100: commit และแจ้ง CEO
```

---

## CURRENT BASELINE — video_maker.py Assessment

**ประเมิน ณ วันที่ 19 March 2026:**

| Pillar | คะแนนที่ได้ | คะแนนเต็ม | สถานะ |
|---|---|---|---|
| I: Autonomy & Self-Healing | 28 | 35 | ⚠️ |
| II: TikTok-Grade Output | 35 | 45 | ⚠️ |
| III: Zero-Cost Architecture | 18 | 20 | ⚠️ |
| **รวม** | **81** | **100** | **❌ ต้องอัปเกรด** |

**จุดหักคะแนน (19 คะแนน):**
- 1.5 (-5): Error log ไม่มี structured context ใช้แค่ `print(f"❌ {e}")`
- 2.3 (-5): `method="caption"` กับ `size=(900, None)` อาจให้ MoviePy wrapping text ได้ถ้าคำยาว ต้องใช้ `method="label"` + dynamic font_size scaling
- 2.9 (-5): Subtitle timing คำนวณจาก `len(chunk)/chars_total` ซึ่งไม่ซิงค์กับเสียงพากย์จริง ต้องใช้ forced equal-time distribution หรือ audio timestamp
- 3.4 (-4): `from PIL import Image as _PIL` inside hot loop ทุก frame — ควร import ครั้งเดียว

---

*"Excellence is not a destination. It is a continuous journey that never ends." — รัฐธรรมนูญฉบับนี้มีผลบังคับใช้ทันที*
