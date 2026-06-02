import asyncio
from backend.utils.web_scraper import WebScraper

async def main():
    scraper = WebScraper()
    pages = await scraper.crawl_website('https://maven.apache.org/guides/', max_pages=3)
    print(f"Pages fetched: {len(pages)}")

asyncio.run(main())
