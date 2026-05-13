import asyncio
from ai.llm_engine import get_llm_engine

async def main():
    llm = get_llm_engine()
    print("Testing generate_response...")
    resp = await llm.generate_response([{"role": "user", "content": "Hello!"}])
    print("Response:", resp)

if __name__ == "__main__":
    asyncio.run(main())
