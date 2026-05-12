import asyncio
import logging
from utils.web_scraper import WebScraper

async def test_scraper(url: str):
    logging.basicConfig(level=logging.INFO)
    scraper = WebScraper()
    try:
        print(f"Testing fetch_content for: {url}")
        text = await scraper.fetch_content(url)
        print(f"Extracted Text Length: {len(text)}")
        print("Preview (first 200 chars):")
        print(text[:200])
        
        print("\nTesting crawl_website (limited to 2 pages)...")
        pages = await scraper.crawl_website(url, max_pages=2)
        print(f"Crawl collected {len(pages)} pages.")
        if pages:
            print(f"First page length: {len(pages[0])}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://react.carbondesignsystem.com/?path=/docs/getting-started-welcome--welcome"
    asyncio.run(test_scraper(url))
