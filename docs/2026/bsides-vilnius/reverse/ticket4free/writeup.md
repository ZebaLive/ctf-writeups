---
title: "Ticket4Free - BSides Vilnius 2026 Reverse Engineering Writeup"
description: "BSides Vilnius 2026 Ticket4Free writeup. Reverse a hostname-gated Windows PE, invert its byte transform to recover the accepted computer name, and decode the flag."
ctf: "BSides Vilnius 2026"
date: 2026-06-03
category: reverse
difficulty: medium
points: 200
flag_format: "BSIDES{...}"
author: "zeba"
tags:
  - BSides Vilnius 2026
  - Reverse
  - Medium
  - Windows PE
---
# Ticket4Free

## Solution Overview

`Ticket.exe` is a Windows ticket generator that writes its output to `result.txt`. The "lucky" code path that prints the flag is gated by the machine's computer name: the binary reads `GetComputerNameA`, demands an 8-character name, normalizes it to lowercase, and checks it against an embedded 8-byte target. Inverting that transform recovers the one accepted hostname, and feeding the same name into the flag decoder (or just setting it in a Wine prefix and running the binary) prints the flag.

## Tools Used

- A disassembler for static triage (imports, strings, the gate logic)
- Python 3 to invert the byte transform and run the decoder
- Wine for an isolated dynamic verification

## Artifacts

- [`challenge/Ticket.exe`](challenge/Ticket.exe) — the hostname-gated Windows ticket generator
- [`challenge/result.txt`](challenge/result.txt) — the output produced once the gate is satisfied

## Solution

### Triage: what gates the flag?

Basic triage on the PE showed the usual file-writing imports (`fopen`, `fprintf`, `fwrite`), a `strncmp`, `rand`, and a couple of anti-debug checks. More telling were the readable strings in `.rdata`: `result.txt`, `This is your free ticket!`, some coordinates, `kernel32`, and — the interesting one — `GetComputerNameA`.

**First thought:** "The flag path is keyed to the machine name. Find the check, invert it."

Tracing the logic, the program resolves `GetComputerNameA` dynamically, copies the computer name into a stack buffer, asserts the length is exactly 8, then runs each normalized byte through a transform and compares against an embedded 8-byte target. None of that is random — it's fully invertible. So instead of guessing, I brute-forced the per-character transform back to the unique accepted name, which turned out to be the on-the-nose `hostname`.

### Invert the transform and decode

The same machinery that gates entry also derives the key for the flag decoder, so once I had the hostname I could reproduce the decode entirely offline:

```python
from pathlib import Path

binary = Path("Ticket.exe").read_bytes()
enc = list(binary[0x8960:0x8960 + 32])
target = list(binary[0x8980:0x8980 + 8])
perm = list(binary[0x89a0:0x89a0 + 32])

def rol8(value, count):
    count &= 7
    return ((value << count) | (value >> (8 - count))) & 0xff

def find_hosts():
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    matches = []

    def dfs(index, prefix, state):
        if index == 8:
            matches.append(prefix)
            return
        for char in alphabet:
            byte = ord(char)
            normalized = byte + 0x20 if 0 <= byte - 0x41 <= 0x19 else byte
            mixed = ((7 * index + 0x33) ^ normalized) & 0xff
            mixed = rol8(mixed, (index % 5) + 1)
            if ((((13 * index) ^ state) + mixed) & 0xff) == target[index]:
                dfs(index + 1, prefix + char, ((state * 0x21) & 0xffffffff) ^ index ^ normalized)

    dfs(0, "", 0x5a)
    return matches

def key_from_host(host):
    data = [ord(char) for char in host] + [0]
    byte = data[0]
    index = 0
    key = 0x6d
    while byte:
        if 0 <= byte - 0x41 <= 0x19:
            byte += 0x20
        mixed = (index * 0x1d) & 0xffffffff
        index += 1
        key = (key & ~0xff) | rol8(key & 0xff, 3)
        mixed ^= byte
        byte = data[index]
        key ^= mixed
    return (key + 0x3d) & 0xffffffff

def magic_div3(value):
    high = (value * 0xaaaaaaaaaaaaaaab) >> 64
    return (high & 0xfffffffffffffffe) + (high >> 1)

host = find_hosts()[0].lower()
key = key_from_host(host)
out = [0] * 32

for index, position in enumerate(perm):
    left = (position * 17 + key) & 0xff
    rotate = (position - magic_div3(position) + 1) & 0xff
    right = ((0xa7 - position) & 0xff) ^ enc[index]
    out[position] = rol8(left, rotate) ^ right

print(host)
print(bytes(out).decode())
```

Running it prints both the accepted name and the flag:

```text
hostname
BSIDES{t4rg3t_i5_h3r3_und3r_th3}
```

### Sanity check with Wine

I didn't want to trust my reimplementation blindly, so I confirmed it dynamically: set the computer name to `hostname` inside a throwaway Wine prefix, run the real binary, and watch it write the identical flag to `result.txt`.

```bash
WINEPREFIX=/tmp/ticket4free-wine wine reg add \
  'HKLM\System\CurrentControlSet\Control\ComputerName\ComputerName' \
  /v ComputerName /t REG_SZ /d hostname /f
WINEPREFIX=/tmp/ticket4free-wine wine reg add \
  'HKLM\System\CurrentControlSet\Control\ComputerName\ActiveComputerName' \
  /v ComputerName /t REG_SZ /d hostname /f
WINEPREFIX=/tmp/ticket4free-wine wine ./Ticket.exe
cat result.txt
```

Same flag, straight from the binary — case closed.

## Flag

```text
BSIDES{t4rg3t_i5_h3r3_und3r_th3}
```

---

[← Back to BSides Vilnius 2026](../../README.md)
