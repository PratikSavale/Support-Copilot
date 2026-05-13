import asyncio
from google.generativeai import configure, list_models
import os

configure(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyDFSEcObz54ZeMk5K-i2keE1dvxBIzOvk8"))
for m in list_models():
    print(m.name, m.supported_generation_methods)
