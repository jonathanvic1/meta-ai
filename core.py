import httpx
import json
import uuid
import re
import time
from typing import AsyncGenerator, Optional, Dict, Any

class MetaAI:
    def __init__(self, debug: bool = True, access_token: str = None, lsd: str = None, abra_user_id: str = None, cookies: Dict[str, str] = None):
        self.debug = debug
        self.client = httpx.AsyncClient(
            base_url="https://www.meta.ai",
            follow_redirects=True,
            timeout=120.0,
            cookies=cookies
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/x-javascript, text/javascript, application/json, text/plain",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Referer": "https://www.meta.ai/",
            "X-Meta-Internal": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        self.access_token = access_token
        self.lsd = lsd
        self.abra_user_id = abra_user_id
        self.token_expiry = time.time() + (24 * 3600) if access_token else 0

    async def _ensure_session(self):
        """Stable anonymous session establishment."""
        if self.access_token and time.time() < self.token_expiry:
            return

        # 0. Get initial cookies (datr, etc)
        # Manually adding datr from browser session to test
        self.client.cookies.set("datr", "GQilaVBFJ60Ho3kzZZKfHCqX", domain="www.meta.ai")
        await self.client.get("/")

        # 1. Check credentials
        check_data = {
            "doc_id": "2943394199ee6545d1f0c69d5b6e577f",
            "variables": {}
        }
        response = await self.client.post("/api/graphql", json=check_data, headers=self.headers)
        res_json = response.json()
        
        auth_data = res_json.get('data', {}).get('fetchTempUserCredentials', {})
        if auth_data.get('accessToken') is None:
            if self.debug:
                print("DEBUG: Access token missing. Attempting TOS/BirthYear...")
            # 2. Accept TOS/BirthYear
            tos_data = {
                "variables": {"dob": "1995-01-01", "icebreaker_type": "TEXT"},
                "doc_id": "7604648749596940"
            }
            await self.client.post("/api/graphql", json=tos_data, headers=self.headers)
            
            # 3. Retry credentials
            response = await self.client.post("/api/graphql", json=check_data, headers=self.headers)
            res_json = response.json()
            auth_data = res_json.get('data', {}).get('fetchTempUserCredentials', {})

        try:
            self.access_token = auth_data['accessToken']
            # Casing fixed to match browser response
            self.abra_user_id = auth_data['viewer']['abraUserId']
            self.token_expiry = time.time() + (12 * 3600)
            if self.debug:
                print(f"DEBUG: Session established. Token: {self.access_token[:15]}... UserID: {self.abra_user_id}")
        except (KeyError, TypeError) as e:
            if self.debug:
                print(f"DEBUG: Session Establishment Failed: {e}. Raw Response: {res_json}")

    async def chat(self, message: str, conversation_id: str = None, agent_type: str = "think_fast") -> AsyncGenerator[str, None]:
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
            "agent_type": agent_type,
            "enable_thinking": agent_type in ["think_hard", "ruxp", "llama-4-maverick"],
            "dev_overrides": {
                "model": agent_type if agent_type != "think_fast" else None,
                "agent_type": agent_type
            },
            "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": agent_type != "think_fast",
            "__relay_internal__pv__WebPixelRatiorelayprovider": 1
        }
        
        data = {
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraSendMessageMutation",
            "variables": variables,
            "server_timestamps": True,
            "doc_id": "7783822248314888" # Keeping this ID from previous known-good state
        }
        
        headers = self.headers.copy()
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.abra_user_id:
            headers["X-Abra-User-Id"] = self.abra_user_id
        
        # Use multipart/mixed for streaming support
        headers["Accept"] = "multipart/mixed, application/json"
        
        async with self.client.stream("POST", "/api/graphql", json=data, headers=headers) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                
                if self.debug:
                    print(f"DEBUG RAW CHUNK: {line}")
                
                try:
                    if line.startswith('{"'):
                        chunk = json.loads(line)
                        # Check for errors in the GraphQL response
                        if "errors" in chunk:
                            yield f"[INTERNAL ERROR: {chunk['errors'][0].get('message')}]"
                            continue
                            
                        message_node = chunk.get('data', {}).get('abra_send_message', {}).get('message', {})
                        text_delta = message_node.get('text', "")
                        if text_delta:
                            yield text_delta
                except json.JSONDecodeError:
                    continue
