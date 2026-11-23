#!/usr/bin/env python3
"""Prints what /reviewer-memory:check should review, as one command (easy to allow, no shell chaining).

  diff.py [base]

Base: the argument, else origin/HEAD, else main, else master. Prints the commits on top of the base, the
committed diff (merge-base...HEAD) and any uncommitted changes. Without a usable base, falls back to the
last commit plus uncommitted changes.
"""
import subprocess
import sys

from gitbin import git_binary


def git(*args):
    out = subprocess.run([git_binary()] + list(args), capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def pick_base(requested):
    candidates = [requested] if requested else ["origin/HEAD", "main", "master"]
    for ref in candidates:
        if ref and git("rev-parse", "--verify", "--quiet", ref + "^{commit}"):
            merge_base = (git("merge-base", "HEAD", ref) or "").strip()
            head = (git("rev-parse", "HEAD") or "").strip()
            if merge_base and merge_base != head:
                return ref, merge_base
    return None, None


def main(argv):
    if git("rev-parse", "--git-dir") is None:
        sys.exit("Not a git repository.")
    ref, merge_base = pick_base(argv[0] if argv else None)
    if ref:
        print("# Base: %s (merge-base %s)\n" % (ref, merge_base[:10]))
        print("# Commits\n" + (git("log", "--oneline", "%s..HEAD" % merge_base) or ""))
        print("# Committed changes\n" + (git("diff", "--unified=5", "%s...HEAD" % ref) or ""))
    else:
        print("# No base branch with new commits found; reviewing the last commit.\n")
        print(git("show", "--unified=5", "--format=# Commit %h %s%n", "HEAD") or "(no commits)")
    uncommitted = git("diff", "--unified=5", "HEAD") or ""
    print("# Uncommitted changes\n" + (uncommitted if uncommitted.strip() else "(none)\n"))


if __name__ == "__main__":
    main(sys.argv[1:])
