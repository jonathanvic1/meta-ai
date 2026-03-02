import asyncio
import uuid
from core import MetaAI

async def test_session_persistence():
    ai = MetaAI(debug=True)
    convo_id = str(uuid.uuid4())
    
    print(f"--- Starting Conversation (ID: {convo_id}) ---")
    
    # Message 1
    print("\nUser: Hello, I am an Apple")
    print("Assistant: ", end="", flush=True)
    async for chunk in ai.chat("Hello, I am an Apple", conversation_id=convo_id):
        print(chunk, end="", flush=True)
    print()
    
    # Message 2
    print("\nUser: What am I?")
    print("Assistant: ", end="", flush=True)
    response_2 = ""
    async for chunk in ai.chat("What am I?", conversation_id=convo_id):
        print(chunk, end="", flush=True)
        response_2 += chunk
    print()
    
    if "apple" in response_2.lower():
        print("\n✅ SUCCESS: Context persisted! The AI remembered you are an Apple.")
    else:
        print("\n❌ FAILURE: Context lost. The AI did not remember you are an Apple.")

if __name__ == "__main__":
    asyncio.run(test_session_persistence())
