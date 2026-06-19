---
title: "BSides Vilnius 2026 CTF Writeups - Selected Solutions"
description: "Selected writeups from BSides Vilnius 2026 CTF: scriptless CSS font exfiltration into an AWS cloud chain, a Dahua PTZ camera QR recovery, a buffer-overflow container escape, a hostname-gated PE reverse, and a shared-prime RSA TLS decrypt."
---

# BSides Vilnius 2026 Writeups

A selection of my writeups from the **BSides Vilnius 2026** CTF, spanning web, pwn, reverse, and crypto.

## Challenges

### Web Exploitation

- **[BSides Nail Salon](web/nail-salon/writeup.md)** (Hard) — Scriptless CSS `@font-face`/`unicode-range` token exfiltration chained into an AWS confused-deputy → Secrets Manager → EKS → Kyverno apiCall leak → IRSA → CloudFront OAC cross-account S3 read.
- **[Operation (DroneOps PTZ Camera)](web/operation/writeup.md)** (Medium) — Crack a Dahua camera password from an MD5 value, remove a privacy mask via the config API, and beat IR night-grain by frame-averaging to decode a hidden QR.

### Binary Exploitation (Pwn)

- **[BOF2root](pwn/bof2root/writeup.md)** (Medium) — Source-port-53 ACL bypass, a `jmp rsp` stack overflow into an executable stack, then a Docker-socket container escape to read the host.

### Reverse Engineering

- **[Ticket4Free](reverse/ticket4free/writeup.md)** (Medium) — Invert a hostname-gated Windows PE's byte transform to recover the accepted computer name and decode the flag, verified under Wine.

### Cryptography

- **[S3cur3](crypto/s3cur3/writeup.md)** (Medium) — A shared-prime RSA `gcd` factor recovers the server key, which decrypts a captured TLS 1.2 RSA session to reveal the flag.
