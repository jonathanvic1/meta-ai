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
        self.token_expiry = 0

    async def _ensure_session(self):
        """Initializes an anonymous session using the newly discovered FetchTempUserCredentialsMutation."""
        if self.access_token and time.time() < self.token_expiry:
            return

        # 1. Fetch main page to get LSD token
        response = await self.client.get("/")
        html = response.text
        lsd_match = re.search(r'\["LSD",\[\],{"token":"(.*?)"}', html)
        if lsd_match:
            self.lsd = lsd_match.group(1)
        
        # 2. Use the discovered useFetchTempUserCredentialsMutation (ID: 2943394199ee6545d1f0c69d5b6e577f)
        # This is more modern than the TOS acceptance mutation.
        data = {
            "lsd": self.lsd,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useFetchTempUserCredentialsMutation",
            "variables": json.dumps({}), # Usually empty for this mutation
            "doc_id": "2943394199ee6545d1f0c69d5b6e577f"
        }
        
        response = await self.client.post("/api/graphql/", data=data, headers=self.headers)
        res_json = response.json()
        
        try:
            auth_data = res_json['data']['fetchTempUserCredentials']
            if auth_data.get('success'):
                self.access_token = auth_data['accessToken']
                self.token_expiry = time.time() + (12 * 3600)
            else:
                # Fallback to old mutation if this fails
                await self._fallback_ensure_session()
        except (KeyError, TypeError):
            await self._fallback_ensure_session()

    async def _fallback_ensure_session(self):
        """Original fallback mutation."""
        data = {
            "lsd": self.lsd,
            "variables": json.dumps({"dob": "1999-01-01", "icebreaker_type": "TEXT"}),
            "doc_id": "7604648749596940"
        }
        response = await self.client.post("/api/graphql/", data=data, headers=self.headers)
        res_json = response.json()
        try:
            auth_data = res_json['data']['abra_accept_tos_for_temp_user']['new_temp_user_auth']
            self.access_token = auth_data['access_token']
            self.token_expiry = time.time() + (12 * 3600)
        except:
            print("Critial Error: Could not establish Meta AI session.")

    async def chat(self, message: str, conversation_id: str = None, agent_type: str = "think_fast") -> AsyncGenerator[str, None]:
        await self._ensure_session()
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        offline_threading_id = str(uuid.uuid4())
        
        # Determine if we should enable thinking (from JS discovery)
        enable_thinking = True if agent_type in ["think_hard", "ruxp", "llama-4-maverick"] else False
        
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
            # DISCOVERY: Adding internal agent and thinking flags
            "agent_type": agent_type,
            "enable_thinking": enable_thinking,
            # DISCOVERY: Potential developer overrides
            "dev_overrides": {
                "model": "llama-4-maverick" if agent_type == "llama-4-maverick" else None,
                "agent_type": agent_type
            },
            "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": True if agent_type != "think_fast" else False,
            "__relay_internal__pv__WebPixelRatiorelayprovider": 1
        }
        
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
