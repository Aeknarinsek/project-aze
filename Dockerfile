# ============================================================
# PROJECT A.Z.E. — Autonomous Zombie Empire
# Dockerfile: Write Once, Run Anywhere (Cloud-Ready)
# Python 3.11 · FFmpeg · ImageMagick · Playwright · Thai Fonts
# ============================================================

FROM python:3.11-slim

# ── ป้องกัน interactive prompt ระหว่าง apt-get ─────────────
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── System dependencies ──────────────────────────────────────
# ffmpeg        — สำหรับ MoviePy ตัด/รวม video + audio
# imagemagick   — สำหรับ TextClip (subtitle) ใน MoviePy
# fonts-thai-*  — ฟอนต์ภาษาไทยระบบ (fallback)
# wget / unzip  — ดาวน์โหลด Kanit font
# libgl1        — OpenCV / Pillow dependency
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    imagemagick \
    fonts-thai-tlwg \
    fonts-noto-cjk \
    wget unzip curl \
    libgl1 libglib2.0-0 \
    # Playwright chromium dependencies
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxcb1 libxkbcommon0 libx11-6 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# ── ดาวน์โหลดฟอนต์ Kanit จาก Google Fonts ──────────────────
# (ใช้ใน video subtitle — ต้องตรงกับ path ใน video_maker.py)
RUN mkdir -p /usr/share/fonts/truetype/kanit \
    && wget -q "https://fonts.gstatic.com/s/kanit/v15/nKKZ-Go6G5tXcoaSEQGodLxA.woff2" \
       -O /tmp/kanit.woff2 \
    # woff2 ไม่รองรับบางระบบ — ดาวน์โหลด TTF แทน
    && wget -q "https://github.com/google/fonts/raw/main/ofl/kanit/Kanit-Regular.ttf" \
       -O /usr/share/fonts/truetype/kanit/Kanit-Regular.ttf \
    && wget -q "https://github.com/google/fonts/raw/main/ofl/kanit/Kanit-Bold.ttf" \
       -O /usr/share/fonts/truetype/kanit/Kanit-Bold.ttf \
    && fc-cache -fv \
    && rm -f /tmp/kanit.woff2

# ── แก้ policy ImageMagick ให้อ่าน PDF/video ได้ ────────────
# (default policy ใน Debian บล็อก write ทุกอย่าง)
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' \
    /etc/ImageMagick-6/policy.xml 2>/dev/null || true \
    && sed -i 's/<policy domain="coder" rights="none"/<policy domain="coder" rights="read|write"/' \
    /etc/ImageMagick-6/policy.xml 2>/dev/null || true

# ── WORKDIR ──────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ──────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Playwright — ติดตั้ง Chromium browser ───────────────────
RUN python -m playwright install chromium \
    && python -m playwright install-deps chromium

# ── Copy source code ─────────────────────────────────────────
COPY . .

# ── สร้าง directories ที่จำเป็น ──────────────────────────────
RUN mkdir -p data/images data/browser_state data/fonts logs

# ── Copy font ไปยัง data/fonts ด้วย (สำหรับ video_maker.py) ──
RUN cp /usr/share/fonts/truetype/kanit/Kanit-Regular.ttf data/fonts/ 2>/dev/null || true

# ── Default command ──────────────────────────────────────────
CMD ["python", "main.py"]
