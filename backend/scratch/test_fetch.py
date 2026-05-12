import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_fetch(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Content Length: {len(response.text)}")
            
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
            lines = (line.strip() for line in text.splitlines())
            text = "\n".join(line for line in lines if line)
            print(f"Extracted Text Length: {len(text)}")
            print("Preview:")
            print(text[:500])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://react.carbondesignsystem.com/?path=/docs/getting-started-welcome--welcome"
    asyncio.run(test_fetch(url))
