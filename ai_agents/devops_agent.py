"""
ai_agents/devops_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT A.Z.E. — DevOps Auto-Healing Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
หน้าที่:
  1. เฝ้าดู logs/error_crash.log แบบ real-time
  2. จำแนกประเภท error (ImportError, NetworkError, ฯลฯ)
  3. ซ่อมแซมอัตโนมัติ (auto pip-install, retry, restart)
  4. ส่งข้อ error ที่ซับซ้อนให้ Gemini วิเคราะห์
  5. Restart pipeline หากจำเป็น

Usage (standalone):
    python -m ai_agents.devops_agent

Usage (as module):
    from ai_agents.devops_agent import DevOpsAgent
    agent = DevOpsAgent()
    await agent.run()
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"
CRASH_LOG = LOG_DIR / "error_crash.log"
HEAL_LOG = LOG_DIR / "devops_heal.log"
MAIN_SCRIPT = ROOT_DIR / "main.py"

# ── Config ───────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MAX_AUTO_RESTARTS = 5          # จำนวน restart สูงสุดต่อชั่วโมง
RESTART_COOLDOWN = 30          # วินาที ก่อน restart
WATCH_INTERVAL = 5             # วินาที ระหว่างแต่ละ poll
MAX_HEAL_ATTEMPTS = 3          # ความพยายาม heal ต่อ error instance


# ══════════════════════════════════════════════════════════════
#  Error Classification
# ══════════════════════════════════════════════════════════════

class ErrorType:
    IMPORT_ERROR = "ImportError"
    MODULE_NOT_FOUND = "ModuleNotFoundError"
    NETWORK_ERROR = "NetworkError"
    PLAYWRIGHT_ERROR = "PlaywrightError"
    GEMINI_ERROR = "GeminiError"
    FILE_NOT_FOUND = "FileNotFoundError"
    PERMISSION_ERROR = "PermissionError"
    RATE_LIMIT = "RateLimitError"
    UNKNOWN = "UnknownError"


# regexp → (ErrorType, capture_group_name)
_CLASSIFIERS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"ModuleNotFoundError: No module named '(\S+)'"),
     ErrorType.MODULE_NOT_FOUND, "module"),
    (re.compile(r"ImportError: cannot import name '(\S+)'"),
     ErrorType.IMPORT_ERROR, "symbol"),
    (re.compile(r"(playwright\._impl\._errors|playwright\.sync_api)"),
     ErrorType.PLAYWRIGHT_ERROR, ""),
    (re.compile(r"(google\.api_core\.exceptions|ResourceExhausted|quota)"),
     ErrorType.GEMINI_ERROR, ""),
    (re.compile(r"(ConnectionError|aiohttp\.ClientError|requests\.exceptions|httpx)"),
     ErrorType.NETWORK_ERROR, ""),
    (re.compile(r"FileNotFoundError: \[Errno 2\]"),
     ErrorType.FILE_NOT_FOUND, ""),
    (re.compile(r"PermissionError"),
     ErrorType.PERMISSION_ERROR, ""),
    (re.compile(r"(Rate limit|429|Too Many Requests)"),
     ErrorType.RATE_LIMIT, ""),
]


def classify_error(error_text: str) -> tuple[str, str]:
    """
    Returns (ErrorType, extra_info).
    extra_info เช่น ชื่อ module ที่หายไป
    """
    for pattern, etype, group in _CLASSIFIERS:
        m = pattern.search(error_text)
        if m:
            extra = m.group(1) if group and m.lastindex else ""
            return etype, extra
    return ErrorType.UNKNOWN, ""


# ══════════════════════════════════════════════════════════════
#  Log Writer
# ══════════════════════════════════════════════════════════════

def _log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [DevOps] {msg}"
    print(line, flush=True)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(HEAL_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
#  Auto-Heal Actions
# ══════════════════════════════════════════════════════════════

def heal_module_not_found(module_name: str) -> bool:
    """Auto pip-install missing module."""
    # strip submodule path: 'google.cloud.storage' → 'google-cloud-storage'
    package = module_name.split(".")[0].replace("_", "-")
    _log(f"🔧 Auto-installing missing package: {package}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "--quiet"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            _log(f"✅ Successfully installed: {package}")
            return True
        _log(f"❌ pip install failed: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        _log(f"⏱️ pip install timed out for: {package}")
    except Exception as e:
        _log(f"❌ pip install error: {e}")
    return False


async def heal_playwright() -> bool:
    """Attempt reinstall/repair playwright browser."""
    _log("🔧 Repairing Playwright browser installation...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            _log("✅ Playwright chromium reinstalled.")
            return True
        _log(f"❌ Playwright install failed: {result.stderr[:200]}")
    except Exception as e:
        _log(f"❌ Playwright repair error: {e}")
    return False


async def heal_network_error() -> bool:
    """Brief backoff for transient network issues."""
    delay = 30
    _log(f"🌐 Network error detected — waiting {delay}s before retry...")
    await asyncio.sleep(delay)
    return True  # pipeline restart will retry


async def heal_rate_limit() -> bool:
    """Gemini/API rate limit — wait longer."""
    delay = 120
    _log(f"⏳ Rate-limit detected — cooling down {delay}s...")
    await asyncio.sleep(delay)
    return True


# ══════════════════════════════════════════════════════════════
#  Gemini AI Diagnosis (for UNKNOWN errors)
# ══════════════════════════════════════════════════════════════

async def gemini_diagnose(error_text: str) -> str:
    """Ask Gemini what went wrong and how to fix it."""
    if not GEMINI_API_KEY:
        return "Gemini API key ไม่ได้ตั้งค่า — ไม่สามารถวิเคราะห์ได้"
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = (
            "คุณเป็น DevOps AI ของระบบ AZE (Autonomous Zombie Empire) "
            "ซึ่งเป็น pipeline Python สำหรับสร้าง TikTok video อัตโนมัติ\n\n"
            "Error log ด้านล่างนี้เกิดขึ้นใน pipeline:\n"
            f"```\n{error_text[:1500]}\n```\n\n"
            "จงตอบเป็น JSON format:\n"
            '{"diagnosis": "สาเหตุเป็น...", '
            '"fix": "คำสั่งหรือโค้ดที่แนะนำ", '
            '"severity": "low|medium|high|critical", '
            '"restart_needed": true|false}'
        )
        resp = await asyncio.to_thread(model.generate_content, prompt)
        return resp.text.strip()
    except Exception as e:
        return f"Gemini diagnosis ล้มเหลว: {e}"


# ══════════════════════════════════════════════════════════════
#  Pipeline Restarter
# ══════════════════════════════════════════════════════════════

_pipeline_process: Optional[subprocess.Popen] = None
_restart_count = 0
_last_restart_hour = -1


async def restart_pipeline() -> bool:
    """Kill existing pipeline process and start a fresh one."""
    global _pipeline_process, _restart_count, _last_restart_hour

    current_hour = datetime.now().hour
    if current_hour != _last_restart_hour:
        _restart_count = 0
        _last_restart_hour = current_hour

    if _restart_count >= MAX_AUTO_RESTARTS:
        _log(f"🚨 เกินจำนวน restart สูงสุด ({MAX_AUTO_RESTARTS}/ชม.) — รอ human intervention")
        return False

    # Kill existing
    if _pipeline_process and _pipeline_process.poll() is None:
        _log("🛑 Killing existing pipeline process...")
        _pipeline_process.terminate()
        try:
            _pipeline_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _pipeline_process.kill()

    _log(f"⏳ รอ {RESTART_COOLDOWN}s ก่อน restart...")
    await asyncio.sleep(RESTART_COOLDOWN)

    _log(f"🚀 Starting pipeline (attempt {_restart_count + 1}/{MAX_AUTO_RESTARTS})...")
    try:
        _pipeline_process = subprocess.Popen(
            [sys.executable, str(MAIN_SCRIPT)],
            cwd=str(ROOT_DIR),
        )
        _restart_count += 1
        _log(f"✅ Pipeline started — PID {_pipeline_process.pid}")
        return True
    except Exception as e:
        _log(f"❌ Failed to start pipeline: {e}")
        return False


# ══════════════════════════════════════════════════════════════
#  Log File Watcher
# ══════════════════════════════════════════════════════════════

class CrashLogWatcher:
    """Tail logs/error_crash.log and yield new error blocks."""

    def __init__(self, path: Path):
        self.path = path
        self._position = 0
        self._seen_blocks: set[str] = set()

    def _collect_new_lines(self) -> str:
        if not self.path.exists():
            return ""
        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._position)
                new_text = f.read()
                self._position = f.tell()
            return new_text
        except Exception:
            return ""

    def poll(self) -> list[str]:
        """Return list of new error blocks since last poll."""
        new_text = self._collect_new_lines()
        if not new_text.strip():
            return []

        # split on common Python traceback headers
        blocks = re.split(r"(?=Traceback \(most recent call last\))", new_text)
        results = []
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            # deduplicate identical crashes
            fingerprint = block[-200:]
            if fingerprint not in self._seen_blocks:
                self._seen_blocks.add(fingerprint)
                results.append(block)
        return results


# ══════════════════════════════════════════════════════════════
#  Main DevOps Agent
# ══════════════════════════════════════════════════════════════

class DevOpsAgent:
    """
    Auto-healing DevOps agent for Project A.Z.E.

    Loop:
      1. สังเกต crash log
      2. จำแนก error
      3. ซ่อมอัตโนมัติ
      4. Restart pipeline ถ้าจำเป็น
    """

    def __init__(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.watcher = CrashLogWatcher(CRASH_LOG)
        self._heal_counts: dict[str, int] = {}

    async def _handle_error_block(self, error_block: str) -> None:
        etype, extra = classify_error(error_block)
        _log(f"🔍 Error classified: {etype} | extra='{extra}'")
        _log(f"   Snippet: {error_block[-120:]!r}")

        # track heal attempts per error fingerprint
        fp = error_block[-100:]
        attempts = self._heal_counts.get(fp, 0)
        if attempts >= MAX_HEAL_ATTEMPTS:
            _log(f"⚠️ เกินจำนวน heal attempts — เรียก Gemini AI diagnosis...")
            diagnosis = await gemini_diagnose(error_block)
            _log(f"🤖 Gemini says:\n{diagnosis}")
            return
        self._heal_counts[fp] = attempts + 1

        healed = False
        need_restart = True

        if etype == ErrorType.MODULE_NOT_FOUND:
            healed = heal_module_not_found(extra or "unknown")

        elif etype == ErrorType.IMPORT_ERROR:
            _log(f"💡 ImportError — ตรวจสอบว่า module ถูก install หรือไม่")
            # ImportError from wrong symbol — cannot auto-fix
            need_restart = False

        elif etype == ErrorType.PLAYWRIGHT_ERROR:
            healed = await heal_playwright()

        elif etype == ErrorType.NETWORK_ERROR:
            healed = await heal_network_error()

        elif etype == ErrorType.RATE_LIMIT:
            healed = await heal_rate_limit()

        elif etype == ErrorType.GEMINI_ERROR:
            _log("🔑 Gemini API error — ตรวจสอบ GEMINI_API_KEY ใน .env")
            need_restart = False

        elif etype == ErrorType.FILE_NOT_FOUND:
            _log("📁 FileNotFoundError — ตรวจสอบ path หรือสร้าง directory ที่ขาด")
            _ensure_data_dirs()
            healed = True

        elif etype == ErrorType.UNKNOWN:
            _log("🤔 Unknown error — ส่งให้ Gemini วิเคราะห์...")
            diagnosis = await gemini_diagnose(error_block)
            _log(f"🤖 Gemini diagnosis:\n{diagnosis}")
            need_restart = False  # รอผลจาก Gemini ก่อน

        if healed and need_restart:
            _log("🔄 Heal สำเร็จ — กำลัง restart pipeline...")
            await restart_pipeline()
        elif not healed and need_restart:
            _log("⚠️ Heal ไม่สำเร็จ — restart pipeline อยู่ดี (หวังว่าจะ recover เอง)")
            await restart_pipeline()

    async def run(self) -> None:
        """Main watch loop — runs forever."""
        _log("🧟 DevOps Agent เริ่มทำงาน — กำลังเฝ้าดู crash log...")
        _log(f"   Watching: {CRASH_LOG}")

        while True:
            try:
                new_errors = self.watcher.poll()
                for block in new_errors:
                    await self._handle_error_block(block)
            except Exception as e:
                _log(f"❗ DevOps Agent internal error: {e}")

            await asyncio.sleep(WATCH_INTERVAL)

    async def run_once(self, pipeline: bool = True) -> None:
        """
        Run pipeline once under supervision.
        หากล้มเหลว จะพยายาม heal แล้ว restart อัตโนมัติ
        """
        _log("🚀 Starting supervised pipeline run...")
        await restart_pipeline()

        # watch until pipeline exits
        while _pipeline_process and _pipeline_process.poll() is None:
            new_errors = self.watcher.poll()
            for block in new_errors:
                await self._handle_error_block(block)
            await asyncio.sleep(WATCH_INTERVAL)

        rc = _pipeline_process.returncode if _pipeline_process else -1
        if rc == 0:
            _log("✅ Pipeline เสร็จสมบูรณ์ — exit code 0")
        else:
            _log(f"❌ Pipeline จบด้วย exit code {rc} — กำลัง heal...")
            new_errors = self.watcher.poll()
            for block in new_errors:
                await self._handle_error_block(block)


# ── Helpers ──────────────────────────────────────────────────

def _ensure_data_dirs() -> None:
    for sub in ("images", "browser_state", "fonts"):
        (ROOT_DIR / "data" / sub).mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════
#  Entry Point
# ══════════════════════════════════════════════════════════════

async def main():
    agent = DevOpsAgent()
    mode = os.getenv("DEVOPS_MODE", "watch").lower()
    if mode == "supervised":
        await agent.run_once()
    else:
        await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
