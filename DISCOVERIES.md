# Meta AI Internal Discoveries & Leaks

This document tracks findings reverse-engineered from the Meta AI frontend chunks (specifically `dfc9ad9b0f73816c.js`).

## 🚨 Major Model Leaks (Internal Overrides)
The following models are listed as developer overrides in the Meta AI source code. This suggests Meta is internally benchmarking or providing access to unreleased models:

### **Next-Gen Models**
- **Llama 4 Maverick**: Confirmed internal testing of the Llama 4 foundation.
- **Claude Sonnet 4.5 & Opus 4.5**: Future Anthropic models.
- **Gemini 2.5 (Pro/Flash/Lite)** & **Gemini 3 Pro Preview**: Future Google models.
- **GPT-5.1 Codex**: Confirmation of Meta tracking or testing against future OpenAI "GPT-5" series.
- **Grok 4.1 Fast**: xAI's future iteration.

### **Production Internal Labels**
- `omni-prod`: Llama Assistant (Prod)
- `think_hard` / `big_brain`: Reasoning-heavy models.
- `think_fast`: Default low-latency Llama 3.1.
- `qwen-3-235b`: Alibaba's Qwen 3 large model.

---

## 🛠️ Internal Tools & Agent Capabilities
The assistant has internal support for the following specialized tools (some currently hidden):

- **`google_calendar_query`**: Direct Google Calendar integration.
- **`convo_recall`**: Long-term conversational memory/retrieval.
- **`meta_post_search`**: Searching through Facebook/Instagram social posts.
- **`imagine`**: Image generation (Abra-native).
- **`mks_endless_scroll_widget`**: UI-based content discovery.
- **`stocks_widget` / `sports_widget` / `weather_widget`**: Specialized data fetchers.

---

## 🔑 Technical IDs & Endpoints
Useful for further reverse-engineering of the GraphQL API:

- **Anonymous Credentials Mutation**: `useFetchTempUserCredentialsMutation`
- **Hex ID**: `2943394199ee6545d1f0c69d5b6e577f` (Stable as of March 2026)
- **TOS Mutation ID**: `7604648749596940` (Deprecated/Requires LSD)
- **Chat Send Mutation ID**: `7783822248314888`
- **Internal WebSocket (DGW)**: `wss://[host].facebook.com:8086/ws`

---

## 🧠 Reasoning Modes
Meta tracks different "Clippy Streaming Behaviors" and agent types:
- `THINK_HARD`: Enabled via `enableThinking: true`.
- `TF_GEMINI_3_FLASH`: A specific agent type for fast-response benchmarking.
- `TF_LOGGED_OUT`: The anonymous mode used by this wrapper.

---

## 🕵️ Browser & Environment Investigation (March 2026)

### 1. The "Ghost Page" Defense
Meta AI employs a "Ghost Page" strategy against automated browsers (Playwright, Puppeteer, nodriver). Even if the browser successfully bypasses Cloudflare, the server detects the TLS fingerprint or headless signal and serves a version of the page where:
- `window.__RELAY_API_CONFIG__` is empty or missing.
- Critical tokens like `LSD` and `accessToken` are stripped from the HTML.
- The `fetchTempUserCredentials` GraphQL mutation is never triggered.

### 2. CDP vs WebDriver
- **WebDriver (Playwright/Selenium)**: Easily detected via `navigator.webdriver`.
- **CDP (nodriver/Chrome DevTools MCP)**: Communicates directly with the browser. This is much more effective but still susceptible to TLS-level detection if the client's SSL handshake doesn't match a standard Chrome browser.

### 3. Environment Isolation Issues
In virtualized or emulated environments (like Rosetta on Mac), CDP-based libraries like `nodriver` can fail to establish a WebSocket connection to the browser's debugging port due to process isolation, even if the browser binary itself is running correctly.

### 4. Verified Workarounds
- **Double-Load Strategy**: Navigating, waiting for the challenge to settle, and then reloading often triggers a "refresh" of the session that provides fresh tokens.
- **TLS Impersonation**: Using `curl_cffi` with `impersonate="chrome"` is mandatory for subsequent HTTP requests to prevent `Bad Request` errors.
- **Manual Bridge**: Capturing tokens from a real, persistent browser session remains the most reliable "bootstrap" method for high-trust requirements.
