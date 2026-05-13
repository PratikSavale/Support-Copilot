import httpx
import asyncio

async def main():
    url = "https://react.carbondesignsystem.com/iframe.html?id=components-accordion--default&viewMode=docs"
    async with httpx.AsyncClient() as client:
        # Get markdown via Jina
        resp = await client.get(f"https://r.jina.ai/{url}")
        print(resp.text[:500])
            
if __name__ == "__main__":
    asyncio.run(main())
