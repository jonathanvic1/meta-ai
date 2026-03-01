# Meta AI Unofficial Wrapper (Zero-Setup Anonymous Mode)

This is a high-performance, OpenAI-compatible API wrapper for the Meta AI (meta.ai) web interface. It works completely anonymously, just like an incognito browser session.

## Features
- **Zero-Setup**: No browser login, no Playwright, no manual cookie stealing.
- **OpenAI Compatible**: Supports `/v1/chat/completions`.
- **Fast Performance**: Direct `httpx` GraphQL communication.
- **Streaming Support**: Real-time token streaming.

## Setup

1. **Activate Virtual Environment**
   ```bash
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the API Server**
   ```bash
   python main.py
   ```
   The server will run at `http://localhost:8000`.

## Example Usage

### Using cURL
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama-3",
    "messages": [{"role": "user", "content": "Tell me a joke."}],
    "stream": true
  }'
```

## Project Structure
- `core.py`: Handles anonymous session handshakes and GraphQL messaging.
- `main.py`: The FastAPI server providing the OpenAI-compatible endpoint.
