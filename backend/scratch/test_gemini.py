import asyncio
import sys
from pathlib import Path

# Add backend to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import get_settings
from langchain_google_genai import ChatGoogleGenerativeAI

async def test_gemini():
    settings = get_settings()
    print("Testing Model:", settings.GEMINI_MODEL)
    print("Testing API Key prefix:", settings.GEMINI_API_KEY[:8] + "...")
    
    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        convert_system_message_to_human=True,
        temperature=0.3,
        max_tokens=1024,
        max_retries=0
    )
    
    try:
        print("Sending test invoke...")
        res = await model.ainvoke("Reply with exactly: Connected!")
        print("Response content:", repr(res.content))
    except Exception as e:
        print("Invoke failed with exception:", e)
        print("Exception type:", type(e))

if __name__ == "__main__":
    asyncio.run(test_gemini())
