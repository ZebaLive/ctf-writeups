# openECSC 2025

## Challenge: Polite Email

## Tags: crypto

## Dificulty: Medium

## Table of Contents

- [Solution Overview](#solution-overview)
- [Tools Used](#tools-used)
- [Solution](#solution)
- [Solution Script](#solution-script)
- [Flag](#flag)

### Solution Overview

The service expects me to send the challenge author a polite e-mail that already contains their canned text. A response with the flag is only returned when:

- The mail body includes the exact polite template the challenge author provided.
- A single integer "MAC" value matches the output of **five different CRC algorithms** (three 32-bit variants and two 64-bit ones) when run over the submitted mail body.

CRC computations are linear over GF(2), so I can treat the MAC requirement as a system of linear equations in the bits I control. By extending the polite mail with carefully chosen bytes I ensured that every CRC evaluates to zero, allowing me to submit a MAC of `0` and still pass all checks.

### Tools Used

1. `python3` with the `fastcrc` module (already packaged with the challenge)
2. `ncat` for interacting with the remote service

### Solution

When I first looked at this challenge, I started by examining the `email.py` file to understand what exactly the service was checking. I immediately noticed the `ImpossibleMAC` function - it was requiring that a single MAC value matches the output of **five different CRC algorithms**: three 32-bit variants (`crc32.autosar`, `crc32.iscsi`, `crc32.iso_hdlc`) and two 64-bit ones (`crc64.go_iso`, `crc64.xz`). My first thought was "this seems impossible" - hence the function name!

But then I remembered a key property of CRC algorithms: they're linear over GF(2). This means that if I have a message and I XOR it with some other data, the CRC of the result is the XOR of the individual CRCs. This gave me an idea: what if I could append some carefully chosen bytes to the polite email template such that all five CRCs evaluate to zero? Then I could submit a MAC of `0` and it would match all the CRC outputs.

My approach became: take the required polite email template (with my chosen sender name "Me"), append some unknown bytes to it, and solve for those bytes such that every CRC algorithm returns zero.

I realized this was essentially a system of linear equations over GF(2). Each CRC algorithm produces a certain number of bits (32 or 64), and each bit of the output is a linear combination of the input bits. So I had 224 total equations (32+32+32+64+64) that I needed to satisfy.

To build this system, I computed the "base" CRC values for the polite email plus a zero suffix, then for each bit position in my unknown suffix, I flipped that bit and recorded how it changed each CRC output. This gave me the coefficient matrix for my linear system.

With 28 bytes of unknown suffix (224 bits), I had exactly 224 variables for my 224 equations - a perfect square system that I could solve using Gaussian elimination over GF(2).

I implemented the Gaussian elimination algorithm, solved for the suffix bits, converted them back to bytes, and tested my solution. When I ran all five CRC algorithms on the polite email plus my computed suffix, they all returned zero!

Finally, I hex-encoded the complete message, submitted it to the service with MAC value `0`, and received the flag.

```python
# Example interaction (shortened):
# python email.py
# Enter name: Me
# Enter mail: 4465...dd08
# Enter MAC: 0
# => returns the flag
```

### Solution Script

```python
from fastcrc import crc32, crc64

CRC32S = ["autosar", "iscsi", "iso_hdlc"]
CRC64S = ["go_iso", "xz"]
ALGS = [(crc32, name, 32) for name in CRC32S] + [(crc64, name, 64) for name in CRC64S]

sender = "Me"
recipient = "Challenge Author"
body = "Pretty please give me the flag."
polite_email = f"""Dear {recipient}.

{body}

Best regards,
{sender}""".encode()

suffix_len = 28
num_bits = suffix_len * 8
base_suffix = bytes(suffix_len)

bases = []
bit_diffs = []

# Collect base values and XOR effects of flipping each suffix bit
for module, name, width in ALGS:
    func = getattr(module, name)
    base_val = func(polite_email + base_suffix)
    bases.append((base_val, width))
    diffs = []
    for bit in range(num_bits):
        test = bytearray(base_suffix)
        byte_idx, bit_idx = divmod(bit, 8)
        test[byte_idx] = 1 << (7 - bit_idx)
        diff = base_val ^ func(polite_email + bytes(test))
        diffs.append(diff)
    bit_diffs.append((diffs, width))

# Build the linear system rows over GF(2)
rows = []
rhs = []
for (base, width), (diffs, _) in zip(bases, bit_diffs):
    for bit_pos in range(width):
        bit_mask = 1 << (width - 1 - bit_pos)
        row_mask = 0
        for col, diff in enumerate(diffs):
            if diff & bit_mask:
                row_mask |= 1 << col
        rows.append(row_mask)
        rhs.append(1 if (base & bit_mask) else 0)

# Gaussian elimination (mod 2)
solution = [0] * num_bits
pivot_row = 0
pivot_cols = []
for col in range(num_bits):
    pivot = None
    for r in range(pivot_row, len(rows)):
        if (rows[r] >> col) & 1:
            pivot = r
            break
    if pivot is None:
        continue
    rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
    rhs[pivot_row], rhs[pivot] = rhs[pivot], rhs[pivot_row]
    pivot_cols.append(col)
    for r in range(len(rows)):
        if r != pivot_row and ((rows[r] >> col) & 1):
            rows[r] ^= rows[pivot_row]
            rhs[r] ^= rhs[pivot_row]
    pivot_row += 1

# Back-substitute to recover suffix bits
for idx in range(len(pivot_cols) - 1, -1, -1):
    col = pivot_cols[idx]
    row_mask = rows[idx]
    value = rhs[idx]
    mask = row_mask >> (col + 1)
    j = col + 1
    while mask:
        if mask & 1:
            value ^= solution[j]
        mask >>= 1
        j += 1
    solution[col] = value

# Turn bit solution into bytes
suffix = bytearray(suffix_len)
for bit, val in enumerate(solution):
    if val:
        byte_idx, bit_idx = divmod(bit, 8)
        suffix[byte_idx] |= 1 << (7 - bit_idx)

print("Suffix (hex):", suffix.hex())
message = polite_email + suffix
print("CRC32/CRC64 values:")
for module, name, _ in ALGS:
    print(name, getattr(module, name)(message))
```

Running this script prints the required suffix `433dcdc3cdeec717cc41bea0e2030eaaf2ca2307b3d0145ba694dd08`, which sets all CRC outputs to zero. Submitting the polite mail with this suffix and MAC `0` convinces the author that everything matches.

### Flag

**`openECSC{when_politeness_fails_chinese_remainder_theorem_usually_works_23456789054}`**
