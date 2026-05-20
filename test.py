import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        r = await client.get('https://r.jina.ai/https://maven.apache.org/guides/')
        print(r.status_code, len(r.text))

asyncio.run(main())
