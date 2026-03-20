import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# NOTE: genai.Client ถูกสร้างแบบ Lazy — เฟ้า production mode เท่านั้น
# ไม่มีการเชื่อมต่อ Google API ใดๆ ในโหมด mock

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def save_file(file_path, content):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def evaluate_script(script, qc_prompt, mode: str = "mock"):
    # =========================================================
    # MOCK MODE — อนุมัติสคริปต์อัตโนมัติ ไม่เรียก Gemini API
    # =========================================================
    if mode == "mock":
        print("✅ [MOCK] QC ผ่านอัตโนมัติ — ไม่เรียก Gemini API")
        return "PASS"

    # PRODUCTION MODE
    from google import genai as _genai  # Lazy import — โหลดเฉพาะตอนใช้งานจริง
    client = _genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(model='gemini-2.5-flash', contents=f"{qc_prompt}\n\nScript: {script}")
    return response.text

def main(mode: str = "mock"):
    script = read_file("data/generated_script.txt")
    qc_prompt = read_file("prompts/qc.txt")
    evaluation = evaluate_script(script, qc_prompt, mode=mode)

    if "PASS" in evaluation:
        save_file("data/approved_script.txt", script)
        print("Script approved and saved.")
    elif "REJECT" in evaluation:
        print("Script rejected. Reason:")
        print(evaluation)

if __name__ == "__main__":
    main()