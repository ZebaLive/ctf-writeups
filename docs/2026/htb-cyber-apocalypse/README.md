---
title: "HTB Cyber Apocalypse 2026 CTF - Writeups"
description: "Writeups from Hack The Box Cyber Apocalypse 2026: secure-coding trust boundaries, GamePwn, ML/tokenizer tricks, and LLM prompt-injection challenges. Team finished 341st with 40,500 points."
---

# HTB Cyber Apocalypse 2026

My writeups from **Hack The Box Cyber Apocalypse 2026**.

<div class="ctf-stats">
  <div class="ctf-stat"><span class="num">341st</span><span class="label">Team Rank</span></div>
  <div class="ctf-stat"><span class="num">40,500</span><span class="label">Team Points</span></div>
  <div class="ctf-stat"><span class="num">78/136</span><span class="label">Flags</span></div>
</div>

## Challenges

### GamePwn

- **[The Salt Crown](gamepwn/the-salt-crown/writeup.md)** (Hard) — A Godot game whose progression lives in a native GDExtension. Cheating the boss's HP fails against a signed event transcript, so the solve fabricates the transcript in live memory from the parent process and lets the game render its own AES-GCM encrypted flag.
