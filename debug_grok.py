
import asyncio
import os
from neurohack_memory.extractors import extract
from neurohack_memory.utils import load_yaml

TEXT = "Hi! My preferred language is Kannada. Please schedule calls after 11 AM. Also, never call on Sundays."

async def main():
    print(f"Testing extraction for: '{TEXT}'")
    print(f"Provider: {os.getenv('EXTRACTOR_PROVIDER', 'grok')}")
    print(f"API Key present: {'XAI_API_KEY' in os.environ}")
    
    mems = await extract(TEXT, 1)
    
    print(f"\nExtracted {len(mems)} memories:")
    for m in mems:
        print(f"- [{m.type.value}] {m.key}={m.value} (conf={m.confidence})")

if __name__ == "__main__":
    asyncio.run(main())
