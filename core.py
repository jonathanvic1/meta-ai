import httpx
import json
import uuid
import re
import time
from typing import AsyncGenerator, Optional, Dict, Any

class MetaAI:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url="https://www.meta.ai",
            follow_redirects=True,
            timeout=120.0
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.meta.ai",
            "Referer": "https://www.meta.ai/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        self.access_token = None
        self.lsd = None
        self.datr = None
        self.token_expiry = 0

    async def _ensure_session(self):
        """Initializes an anonymous session if one doesn't exist or is expired."""
        if self.access_token and time.time() < self.token_expiry:
            return

        # 1. Fetch main page to get initial cookies and LSD token
        response = await self.client.get("/")
        html = response.text
        
        # Extract LSD token
        lsd_match = re.search(r'\["LSD",\[\],{"token":"(.*?)"}', html)
        if lsd_match:
            self.lsd = lsd_match.group(1)
        
        # 2. Perform "Accept TOS for Temporary User" mutation
        # This is the exact mutation Meta AI uses when you first visit in Incognito
        variables = {
            "dob": "1999-01-01", 
            "icebreaker_type": "TEXT"
        }
        
        data = {
            "lsd": self.lsd,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraAcceptTOSForTempUserMutation",
            "variables": json.dumps(variables),
            "doc_id": "7604648749596940" # Doc ID for TOS acceptance
        }
        
        tos_response = await self.client.post("/api/graphql/", data=data, headers=self.headers)
        tos_json = tos_response.json()
        
        # Extract the access token for our new anonymous session
        try:
            auth_data = tos_json['data']['abra_accept_tos_for_temp_user']['new_temp_user_auth']
            self.access_token = auth_data['access_token']
            # Temp tokens usually last ~24 hours, let's refresh every 12 to be safe
            self.token_expiry = time.time() + (12 * 3600)
        except (KeyError, TypeError):
            print("Error: Could not create temporary anonymous session.")

    async def chat(self, message: str, conversation_id: str = None) -> AsyncGenerator[str, None]:
        await self._ensure_session()
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        offline_threading_id = str(uuid.uuid4())
        
        variables = {
            "message": {"sensitive_string_value": message},
            "externalConversationId": conversation_id,
            "offlineThreadingId": offline_threading_id,
            "suggestedPromptIndex": None,
            "flashVideoRecapInput": {"images": []},
            "flashPreviewInput": None,
            "promptPrefix": None,
            "entrypoint": "ABRA__CHAT__TEXT",
            "icebreaker_type": "TEXT",
            "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
            "__relay_internal__pv__WebPixelRatiorelayprovider": 1
        }
        
        # For anonymous users, we use the access_token instead of fb_dtsg
        data = {
            "access_token": self.access_token,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraSendMessageMutation",
            "variables": json.dumps(variables),
            "server_timestamps": "true",
            "doc_id": "7783822248314888"
        }
        
        async with self.client.stream("POST", "/api/graphql/", data=data, headers=self.headers) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                
                try:
                    if line.startswith('{"'):
                        chunk = json.loads(line)
                        message_node = chunk.get('data', {}).get('abra_send_message', {}).get('message', {})
                        text_delta = message_node.get('text', "")
                        if text_delta:
                            yield text_delta
                except json.JSONDecodeError:
                    continue

if __name__ == "__main__":
    import asyncio
    async def test():
        ai = MetaAI()
        print("Sending: Hello (Anonymous Mode)!")
        async for text in ai.chat("Hello!"):
            print(text, end="", flush=True)
        print("\nDone.")
    # asyncio.run(test())
