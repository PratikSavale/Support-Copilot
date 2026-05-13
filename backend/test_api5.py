import os
from google.generativeai import configure, GenerativeModel

configure(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyDFSEcObz54ZeMk5K-i2keE1dvxBIzOvk8"))

for m in ["gemini-flash-latest", "gemini-pro-latest", "gemini-3.1-flash-lite"]:
    try:
        print(m, ":", GenerativeModel(m).generate_content("hello").text[:20])
    except Exception as e:
        print("Error", m, ":", e)
