import asyncio
import os
from google.generativeai import configure, GenerativeModel

configure(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyDFSEcObz54ZeMk5K-i2keE1dvxBIzOvk8"))
model = GenerativeModel("gemini-2.5-flash")
try:
    print(model.generate_content("hello").text)
except Exception as e:
    print("Error 2.5:", e)

model2 = GenerativeModel("gemini-1.5-flash")
try:
    print(model2.generate_content("hello").text)
except Exception as e:
    print("Error 1.5:", e)

