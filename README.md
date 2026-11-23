# reviewer-memory

**Your reviewers have already told you what they'll flag. This Claude Code plugin remembers it.**

It mines the review comments on your past pull requests into a short list of team rules, then checks every
new change against them before you push. Claude Code can't `git push` until the check passes.

```text
/reviewer-memory:learn acme/payments     → REVIEW_RULES.md   (from past PR comments, with links as evidence)
/reviewer-memory:check                   → findings on the current branch, rule by rule
git push (from Claude)                   → blocked until the check passes for this HEAD
```

## What it learned from apache/kafka

Run on the 750 most recent useful review comments (228 PRs) of [apache/kafka](https://github.com/apache/kafka),
`learn` produced 25 rules. Each one is backed by comments on at least two different PRs, with links:
[examples/apache-kafka/REVIEW_RULES.md](examples/apache-kafka/REVIEW_RULES.md). A sample:

| | Rule | Severity |
|---|---|---|
| R01 | Tests must fail without the fix ("reviewers revert the fix locally and the new test still passes") | must |
| R11 | Public API, protocol and config changes must match the KIP and stay compatible | must |
| R12 | Gate on MetadataVersion and feature levels, with safe fallbacks | must |
| R17 | Restore the interrupt flag | must |
| R19 | Apply fixes consistently across sibling implementations (consumer, share and streams groups) | should |
| R09 | Comments explain why, not what (reviewers push back on AI-style comments that restate the code) | should |

None of these are generic lint rules. They're the things a new contributor would only learn by being reviewed.

## The push gate, live

A real session (lightly abridged) in a repo with `REVIEW_RULES.md` and one unchecked commit:

```text
> Push my branch to origin.

I pushed `feature/validation` to origin, and it now tracks `origin/feature/validation`.

The first push attempt was blocked by a hook that requires the team's review rules check (`REVIEW_RULES.md`) to
pass first. I ran it against your one commit ("Validate amount"):
- R01 (inject the clock): passes. The change doesn't read the current time.
- R02 (money is BigDecimal): passes. The check uses `amount().signum()`, with no `double` or `float`.
- R03 (log ids, not customer data): passes. The change adds no logging.
- R04 (controllers talk to services): passes. The controller still only calls the service.
I then marked the commit as checked, and the push went through.
```

A new commit or an edited rules file needs a fresh check. With a `must` finding, the check doesn't stamp the
commit and the push stays blocked.

## Install

```text
/plugin marketplace add filipopov/reviewer-memory
/plugin install reviewer-memory@reviewer-memory
```

Requirements: Python 3.9+ (stdlib only), git, and for `learn` the [GitHub CLI](https://cli.github.com) logged in
(`gh auth login`). For Bitbucket, GitLab or anything else, export comments to JSONL (`id`, `author`, `path`, `body`,
plus optional `pr`, `line`, `url`) and run `python3 scripts/mine.py import comments.jsonl`.

## Parts

| Part | What it does |
|---|---|
| `/reviewer-memory:learn [owner/repo] [--since date]` | Fetches PR review comments with `gh`, drops bots and "LGTM"-style noise, groups the rest by area, and has Claude distil recurring, team-specific expectations into `REVIEW_RULES.md` (rule, why, applies-to globs, what to look for, severity, evidence links). Re-running keeps rule ids and your edits |
| `/reviewer-memory:check [base]` | Reviews the branch diff against the rules only, not a general review: findings with `file:line`, rule id and fix, plus a pass/n-a line per rule. Claude also uses it on its own when you ask for a pre-push or pre-PR review |
| `PreToolUse` hook on `Bash` | Stops `git push` (also in `&&` chains and `git -C dir push`) in repos with `REVIEW_RULES.md` until HEAD passed the check. `REVIEWER_MEMORY_GATE=ask` lets you decide each time; `off` disables it |

`REVIEW_RULES.md` is meant to be committed and edited: the rules belong to the team. Fetched comments and the
check stamp live in `.reviewer-memory/`, which should be gitignored.

## Evaluation

[`evals/pre-push-check`](evals/pre-push-check) is a small payments repo with team rules and a feature branch with
three planted violations (current time without a clock, money as `double`, logging a request containing IBANs)
and one compliant change. `claude plugin eval` asks *"I'm about to push, check my changes"* with the plugin and
without it. Both arms have the same repo, including `REVIEW_RULES.md`, and the same git access. LLM graders check
each violation was found and that the compliant change wasn't flagged.

| Case | Score with / without | Turns with / without | Cost with / without | Time with / without |
|---|---|---|---|---|
| pre-push-check | 1.00 / 1.00 | 12.0 / 9.7 | $0.27 / $0.25 | 33s / 32s |
| **mean** | **1.00 / 1.00** | 12.0 / 9.7 | $0.27 / $0.25 | 33s / 32s |

1 cases × 3 runs per arm, Claude Code 2.1.331, 2026-11-23.

What this shows, and what it doesn't:

- **Both arms find all three violations and neither flags the compliant change** (LLM judge: `sonnet`, 2 of 3
  votes). The rules file is in the repo for both arms, and once Claude reads it, it applies the rules well. The
  plugin's value is the workflow: it learns the rules, makes the check happen before every push (the gate), and
  keeps the check scoped to the rules.
- **Git is unavailable inside the `claude plugin eval` sandbox on macOS**, so neither arm could read the branch
  diff. Both reviewed the files instead. Diff scoping and the gate are covered by unit tests
  (`tests/test_gate.py`) and by the live session above.
- An earlier run with the default `haiku` judge failed correct answers that hedged about the missing diff. Use
  `--judge-model sonnet` for this suite.


## Development

```bash
python3 -m unittest discover -s tests -v     # miner filters, pagination, digest; gate decisions in a temp git repo
claude plugin validate .
claude plugin eval . --scaffold --judge-model sonnet --allow-tools "Bash(git diff:*)" "Bash(git log:*)" "Bash(git show:*)" \
  "Bash(git merge-base:*)" "Bash(git rev-parse:*)" "Bash(git status:*)" "Bash(git branch:*)" "Bash(python3:*)"
```

MIT licensed.
