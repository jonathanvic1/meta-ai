from playwright.async_api import async_playwright
import json
import asyncio
import time

async def get_meta_session(debug=True):
    """
    Uses Playwright to solve the Meta AI JS challenge and extract:
    - datr cookie
    - access_token
    - abra_user_id
    """
    if debug:
        print("DEBUG: Launching headless browser to solve challenge...")
        
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Navigate to meta.ai
        await page.goto("https://www.meta.ai/")
        
        if debug:
            print("DEBUG: Waiting for page load and handling possible TOS...")
            
        await page.wait_for_timeout(3000)
        
        # Check for the birth year selection dialog
        try:
            # Look for the combobox for Year
            year_combo = page.get_by_role("combobox", name="Year")
            if await year_combo.is_visible(): # Timeout not supported on is_visible()
                if debug:
                    print("DEBUG: TOS Dialog detected. Selecting year...")
                await year_combo.click()
                # Type year and press enter
                await page.keyboard.type("1995")
                await page.keyboard.press("Enter")
                
                # Click Continue
                continue_btn = page.get_by_role("button", name="Continue")
                await continue_btn.click()
                if debug:
                    print("DEBUG: Year selected. Waiting for session hydration...")
                await page.wait_for_timeout(3000)
        except Exception as e:
            if debug:
                print(f"DEBUG: No TOS dialog or error handling it: {e}")

        # Extract tokens from window.__RELAY_API_CONFIG__
        session_data = await page.evaluate('''() => {
            return {
                config: window.__RELAY_API_CONFIG__,
                cookies: document.cookie
            };
        }''')
        
        cookies_list = await context.cookies()
        cookies_dict = {c['name']: c['value'] for c in cookies_list}
        
        await browser.close()
        
        if session_data.get('config'):
            config = session_data['config']
            return {
                "access_token": config.get('tempUserAccessToken'),
                "abra_user_id": config.get('tempUserAbraUserId'),
                "cookies": cookies_dict
            }
        
        return None

if __name__ == "__main__":
    # Test it
    res = asyncio.run(get_meta_session())
    print(json.dumps(res, indent=2))
