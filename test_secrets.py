import httpx
import asyncio
import json

# The list of secret internal model IDs discovered in the JS chunk
SECRET_MODELS = [
    "llama-4-maverick",
    "gpt-5-1-codex",
    "claude-sonnet-4-5",
    "claude-opus-4-5",
    "gemini-3-pro",
    "grok-fast",
    "omni-prod",
    "think_hard"
]

async def test_model(model_id):
    print(f"
🧪 Testing Secret Model: {model_id}...")
    url = "http://localhost:8000/v1/chat/completions"
    payload = {
        "model": f"meta-{model_id}", # Maps to the raw ID in main.py
        "messages": [{"role": "user", "content": "Who are you and what version of Llama are you?"}],
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                print(f"✅ RESPONSE ({model_id}): {content[:100]}...")
                
                # Heuristic check to see if it actually changed
                if "Llama 3" in content:
                    print(f"⚠️  Result: Likely ignored (Fallback to Llama 3)")
                else:
                    print(f"🎉 Result: POTENTIAL SUCCESS! Response doesn't explicitly claim to be Llama 3.")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

async def main():
    print("WARNING: Make sure 'python main.py' is running in another terminal!
")
    for model in SECRET_MODELS:
        await test_model(model)

if __name__ == "__main__":
    asyncio.run(main())
