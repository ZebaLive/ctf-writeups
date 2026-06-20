---
title: "S3cur3 - BSides Vilnius 2026 Crypto Challenge Writeup"
description: "BSides Vilnius 2026 S3cur3 writeup. Recover an RSA server key via a shared-prime GCD, then decrypt a captured TLS 1.2 RSA session to read the flag from the admin response."
ctf: "BSides Vilnius 2026"
date: 2026-06-01
category: crypto
difficulty: medium
points: 150
flag_format: "BSIDES{...}"
author: "zeba"
tags:
  - BSides Vilnius 2026
  - Crypto
  - Medium
  - RSA
  - TLS
---
# S3cur3

## Solution Overview

The challenge hands you three things: an RSA public key (`pub.pem`), an RSA-encrypted blob (`secret.enc`), and a PCAP of a TLS 1.2 session to `router.internal.bsides.local`. The handshake uses `TLS_RSA_WITH_AES_128_CBC_SHA`, so whoever owns the server's RSA private key can decrypt the session outright. The "vibecoded" key generator gave itself away: it reused a prime between the throwaway `pub.pem` and the server certificate, so `gcd(n_pub, n_cert)` factors the server modulus instantly. Rebuild the private key, hand it to Wireshark, and the decrypted `GET /admin` response carries the flag.

## Tools Used

- Python 3 with the `cryptography` library
- `tshark` / Wireshark (TLS RSA key decryption + HTTP object export)

## Artifacts

- [`challenge/pub.pem`](challenge/pub.pem) — the "dummy" RSA public key that shares a prime with the server cert
- [`challenge/secret.enc`](challenge/secret.enc) — the RSA-encrypted blob

*(The 40 MB `traffic.pcapng` TLS capture is omitted here for size; the GCD-recovered key decrypts it as shown below.)*

## Solution

### When "secure" reuses a prime

The first thing that caught my eye was that I'd been given a public key (`pub.pem`) that didn't obviously belong to the captured session. Why ship a second RSA key unless it *relates* to the one in the PCAP? The cipher suite negotiated in the handshake was `TLS_RSA_WITH_AES_128_CBC_SHA` — the old, non-forward-secret kind where the client encrypts the premaster secret directly to the server's RSA key. That meant the whole session was decryptable *if* I could recover that private key.

**First thought:** "Two RSA moduli from the same sloppy generator... let me just `gcd` them."

If two RSA keys accidentally share one prime, their moduli share that factor, and `gcd(n1, n2)` pops it out in microseconds — no factoring required. So the plan was: pull the server certificate out of the PCAP, compute `gcd` against the dummy `pub.pem` modulus, reconstruct the private key, then let Wireshark replay the decryption for me.

### Recover the key and decrypt the session

```bash
# 1. Extract the server certificate from the PCAP
tshark -r traffic.pcapng -Y 'tls.handshake.type == 11' \
    -T fields -e tls.handshake.certificate 2>/dev/null | head -1 > /tmp/cert.hex

python3 << 'EOF'
import base64, binascii
from math import gcd
from cryptography import x509
from cryptography.hazmat.primitives.serialization import (
    load_pem_public_key, Encoding, PrivateFormat, NoEncryption,
)
from cryptography.hazmat.primitives.asymmetric import rsa

# Convert cert hex to PEM
der = binascii.unhexlify(open('/tmp/cert.hex').read().strip())
pem = b'-----BEGIN CERTIFICATE-----\n' + base64.encodebytes(der) + b'-----END CERTIFICATE-----\n'
open('/tmp/srv.crt', 'wb').write(pem)

# Factor the server modulus using gcd with the dummy pub.pem
n_pub  = load_pem_public_key(open('pub.pem', 'rb').read()).public_numbers().n
cert   = x509.load_pem_x509_certificate(pem)
n, e   = cert.public_key().public_numbers().n, cert.public_key().public_numbers().e
p = gcd(n_pub, n); q = n // p
assert p * q == n and 1 < p < n
d = pow(e, -1, (p-1) * (q-1))

priv = rsa.RSAPrivateNumbers(
    p, q, d, d % (p-1), d % (q-1), pow(q, -1, p),
    rsa.RSAPublicNumbers(e, n),
).private_key()
open('/tmp/srv.key', 'wb').write(
    priv.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
)
EOF

# 2. Give Wireshark the recovered RSA key and export the decrypted HTTP object
echo '"/tmp/srv.key",""' > ~/.config/wireshark/rsa_keys
mkdir -p /tmp/httpobj
tshark -r traffic.pcapng --export-objects 'http,/tmp/httpobj' -Y 'tcp.port==4443' >/dev/null

# 3. Grab the flag from the admin response
grep -oE 'BSIDES\{[^}]+\}' /tmp/httpobj/admin
```

The `assert p * q == n` passing was the giveaway moment — the shared prime really was there, so the private key reconstruction was exact. Once `tshark` had the key in its `rsa_keys` UAT, it transparently decrypted the RSA-keyed session and let me export the HTTP object, and the `/admin` response handed over the flag:

```
BSIDES{15_1t_s0_b4d_t0_sh4re_4_pr1m3?}
```

The flag answers its own question: yes, sharing a prime is exactly that bad.

## Flag

```
BSIDES{15_1t_s0_b4d_t0_sh4re_4_pr1m3?}
```

---

[← Back to BSides Vilnius 2026](../../README.md)
