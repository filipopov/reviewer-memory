import argparse
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import mine  # noqa: E402


def raw(id, body, login="alice", type="User", path="src/App.java", created="2026-05-01T00:00:00Z", reply=None, pr=7):
    return {"id": id, "body": body, "user": {"login": login, "type": type}, "path": path, "line": 3,
            "pull_request_url": "https://api.github.com/repos/o/r/pulls/%d" % pr, "html_url": "https://github.com/o/r/pull/%d#c%d" % (pr, id),
            "created_at": created, "diff_hunk": "\n".join("line %d" % i for i in range(20)), "in_reply_to_id": reply}


class FilterTest(unittest.TestCase):
    def test_drops_bots_acknowledgements_and_short_comments(self):
        useful = mine.normalize_github(raw(1, "Please inject the clock instead of calling Instant.now() here."))
        self.assertTrue(mine.is_useful(useful))
        for comment in [raw(2, "LGTM!"), raw(3, "Thanks, done."), raw(4, "nit: typo"),
                        raw(5, "Coverage report: 81% of lines are covered", login="codecov[bot]", type="Bot"),
                        raw(6, "Good catch 👍")]:
            self.assertFalse(mine.is_useful(mine.normalize_github(comment)), comment["body"])

    def test_normalize_keeps_pr_number_and_trims_hunk(self):
        c = mine.normalize_github(raw(1, "x" * 2000, pr=42))
        self.assertEqual(c["pr"], "42")
        self.assertEqual(len(c["body"]), mine.MAX_BODY)
        self.assertEqual(len(c["diff_hunk"].splitlines()), mine.HUNK_LINES)


class FetchTest(unittest.TestCase):
    def args(self, **kw):
        base = dict(repo="o/r", limit=100, since=None, include_replies=False)
        base.update(kw)
        return argparse.Namespace(**base)

    def test_paginates_until_empty_and_skips_replies(self):
        pages = {1: [raw(1, "Use constructor injection, not field injection."),
                     raw(2, "Agreed, but this should still be handled.", reply=1)],
                 2: [raw(3, "Log the payment id, never the full request body.")], 3: []}
        kept, seen = mine.fetch(self.args(), page_source=lambda repo, page: pages[page])
        self.assertEqual([c["id"] for c in kept], ["1", "3"])
        self.assertEqual(seen, 3)

    def test_stops_at_since_because_results_are_newest_first(self):
        pages = {1: [raw(1, "Recent: wrap the client call in a timeout.", created="2026-06-01T00:00:00Z"),
                     raw(2, "Old: something from long ago that we ignore.", created="2024-01-01T00:00:00Z"),
                     raw(3, "Never reached because it is after the cutoff.", created="2023-01-01T00:00:00Z")]}
        kept, _ = mine.fetch(self.args(since="2026-01-01"), page_source=lambda repo, page: pages.get(page, []))
        self.assertEqual([c["id"] for c in kept], ["1"])


class DigestTest(unittest.TestCase):
    def test_groups_tests_separately_and_truncates(self):
        comments = [mine.normalize_github(raw(i, "Comment number %d about the code here" % i,
                                              path="src/test/java/FooTest.java" if i % 2 else "src/main/java/Foo.java"))
                    for i in range(1, 7)]
        text = mine.digest(comments, 100000)
        self.assertIn("## tests (3)", text)
        self.assertIn("## src .java (3)", text)
        self.assertIn("[truncated", mine.digest(comments, 200))


if __name__ == "__main__":
    unittest.main()
