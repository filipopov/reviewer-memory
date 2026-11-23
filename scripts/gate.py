#!/usr/bin/env python3
"""Pre-push gate for Claude Code.

As a PreToolUse hook (stdin = hook JSON): when Claude runs `git push` in a repository that has review
rules, and the current HEAD hasn't passed /reviewer-memory:check, the push is stopped with a reason
that tells Claude to run the check first.

  gate.py            hook mode (reads the hook event from stdin)
  gate.py stamp      record that HEAD passed the check (called by the check skill)
  gate.py status     print whether HEAD is checked

REVIEWER_MEMORY_GATE=block (default) | ask (let the user decide) | off.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

from gitbin import git_binary

RULES = "REVIEW_RULES.md"
STAMP = os.path.join(".reviewer-memory", "checked")
PUSH = re.compile(r"(^|[;&|]\s*|\s)git(\s+-C\s+\S+)?\s+push\b")


def git(cwd, *args):
    out = subprocess.run([git_binary(), "-C", cwd] + list(args), capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def fingerprint(root):
    """HEAD plus the rules: new commits or edited rules both need a fresh check."""
    head = git(root, "rev-parse", "HEAD")
    with open(os.path.join(root, RULES), "rb") as f:
        rules = hashlib.sha256(f.read()).hexdigest()[:12]
    return "%s %s" % (head, rules)


def is_checked(root):
    try:
        with open(os.path.join(root, STAMP), encoding="utf-8") as f:
            return f.read().strip() == fingerprint(root)
    except OSError:
        return False


def repo_root(cwd):
    root = git(cwd, "rev-parse", "--show-toplevel")
    return root if root and os.path.exists(os.path.join(root, RULES)) else None


def target_dir(command, cwd):
    match = re.search(r"git\s+-C\s+(\S+)\s+push", command)
    if match:
        return os.path.join(cwd, os.path.expanduser(match.group(1).strip("'\"")))
    match = re.match(r"\s*cd\s+(\S+)\s*&&", command)
    return os.path.join(cwd, os.path.expanduser(match.group(1).strip("'\""))) if match else cwd


def hook(event, mode):
    """Returns the hook's JSON output, or None to allow the command."""
    if mode == "off" or event.get("tool_name") != "Bash":
        return None
    command = (event.get("tool_input") or {}).get("command") or ""
    if not PUSH.search(command):
        return None
    root = repo_root(target_dir(command, event.get("cwd") or os.getcwd()))
    if not root or is_checked(root):
        return None
    reason = ("reviewer-memory: this repository has team review rules (%s) and HEAD has not passed them yet. "
              "Run /reviewer-memory:check, fix the 'must' findings, then push again." % RULES)
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask" if mode == "ask" else "deny",
        "permissionDecisionReason": reason,
    }}


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "hook"
    if command in ("stamp", "status"):
        root = repo_root(os.getcwd())
        if not root:
            sys.exit("No %s in this repository." % RULES)
        if command == "stamp":
            os.makedirs(os.path.join(root, ".reviewer-memory"), exist_ok=True)
            with open(os.path.join(root, STAMP), "w", encoding="utf-8") as f:
                f.write(fingerprint(root) + "\n")
            print("HEAD %s marked as checked" % fingerprint(root).split()[0][:10])
        else:
            print("checked" if is_checked(root) else "not checked")
        return
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return  # Not a hook invocation we understand: never block on our own parse error.
    output = hook(event, os.environ.get("REVIEWER_MEMORY_GATE", "block").lower())
    if output:
        print(json.dumps(output))


if __name__ == "__main__":
    main()
