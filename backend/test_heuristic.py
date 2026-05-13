import asyncio
from utils.web_scraper import WebScraper

async def main():
    scraper = WebScraper()
    url = "https://react.carbondesignsystem.com/?path=/docs/components-accordion--default"
    print("Testing crawl_website with single page limit...")
    res = await scraper.crawl_website(url, max_pages=1, max_concurrent=1)
    if res:
        print(f"Content extracted ({len(res[0])} chars):")
        print("--- END OF CONTENT ---")
        print(res[0][-1000:])

if __name__ == "__main__":
    asyncio.run(main())
