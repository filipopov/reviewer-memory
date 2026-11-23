---
name: check
description: Check the current branch's changes against the team's learned review rules (REVIEW_RULES.md) before pushing or opening a PR. Use when the user asks to pre-review, self-review or check a change before push or PR, or when a push was blocked by reviewer-memory.
argument-hint: "[base branch]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/diff.py:*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate.py:*), Read, Grep, Glob
---

# Check changes against the team's review rules

1. **Rules.** Read `REVIEW_RULES.md`. If it doesn't exist, stop and suggest `/reviewer-memory:learn`.
2. **Diff.** Run this one command on its own (don't chain it with other commands):

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/diff.py" $ARGUMENTS
   ```

   It prints the commits on top of the base (`origin/HEAD`, `main` or `master`, or the argument), the committed diff
   and any uncommitted changes. Review exactly that.
3. **Check rule by rule.** For each rule whose *Applies to* matches a changed file, look at the changed lines (read
   the surrounding code when a rule needs context). Only report a finding when you can point to a line in this diff.
   Don't do a general code review here, and don't invent rules.
4. **Report**, most severe first:

   | Rule | Severity | Where | Finding | Suggested fix |
   |---|---|---|---|---|
   | R03 · … | must | `path/File.java:42` | … | … |

   Then one line per rule that passed or didn't apply, e.g. `R01 ✓  R02 n/a  R04 ✓`.
5. **Gate.** If there are no `must` findings, record the pass so `git push` is allowed:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" stamp
   ```

   If there are `must` findings, don't stamp. Offer to fix them, and run the check again afterwards.
