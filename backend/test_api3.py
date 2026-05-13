import os
from google.generativeai import configure, GenerativeModel

configure(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyDFSEcObz54ZeMk5K-i2keE1dvxBIzOvk8"))
model = GenerativeModel("gemini-2.0-flash-lite-001")
try:
    print("lite:", model.generate_content("hello").text)
except Exception as e:
    print("Error lite:", e)
