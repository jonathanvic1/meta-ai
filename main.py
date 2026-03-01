from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import json
import time
from core import MetaAI

app = FastAPI(title="Meta AI Unofficial API")
ai = MetaAI()

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "meta-llama-3.1"
    messages: List[Message]
    stream: bool = False

@app.get("/")
async def root():
    return {"status": "running", "service": "Meta AI Wrapper"}

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    # Extract the last message from the conversation
    last_message = request.messages[-1].content
    
    if request.stream:
        async def event_generator():
            try:
                async for chunk in ai.chat(last_message):
                    data = {
                        "id": "chatcmpl-" + str(int(time.time())),
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": chunk},
                                "finish_reason": None
                            }
                        ]
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                
                # Signal the end of the stream
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    
    else:
        # Non-streaming response
        full_text = ""
        try:
            async for chunk in ai.chat(last_message):
                full_text += chunk
            
            return {
                "id": "chatcmpl-" + str(int(time.time())),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": full_text
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
