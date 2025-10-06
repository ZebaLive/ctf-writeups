# openECSC 2025 CTF Writeups

This repository contains my writeups for challenges from the **openECSC 2025** Capture The Flag competition.

## About openECSC

The open European Cyber Security Challenge (openECSC) is an annual cybersecurity competition that brings together talented individuals from across Europe to test their skills in various cybersecurity domains.

## Challenges Solved

### World Wide Web

- **[kittychat](web/kittychat/writeup.md)** (Medium) - Authentication bypass through undefined comparison enables XSS in username rendering.
- **[eventhub](web/eventhub/writeup.md)** (Medium) - Exploiting insecure direct object references and lack of rate limiting in the event registration process.
- **[kv-messenger](web/kv-messenger/writeup.md)** (Medium) - Exploiting a vulnerable deserialization process in the message queue service to execute arbitrary code.

### Cryptography

- **[polite-email](crypto/polite-email/writeup.md)** (Medium) - CRC collision attack using linear algebra over GF(2)

### Binary Exploitation

- **[cfp](pwn/cfp/writeup.md)** (Easy) - Buffer overflow with function pointer hijacking and ROP chain construction to bypass PIE and NX.

### Steganography

- **[calamansi](stego/calamansi/writeup.md)** (Medium) - APNG with hidden characters in transparent animation frames revealed through PNG chunk analysis and alpha channel bypass.

### Miscellaneous

- **[oci](misc/oci/writeup.md)** (Medium) - Docker Registry API exploitation with flag hidden in custom HTTP headers
- **[ruby-matcher](misc/ruby-matcher/writeup.md)** (Medium) - Regex oracle via single character code modification in Ruby
- **[organization](misc/organization/writeup.md)** (Medium) - Linux privilege escalation by bypassing wrapper scripts and monitoring xdotool automation.

## Competition Stats

- **Event**: openECSC 2025
- **Challenges Solved**: 21
- **Points**: 3923
- **Rank**: 14th place
