#!/usr/bin/env python3
"""Collects pull-request review comments worth learning from.

  mine.py fetch --repo owner/name [--limit 1500] [--since 2025-01-01] [--include-replies]
  mine.py import <file.jsonl>          # comments from another source (Bitbucket, GitLab export...)
  mine.py digest [--max-chars 60000]   # compact, grouped text for the model to read

Comments are stored in .reviewer-memory/comments.jsonl in the current git repository. Bots, trivial
remarks ("LGTM", "done", "+1") and very short comments are dropped. Python 3.9+, stdlib only; fetch
uses the GitHub CLI (`gh`) and whatever account it is logged in with.
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

STORE_DIR = ".reviewer-memory"
STORE = os.path.join(STORE_DIR, "comments.jsonl")
MIN_LENGTH = 20
MAX_BODY = 1500
HUNK_LINES = 8
TRIVIAL = re.compile(
    r"^\s*(lgtm|looks good( to me)?|thanks?( you)?|thx|done|fixed|addressed|ok(ay)?|nice|\+1|ack|agreed|same here|"
    r"good (catch|point)|will do|resolved)[\s.!:)👍🙏]*$",
    re.IGNORECASE,
)


def is_useful(comment):
    """True for comments that carry a review opinion, not a bot or an acknowledgement."""
    author = comment.get("author") or ""
    body = (comment.get("body") or "").strip()
    if comment.get("author_is_bot") or author.endswith("[bot]") or author.endswith("-bot"):
        return False
    if len(body) < MIN_LENGTH or TRIVIAL.match(body):
        return False
    return True


def normalize_github(raw):
    pr_url = raw.get("pull_request_url") or ""
    hunk = (raw.get("diff_hunk") or "").splitlines()
    user = raw.get("user") or {}
    return {
        "id": str(raw.get("id")),
        "pr": pr_url.rsplit("/", 1)[-1] if pr_url else None,
        "author": user.get("login"),
        "author_is_bot": user.get("type") == "Bot",
        "path": raw.get("path"),
        "line": raw.get("line") or raw.get("original_line"),
        "body": (raw.get("body") or "").strip()[:MAX_BODY],
        "diff_hunk": "\n".join(hunk[-HUNK_LINES:]),
        "url": raw.get("html_url"),
        "created_at": raw.get("created_at"),
        "reply": raw.get("in_reply_to_id") is not None,
    }


def gh_page(repo, page):
    out = subprocess.run(
        ["gh", "api", "repos/%s/pulls/comments?per_page=100&page=%d&sort=created&direction=desc" % (repo, page)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit("gh api failed: " + out.stderr.strip())
    return json.loads(out.stdout)


def fetch(args, page_source=gh_page):
    kept, seen = [], 0
    page = 1
    while seen < args.limit:
        batch = page_source(args.repo, page)
        if not batch:
            break
        for raw in batch:
            seen += 1
            comment = normalize_github(raw)
            if args.since and (comment["created_at"] or "") < args.since:
                seen = args.limit  # results are newest first: everything after this is older
                break
            if comment["reply"] and not args.include_replies:
                continue
            if is_useful(comment):
                kept.append(comment)
        page += 1
    return kept, seen


def save(comments):
    os.makedirs(STORE_DIR, exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as f:
        for c in comments:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


def load():
    if not os.path.exists(STORE):
        sys.exit("No %s yet. Run `mine.py fetch --repo owner/name` (or `import`) first." % STORE)
    with open(STORE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def area(path):
    """Groups files by what they are, so the digest puts related comments together."""
    if not path:
        return "(general)"
    parts = path.split("/")
    if any(p in ("test", "tests", "__tests__", "spec") for p in parts) or re.search(r"(Test|_test|\.test|\.spec)\.", path):
        return "tests"
    ext = os.path.splitext(path)[1] or parts[-1]
    top = parts[0] if len(parts) > 1 else "(root)"
    return "%s %s" % (top, ext)


def digest(comments, max_chars):
    groups = collections.defaultdict(list)
    for c in comments:
        groups[area(c.get("path"))].append(c)
    lines = ["%d review comments from %d PRs by %d reviewers." % (
        len(comments), len({c.get("pr") for c in comments}), len({c.get("author") for c in comments}))]
    for name, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        lines.append("\n## %s (%d)" % (name, len(items)))
        for c in items:
            body = re.sub(r"\s+", " ", c["body"])[:400]
            lines.append("- [%s] PR %s %s:%s @%s: %s" % (c["id"], c.get("pr"), c.get("path"), c.get("line"), c.get("author"), body))
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[truncated: %d more characters; raise --max-chars or read the JSONL]" % (len(text) - max_chars)
    return text


def stats(comments, seen):
    authors = collections.Counter(c.get("author") for c in comments).most_common(5)
    areas = collections.Counter(area(c.get("path")) for c in comments).most_common(5)
    return "kept %d of %d comments from %d PRs\n  top reviewers: %s\n  top areas: %s" % (
        len(comments), seen, len({c.get("pr") for c in comments}),
        ", ".join("%s (%d)" % a for a in authors), ", ".join("%s (%d)" % a for a in areas))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--repo", required=True, help="owner/name on GitHub")
    f.add_argument("--limit", type=int, default=1500, help="max comments to scan (newest first)")
    f.add_argument("--since", help="ISO date; ignore older comments")
    f.add_argument("--include-replies", action="store_true")
    i = sub.add_parser("import")
    i.add_argument("file", help="JSONL with at least: id, author, path, body (optional: pr, line, url, diff_hunk)")
    d = sub.add_parser("digest")
    d.add_argument("--max-chars", type=int, default=60000)
    args = parser.parse_args(argv)

    if args.command == "fetch":
        comments, seen = fetch(args)
        save(comments)
        print(stats(comments, seen), file=sys.stderr)
        print(STORE)
    elif args.command == "import":
        with open(args.file, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        comments = [r for r in rows if is_useful(r)]
        save(comments)
        print(stats(comments, len(rows)), file=sys.stderr)
        print(STORE)
    else:
        print(digest(load(), args.max_chars))


if __name__ == "__main__":
    main()
