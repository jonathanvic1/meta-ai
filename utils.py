import nodriver as uc
import json
import asyncio
import re
import os

async def get_meta_session(debug=True):
    """
    Uses nodriver (CDP-based, undetected) with explicit browser args.
    """
    if debug:
        print("DEBUG: Starting nodriver Booster with explicit args...")
        
    session_info = {
        "access_token": None,
        "abra_user_id": None,
        "lsd": None,
        "cookies": {}
    }

    browser_path = "/Users/jonathanquantumga/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

    if not os.path.exists(browser_path):
        return None

    try:
        if debug: print(f"DEBUG: Launching browser...")
        # Fix: pass sandbox flags in browser_args
        browser = await uc.start(
            browser_executable_path=browser_path,
            browser_args=['--no-sandbox', '--disable-setuid-sandbox', '--headless=new'],
            headless=True
        )
        
        page = await browser.get("https://www.meta.ai/")
        await asyncio.sleep(5)
        
        await page.reload()
        await asyncio.sleep(5)

        # 1. Extract tokens
        config = await page.evaluate("window.__RELAY_API_CONFIG__")
        if config:
            session_info["access_token"] = config.get("tempUserAccessToken")
            session_info["abra_user_id"] = config.get("tempUserAbraUserId")

        # 2. Extract LSD
        content = await page.get_content()
        lsd_match = re.search(r'"lsd":"(.*?)"', content) or re.search(r'\["LSD",\[\],{"token":"(.*?)"}', content)
        if lsd_match:
            session_info["lsd"] = lsd_match.group(1) or lsd_match.group(2)

        # 3. Capture Cookies
        cookies = await browser.cookies.get_all()
        for cookie in cookies:
            session_info["cookies"][cookie.name] = cookie.value

        await browser.stop()
        return session_info if session_info["access_token"] else None
            
    except Exception as e:
        if debug: print(f"DEBUG: nodriver error: {e}")
        try: await browser.stop()
        except: pass

    return None

async def get_mcp_session(debug=True):
    return {
        "access_token": "ecto1:Q8yEDAER2UrWLbYLT9NoGl-YciVn_LAFbdz0uPS_e87NCxVRqWkC6qz-cQqPViBjZJDHD_VP6ssF4otNBAqiBJ7JTFxlSSXlzHD3oD4OGVWi-Se7d0Kf-KFDgDzbz5lAdXCJgcQ5eDyUo3OYuUWxKuuSiA18T2ehea9_HaefDjf5XD8J40jWTMy2d5WLpGjhIQ5-yfhHlwN3_RvujIeWV8B45Bbcj0VLqgGHVLxs9s2SAZxaJ-hgSVC2XnaZcYmZVzCyGweO5VEK-BGzTvQ6b9gHEV5sJgCGNh-gSF5BwPL0wH3WniWXXpuJiwYkrNBGxUIrRHeT2IxuQCUjSqG2iH85a0wXj_RpPPAA49p4vAnGbyIADtHL_-0N0aXedWbOIg",
        "abra_user_id": "992315297304883",
        "lsd": "AVrtfXpWpRE",
        "cookies": {
            "datr": "GQilaVBFJ60Ho3kzZZKfHCqX",
            "rd_challenge": "Q_6hBQNXAT1yVgX_Xp7USjKSF45oliMiYzXgh7_Ztk7-jiWZjwYQfY7Htlxa_JgoFLARALyZNX9cTfypoVQmOt1vCw"
        }
    }

if __name__ == "__main__":
    res = asyncio.run(get_meta_session())
    print(json.dumps(res, indent=2))
