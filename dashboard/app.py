import streamlit as st
import pandas as pd
import json
import os
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini API client
client = genai.Client(api_key=GEMINI_API_KEY)

# Title
st.title('\ud83d\udc51 A.Z.E. Command Center (\u0e28\u0e39\u0e19\u0e22\u0e4c\u0e1a\u0e31\u0e0d\u0e0a\u0e32\u0e01\u0e32\u0e23)')

# Layout
col1, col2 = st.columns(2)

# Left Column: System Statistics
with col1:
    st.header("\ud83d\udcca \u0e2a\u0e16\u0e34\u0e15\u0e34\u0e23\u0e30\u0e1a\u0e1a")
    try:
        with open("../data/raw_data.json", "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        product_count = len(raw_data)
        st.metric(label="\u0e08\u0e33\u0e19\u0e27\u0e19\u0e2a\u0e34\u0e19\u0e04\u0e49\u0e32", value=product_count)
    except Exception as e:
        st.error("\u0e44\u0e21\u0e48\u0e2a\u0e32\u0e21\u0e32\u0e23\u0e16\u0e42\u0e2b\u0e25\u0e14\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e2a\u0e34\u0e19\u0e04\u0e49\u0e32\u0e44\u0e14\u0e49: \u0e01\u0e23\u0e38\u0e13\u0e32\u0e15\u0e23\u0e27\u0e08\u0e2a\u0e2d\u0e1a\u0e44\u0e1f\u0e25\u0e4c raw_data.json")

# Right Column: Market Trend Analysis
with col2:
    st.header("\ud83d\udd2e \u0e27\u0e34\u0e40\u0e04\u0e23\u0e32\u0e30\u0e2b\u0e4c\u0e40\u0e17\u0e23\u0e19\u0e14\u0e4c\u0e15\u0e25\u0e32\u0e14\u0e14\u0e49\u0e27\u0e22 AI")
    if st.button("\u0e27\u0e34\u0e40\u0e04\u0e23\u0e32\u0e30\u0e2b\u0e4c\u0e40\u0e17\u0e23\u0e19\u0e14\u0e4c"):
        try:
            with open("../data/raw_data.json", "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"\u0e27\u0e34\u0e40\u0e04\u0e23\u0e32\u0e30\u0e2b\u0e4c\u0e2a\u0e34\u0e19\u0e04\u0e49\u0e32\u0e44\u0e2b\u0e19\u0e21\u0e35\u0e42\u0e2d\u0e01\u0e32\u0e2a\u0e02\u0e32\u0e22\u0e14\u0e35\u0e2a\u0e38\u0e14 \u0e1e\u0e23\u0e49\u0e2d\u0e21\u0e1a\u0e2d\u0e01\u0e40\u0e2b\u0e15\u0e38\u0e1c\u0e25\u0e2a\u0e31\u0e49\u0e19\u0e46 3 \u0e02\u0e49\u0e2d: {json.dumps(raw_data, ensure_ascii=False)}"
            )
            st.success("\u0e1c\u0e25\u0e01\u0e32\u0e23\u0e27\u0e34\u0e40\u0e04\u0e23\u0e32\u0e30\u0e2b\u0e4c:")
            st.write(response.text)
        except Exception as e:
            st.error(f"\u0e44\u0e21\u0e48\u0e2a\u0e32\u0e21\u0e32\u0e23\u0e16\u0e27\u0e34\u0e40\u0e04\u0e23\u0e32\u0e30\u0e2b\u0e4c\u0e40\u0e17\u0e23\u0e19\u0e14\u0e4c\u0e44\u0e14\u0e49: {e}")

# Bottom Section: Run A.Z.E. Machine
st.header("\u25b6\ufe0f \u0e23\u0e31\u0e19\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e08\u0e31\u0e01\u0e23 A.Z.E. \u0e17\u0e31\u0e19\u0e17\u0e35")
if st.button("\u0e23\u0e31\u0e19\u0e17\u0e31\u0e19\u0e17\u0e35"):
    st.warning("\u0e1f\u0e31\u0e07\u0e01\u0e4c\u0e0a\u0e31\u0e19\u0e19\u0e35\u0e49\u0e22\u0e31\u0e07\u0e2d\u0e22\u0e39\u0e48\u0e43\u0e19\u0e23\u0e30\u0e2b\u0e27\u0e48\u0e32\u0e07\u0e01\u0e32\u0e23\u0e1e\u0e31\u0e12\u0e19\u0e32")