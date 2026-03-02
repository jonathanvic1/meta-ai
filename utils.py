from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import json
import asyncio
import time
import os
import tempfile

async def get_meta_session(debug=True):
    """
    Uses Playwright with a Persistent Context and SlowMo to look human.
    """
    if debug:
        print("DEBUG: Launching persistent browser context (human-mimic)...")
        
    session_info = {
        "access_token": None,
        "abra_user_id": None,
        "lsd": None,
        "cookies": {}
    }

    # Create a temp directory for the persistent profile
    user_data_dir = tempfile.mkdtemp()

    async with async_playwright() as p:
        # Launch with slow_mo to avoid rapid-fire detection
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            slow_mo=100,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = await browser_context.new_page()
        await stealth_async(page)

        # Network interception
        async def handle_response(response):
            if "api/graphql" in response.url:
                try:
                    body = await response.json()
                    creds = body.get("data", {}).get("fetchTempUserCredentials")
                    if creds and creds.get("accessToken"):
                        session_info["access_token"] = creds["accessToken"]
                        session_info["abra_user_id"] = creds.get("viewer", {}).get("abraUserId")
                        if debug: print(f"DEBUG: Captured Token: {session_info['access_token'][:15]}...")
                except:
                    pass

        page.on("response", handle_response)

        # Navigate
        await page.goto("https://www.meta.ai/", wait_until="networkidle")
        
        # Human-like wait
        await asyncio.sleep(3)

        # Handle Birth Year / TOS
        try:
            year_combo = page.get_by_role("combobox", name="Year")
            if await year_combo.is_visible():
                if debug: print("DEBUG: Completing TOS flow...")
                await year_combo.click()
                await page.keyboard.type("1995")
                await page.keyboard.press("Enter")
                await asyncio.sleep(1)
                await page.get_by_role("button", name="Continue").click()
                # Wait for the credential call that follows TOS acceptance
                await page.wait_for_selector("text=Ask anything", timeout=10000)
        except:
            pass

        # Final Extraction check
        if not session_info["access_token"]:
            # Last ditch attempt to pull from JS memory
            session_info["access_token"] = await page.evaluate("window.__RELAY_API_CONFIG__?.tempUserAccessToken")
            session_info["abra_user_id"] = await page.evaluate("window.__RELAY_API_CONFIG__?.tempUserAbraUserId")

        # Get Cookies
        cookies_list = await browser_context.cookies()
        session_info["cookies"] = {c['name']: c['value'] for c in cookies_list}
        
        # Extract LSD
        html = await page.content()
        import re
        lsd_match = re.search(r'"lsd":"(.*?)"', html)
        if lsd_match:
            session_info["lsd"] = lsd_match.group(1)

        await browser_context.close()
        
        # Cleanup temp dir
        import shutil
        try:
            shutil.rmtree(user_data_dir)
        except:
            pass

        if session_info["access_token"]:
            return session_info
        
        return None

if __name__ == "__main__":
    res = asyncio.run(get_meta_session())
    print(json.dumps(res, indent=2))
