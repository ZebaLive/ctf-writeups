---
title: "CTF Writeups & Solutions - Web Exploitation, Pwn, Crypto, Misc"
description: "Comprehensive CTF writeups and solutions from ECSC 2025, openECSC 2025, BSides Vilnius 2026, and Mārtiņa-CTF 2025. Learn web exploitation, binary exploitation, cryptography, steganography, and misc challenges with detailed walkthroughs and exploit scripts."
hide:
  - navigation
  - toc
---

<div class="ctf-hero" markdown>

<img src="assets/logo.png" alt="zeba" class="ctf-avatar" width="96" height="96">

<span class="ctf-kicker">Personal CTF archive · by zeba</span>

# CTF Writeups

<p>I'm <strong>zeba</strong>. This is where I document the CTF challenges I've solved — my approach, the exploit scripts, and notes on what worked. All my own writeups, kept here for reference.</p>

<div class="ctf-cta" markdown>
[Latest: HTB Cyber Apocalypse 2026](2026/htb-cyber-apocalypse/README.md){ .md-button .md-button--primary }
[Browse by tag](tags.md){ .md-button }
[:fontawesome-brands-github: GitHub](https://github.com/ZebaLive){ .md-button }
</div>

<div class="ctf-stats">
  <div class="ctf-stat"><span class="num">5</span><span class="label">Competitions</span></div>
  <div class="ctf-stat"><span class="num">20</span><span class="label">Writeups</span></div>
  <div class="ctf-stat"><span class="num">6</span><span class="label">Categories</span></div>
  <div class="ctf-stat"><span class="num">1st</span><span class="label">Best Finish</span></div>
</div>

</div>

## Competitions

<div class="grid cards" markdown>

-   :material-skull-crossbones:{ .lg .middle } &nbsp; **HTB Cyber Apocalypse 2026**

    ---

    Hack The Box's flagship event — team finished **341st** with **40,500 points** (78/136 flags). Secure-coding, GamePwn, ML, and LLM prompt-injection.

    [:octicons-arrow-right-24: Browse writeups](2026/htb-cyber-apocalypse/README.md)

-   :material-shield-bug:{ .lg .middle } &nbsp; **BSides Vilnius 2026**

    ---

    Selected writeups across **web, pwn, reverse, and crypto** — CSS exfiltration into AWS IAM, container escapes, RSA/TLS, and PE reversing.

    [:octicons-arrow-right-24: Browse writeups](2026/bsides-vilnius/README.md)

-   :material-trophy:{ .lg .middle } &nbsp; **Mārtiņa-CTF 2025**

    ---

    **1st place (Remote)** — 12 personal solves. Blind SQL injection, WAF bypass, and Git history exploitation.

    [:octicons-arrow-right-24: Browse writeups](2025/martina-ctf/README.md)

-   :material-flag-checkered:{ .lg .middle } &nbsp; **ECSC 2025**

    ---

    European Cybersecurity Challenge — PHP type juggling to webshell, and Bluetooth HID PCAP reconstruction.

    [:octicons-arrow-right-24: Browse writeups](2025/ecsc/README.md)

-   :material-earth:{ .lg .middle } &nbsp; **openECSC 2025**

    ---

    21 challenges solved, 14th place. CSP/Trusted-Types bypasses, prototype pollution, ROP, APNG stego, and more.

    [:octicons-arrow-right-24: Browse writeups](2025/openecsc/README.md)

</div>

## Categories

<div class="grid cards" markdown>

-   :material-web:{ .lg .middle } &nbsp; **Web Exploitation**

    ---

    SQLi, XSS, SSRF, CSP & Trusted-Types bypass, CRLF injection, prototype pollution, CSS exfiltration, cloud/IAM abuse.

-   :material-memory:{ .lg .middle } &nbsp; **Binary Exploitation (Pwn)**

    ---

    Buffer overflows, ROP chains, function-pointer hijacking, libc leaks, container escapes, and GamePwn — live memory patching of a running game's native state machine.

-   :material-lock:{ .lg .middle } &nbsp; **Cryptography**

    ---

    RSA shared-prime attacks, TLS session decryption, CRC forgery, and linear algebra over GF(2).

-   :material-image-search:{ .lg .middle } &nbsp; **Stego & Forensics**

    ---

    APNG frame analysis, PCAP reconstruction, and hidden-data extraction.

-   :material-bug:{ .lg .middle } &nbsp; **Reverse Engineering**

    ---

    Windows PE analysis, byte-transform inversion, and gated-binary recovery.

-   :material-dots-horizontal:{ .lg .middle } &nbsp; **Miscellaneous**

    ---

    Docker registry enumeration, Git history analysis, Linux privesc, and Ruby regex oracles.

</div>

---

!!! info "Disclaimer & License"
    All materials are provided for **educational and research purposes only** — use responsibly and respect CTF competition rules. Licensed under the [MIT License](https://github.com/ZebaLive/ctf-writeups/blob/main/LICENSE).
