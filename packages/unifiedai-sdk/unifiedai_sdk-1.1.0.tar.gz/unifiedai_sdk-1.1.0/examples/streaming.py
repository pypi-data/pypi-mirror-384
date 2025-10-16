import asyncio

from unifiedai import UnifiedAI


async def main() -> None:
    async with UnifiedAI(provider="cerebras", model="llama3") as client:
        async for chunk in client.chat.completions.create_stream(
            messages=[{"role": "user", "content": "Hello"}]
        ):
            print(chunk.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
