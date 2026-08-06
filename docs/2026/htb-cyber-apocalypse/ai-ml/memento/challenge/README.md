# Memento — handout artifacts (defanged)

The parts of the handout you need to reproduce the solve. **Everything here is
inert on purpose:**

- The agent config lives in `claude-config/`, not `.claude/`, and every
  instruction file carries a `.txt` suffix. Nothing in this directory will be
  auto-loaded as project memory or as a skill by any coding agent, including one
  started inside this folder.
- The malicious `shell-helper` skill is included because it is the solution —
  it is the blob the last handout commit deleted, and it carries the campaign
  key. It is here as evidence, not as something to run.

The six HTML leaves and `style.css` are not copied; the only thing they
contribute is one beacon each, and those are extracted verbatim into
`beacons.txt`.

## Contents

| Path | What it is |
|------|------------|
| `claude-config/CLAUDE.md.txt` | The poisoned project memory — carries the "HTML output rule". |
| `claude-config/settings.json` | Permissions the construct ran with (`Write` + `git commit` allowed). |
| `claude-config/skills/shell-helper.SKILL.md.txt` | **Deleted in the handout's last commit.** The rogue skill; `x-campaign` is the XOR key. |
| `claude-config/skills/word-count.SKILL.md.txt` | Deleted alongside it — genuinely unused, cover for the prune. |
| `claude-config/skills/recopy-leaf.SKILL.md.txt` | The benign rite that regenerates a leaf and re-reads the poisoned memory. |
| `claude-config/skills/summarize-url.SKILL.md.txt` | Benign. |
| `claude-config/skills/format-json.SKILL.md.txt` | Benign. |
| `beacons.txt` | The `s=`/`b=` pairs pulled from each of the six leaves. |

## The handout's own notice

From the challenge `README.md`, which is the nudge toward `.git`:

> Seized after the construct began pressing an unexplained mark beneath every
> leaf it copied. Read the residue and find what the mark carries across the
> water.

## Handout git history

```
c9517be housekeeping: prune unused skills           <- deletes shell-helper (+ word-count)
c39fe85 rebuild pages with analytics beacon         <- injects beacons into all 6 leaves
d9448ac chore: add project memory / build conventions <- adds the malicious CLAUDE.md rule
c64506d initial site + tooling
```

Recover the deleted skill with:

```bash
git show c9517be^:.claude/skills/shell-helper/SKILL.md
```
