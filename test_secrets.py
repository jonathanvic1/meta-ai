import httpx
import asyncio
import json

# The list of secret internal model IDs discovered in the JS chunk
SECRET_MODELS = [
    "meta-llama-4-maverick",
    "meta-llama-gpt-5-1-codex",
    "meta-claude-sonnet-4-5",
    "meta-claude-opus-4-5",
    "meta-gemini-3-pro",
    "meta-grok-fast",
    "meta-omni-prod",
    "meta-think_hard"
]

async def test_model(model_id):
    print(f"\n🧪 Testing Secret Model: {model_id}...")
    url = "http://localhost:8000/v1/chat/completions"
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Who are you and what version of Llama are you?"}],
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                print(f"✅ RESPONSE ({model_id}): {content[:150]}...")
                
                # Heuristic check to see if it actually changed
                if "Llama 3" in content or "Llama 3.1" in content:
                    print(f"⚠️  Result: Likely ignored (Fallback to Llama 3/3.1)")
                else:
                    print(f"🎉 Result: POTENTIAL SUCCESS! Response doesn't explicitly claim to be Llama 3.")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

async def main():
    print("WARNING: Make sure 'python3 main.py' is running in another terminal!\n")
    for model in SECRET_MODELS:
        await test_model(model)

if __name__ == "__main__":
    asyncio.run(main())
