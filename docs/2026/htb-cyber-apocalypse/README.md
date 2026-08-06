---
title: "Cyber Apocalypse CTF 2026: The Salt Crown - Writeups"
description: "Writeups from Cyber Apocalypse CTF 2026: The Salt Crown, Hack The Box's flagship annual event. GamePwn, secure-coding trust boundaries, ML/tokenizer tricks, and LLM prompt-injection challenges. Team finished 341st with 40,500 points."
---

# Cyber Apocalypse CTF 2026: The Salt Crown

My writeups from **Cyber Apocalypse CTF 2026: The Salt Crown**, Hack The Box's flagship annual event.

## About

Cyber Apocalypse is one of the largest jeopardy CTFs of the year. The 2026 edition is set in the realm of Valyssar after the sovereign artifact that made royal decrees absolute shatters into fragments — recasting the succession war as one of "infrastructure, logic, and counterfeit governance." The endgame is the Salt Crown itself: a fault-tolerant constraint system built to leash authority rather than grant it, which is a fair description of the challenges too — most of them are about breaking a validation rule rather than a lock.

**Event Details:**

- **Duration:** July 24–29, 2026
- **Format:** Jeopardy-style, online, open to the public
- **Team size:** Up to 30 players
- **Scale:** 74 scenarios across 16 categories, with 12,695 players in 6,743 teams
- **Website:** [https://ctf.hackthebox.com/event/details/cyber-apocalypse-ctf-2026-the-salt-crown-3432](https://ctf.hackthebox.com/event/details/cyber-apocalypse-ctf-2026-the-salt-crown-3432)

## Challenges Solved

### AI - ML

- **[The Obligation Indexer](ai-ml/obligation-indexer/writeup.md)** (Easy) — An LLM chat that guards "read only your own account" in its system prompt but trusts its own persistent dossier. Direct requests and authority spoofing all bounce; the solve poisons the dossier with a fake "joint-registry statute" so a benign self-lookup leaks another petitioner's sealed debts — indirect prompt injection via conversational memory.

### GamePwn

- **[The Salt Crown](gamepwn/the-salt-crown/writeup.md)** (Hard) — A Godot game whose progression lives in a native GDExtension. Cheating the boss's HP fails against a signed event transcript, so the solve fabricates the transcript in live memory from the parent process and lets the game render its own AES-GCM encrypted flag.

## Competition Stats

- **Event**: Cyber Apocalypse CTF 2026: The Salt Crown
- **Challenges Solved**: 78/136 (team)
- **Points**: 40500 (team)
- **Rank**: 341st place (team)
