---
name: learn
description: Learn a team's code-review rules from the review comments on its past pull requests, and save them to REVIEW_RULES.md so future changes can be checked against them before review.
argument-hint: "[owner/repo] [--since YYYY-MM-DD]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mine.py:*), Bash(gh repo view:*), Read, Write, Edit
---

# Learn review rules from past PRs

Arguments: `$ARGUMENTS`

## 1. Collect the comments

Use the repository from the arguments, or else the current one (`gh repo view --json nameWithOwner -q .nameWithOwner`).

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mine.py" fetch --repo <owner/repo> [--since <date>]
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mine.py" digest
```

The digest groups useful comments by area (bots and "LGTM"-style remarks are already dropped). For a non-GitHub
source, the user can export comments to JSONL and run `mine.py import <file>` instead.

## 2. Turn comments into rules

Read the whole digest. A rule is a **recurring, team-specific expectation**:

- Raise a rule only when **at least 2 comments on different PRs** express it. A single comment is an anecdote.
- Prefer what's specific to this codebase (naming, layering, error handling, test style, logging, API compatibility,
  framework conventions) over generic advice a linter or any reviewer would give.
- Merge near-duplicates. Aim for 8–25 rules. Fewer, sharper rules are better.
- If `REVIEW_RULES.md` already exists, keep the existing rule ids and edits the user made. Add, update or
  retire rules; don't renumber.

## 3. Write `REVIEW_RULES.md`

Use exactly this structure, because `/reviewer-memory:check` parses it:

```markdown
# Review rules

Learned from <N> review comments on <M> PRs in <owner/repo> (<date range>) by reviewer-memory.
Edit freely: these are the team's rules now, not the tool's.

## R01 · <short title>
- **Rule:** <imperative, checkable statement>
- **Why:** <the reason reviewers gave>
- **Applies to:** <globs, e.g. `src/main/**/*.java`, or `*`>
- **Look for:** <what in a diff indicates a violation>
- **Severity:** must | should
- **Evidence:** <count> comments, e.g. [#123](url), [#140](url)
```

Use `must` only for things reviewers consistently blocked on: correctness, compatibility, security, layering.

## 4. Finish

- Make sure `.reviewer-memory/` is in `.gitignore`. The rules file itself is meant to be committed.
- Reply with the rules as a table (id, title, severity, evidence count) and the 3 most frequent themes. Remind the
  user that `git push` from Claude Code is now gated on `/reviewer-memory:check` (set `REVIEWER_MEMORY_GATE=ask` or
  `off` to soften it).
