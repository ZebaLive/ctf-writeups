# openECSC 2025

## Challenge: OCI

## Tags: misc, web

## Difficulty: Medium

## Table of Contents

- [Solution Overview](#solution-overview)
- [Tools Used](#tools-used)
- [Solution](#solution)
- [Solution Script](#solution-script)
- [Flag](#flag)

### Solution Overview

The challenge presents a Docker Registry API that masquerades as an official `nginx:alpine` repository. Through systematic enumeration of available tags, I discovered a hidden `secret` build alongside the expected `alpine` tag. While the additional layers in the secret build contained only decoy HTML files, the true flag was embedded as a custom HTTP header (`X-Injected-Secret`) in the blob response, encoded in Base64.

### Tools Used

- `curl` for Docker Registry API interaction and HTTP header inspection
- `tar` and `gzip` for OCI layer extraction and analysis
- `rg` (ripgrep) for efficient content searching within extracted layers
- `python` (standard library) for Base64 decoding

### Solution

When approaching this challenge, I began by investigating the nature of the target service. The URL suggested I was dealing with some form of container registry, so I started by verifying that it implemented the Docker Registry API protocol. Querying the standard `/v2/` endpoint revealed the telltale JSON response `{"version":"1.1"}`, confirming I was indeed working with a legitimate Docker Registry implementation.

```bash
curl -ks https://9995e585-fa2f-4889-9d28-f6bcf0918a7a.openec.sc:1337/v2/
```

With the registry protocol confirmed, I naturally proceeded to explore what repositories and tags were available. The tag enumeration for the `/nginx` repository revealed something immediately interesting—alongside the expected `alpine` tag, there was a mysterious `secret` tag that clearly warranted investigation.

```bash
curl -ks https://9995e585-fa2f-4889-9d28-f6bcf0918a7a.openec.sc:1337/v2//nginx/tags/list
```

Curiosity piqued by the `secret` tag, I retrieved its manifest to understand the layer composition and identify any differences from the standard `alpine` build. The manifest revealed additional layers that seemed to contain custom content, so I downloaded and extracted them to examine their contents.

```bash
curl -ks -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' \
     https://9995e585-fa2f-4889-9d28-f6bcf0918a7a.openec.sc:1337/v2//nginx/manifests/secret

curl -ksO https://9995e585-fa2f-4889-9d28-f6bcf0918a7a.openec.sc:1337/v2//nginx/blobs/sha256:ed14ee4edc82783d49e5dfee29bcd8649dc701051bcca1fb1dd90f40d0da9038
tar -tzf sha256:ed14ee4edc82783d49e5dfee29bcd8649dc701051bcca1fb1dd90f40d0da9038
```

The extracted layer revealed three files: `index.html`, `secret.html`, and `.env`. However, upon examination, each contained different unhelpful messages designed to mislead: `No flags here :/`, `I wish I had a flag`, and `NOTFLAG="nahthiswouldbetooeasy"`. The playful nature of these decoy messages felt deliberate—like the challenge authors were clearly directing my attention elsewhere.

This realization prompted me to step back and reconsider the attack surface. If the file contents were intentional misdirection, perhaps the flag was hidden in the HTTP transport layer itself. I decided to examine the response headers more carefully, using a HEAD request to access the full header information without downloading the entire blob.

```bash
curl -ksI https://9995e585-fa2f-4889-9d28-f6bcf0918a7a.openec.sc:1337/v2//nginx/blobs/sha256:ed14ee4edc82783d49e5dfee29bcd8649dc701051bcca1fb1dd90f40d0da9038
```

This approach immediately paid off. Among the response headers, I discovered an unusual custom header: `X-Injected-Secret` containing what appeared to be a Base64-encoded string.

```text
X-Injected-Secret: T3BlbkVDU0N7YzNydDFmMWVkLTBDMV9kM3ZlbDBwZXJfMjAyNV9lNjg5OWI5ZTAyMDR9
```

With the Base64-encoded secret in hand, the final step was straightforward decoding using Python's built-in capabilities:

```python
import base64

secret = "T3BlbkVDU0N7YzNydDFmMWVkLTBDMV9kM3ZlbDBwZXJfMjAyNV9lNjg5OWI5ZTAyMDR9"
print(base64.b64decode(secret).decode())
```

This revealed the flag: `OpenECSC{c3rt1f1ed-0C1_d3vel0per_2025_e6899b9e0204}`, cleverly hidden not in the container layers themselves, but in the HTTP headers used to deliver them.

### Solution Script

The complete solution can be automated using standard Python libraries:

```python
#!/usr/bin/env python3
"""
OCI Challenge Solution
Extracts flag from X-Injected-Secret header in Docker Registry blob response
"""
import base64
import ssl
import urllib.request

BASE_URL = "https://9995e585-fa2f-4889-9d28-f6bcf0918a7a.openec.sc:1337"
BLOB_PATH = "/v2//nginx/blobs/sha256:ed14ee4edc82783d49e5dfee29bcd8649dc701051bcca1fb1dd90f40d0da9038"

# Create request with SSL verification disabled for challenge environment
request = urllib.request.Request(f"{BASE_URL}{BLOB_PATH}", method="HEAD")
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

try:
    with urllib.request.urlopen(request, context=context) as response:
        encoded_secret = response.headers["X-Injected-Secret"]
        flag = base64.b64decode(encoded_secret).decode()
        print(f"Flag: {flag}")
except Exception as e:
    print(f"Error: {e}")
```

### Flag

**`OpenECSC{c3rt1f1ed-0C1_d3vel0per_2025_e6899b9e0204}`**
