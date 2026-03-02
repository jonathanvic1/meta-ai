import asyncio
import uuid
from core import MetaAI

async def test_booster_persistence():
    print("--- Initializing MetaAI with Booster ---")
    # use_booster=True will use Playwright to solve the challenge
    ai = MetaAI(debug=True, use_booster=True)
    
    convo_id = str(uuid.uuid4())
    print(f"Conversation ID: {convo_id}")
    
    # Message 1
    print("\nUser: Hello, I am an Apple")
    print("Assistant: ", end="", flush=True)
    async for chunk in ai.chat("Hello, I am an Apple", conversation_id=convo_id):
        print(chunk, end="", flush=True)
    print()
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Message 2
    print("\nUser: What am I?")
    print("Assistant: ", end="", flush=True)
    response_2 = ""
    async for chunk in ai.chat("What am I?", conversation_id=convo_id):
        print(chunk, end="", flush=True)
        response_2 += chunk
    print()
    
    if "apple" in response_2.lower():
        print("\n✅ SUCCESS: Booster session established and context persisted!")
    else:
        print("\n❌ FAILURE: Context lost or session failed.")

if __name__ == "__main__":
    asyncio.run(test_booster_persistence())
