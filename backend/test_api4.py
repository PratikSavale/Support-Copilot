import os
from google.generativeai import configure, GenerativeModel

configure(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyDFSEcObz54ZeMk5K-i2keE1dvxBIzOvk8"))
model = GenerativeModel("gemini-1.5-flash-latest")
try:
    print("1.5 flash:", model.generate_content("hello").text)
except Exception as e:
    print("Error 1.5 flash:", e)

model2 = GenerativeModel("gemini-1.5-pro-latest")
try:
    print("1.5 pro:", model2.generate_content("hello").text)
except Exception as e:
    print("Error 1.5 pro:", e)
