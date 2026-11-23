import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import gate  # noqa: E402

GATE = os.path.join(os.path.dirname(__file__), "..", "scripts", "gate.py")


def sh(cwd, *cmd):
    subprocess.run(list(cmd), cwd=cwd, check=True, capture_output=True)


class GateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.realpath(self.tmp.name)
        sh(self.repo, "git", "init", "-q")
        sh(self.repo, "git", "config", "user.email", "t@example.com")
        sh(self.repo, "git", "config", "user.name", "t")
        with open(os.path.join(self.repo, gate.RULES), "w") as f:
            f.write("# Review rules\n## R01 · Inject the clock\n")
        sh(self.repo, "git", "add", ".")
        sh(self.repo, "git", "commit", "-qm", "init")

    def tearDown(self):
        self.tmp.cleanup()

    def event(self, command):
        return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": self.repo}

    def stamp(self):
        subprocess.run([sys.executable, GATE, "stamp"], cwd=self.repo, check=True, capture_output=True)

    def test_blocks_unchecked_push_and_allows_other_commands(self):
        out = gate.hook(self.event("git push origin HEAD"), "block")
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("/reviewer-memory:check", out["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertIsNone(gate.hook(self.event("git status && git log -1"), "block"))
        self.assertIsNone(gate.hook(self.event("echo git pushed"), "block"))

    def test_detects_push_in_compound_and_dash_c_commands(self):
        self.assertIsNotNone(gate.hook(self.event("npm test && git push"), "block"))
        other = {"tool_name": "Bash", "tool_input": {"command": "git -C %s push" % self.repo}, "cwd": "/"}
        self.assertIsNotNone(gate.hook(other, "block"))

    def test_stamp_allows_push_until_new_commit_or_rule_change(self):
        self.stamp()
        self.assertIsNone(gate.hook(self.event("git push"), "block"))
        with open(os.path.join(self.repo, "a.txt"), "w") as f:
            f.write("x")
        sh(self.repo, "git", "add", ".")
        sh(self.repo, "git", "commit", "-qm", "change")
        self.assertIsNotNone(gate.hook(self.event("git push"), "block"))
        self.stamp()
        with open(os.path.join(self.repo, gate.RULES), "a") as f:
            f.write("## R02 · New rule\n")
        self.assertIsNotNone(gate.hook(self.event("git push"), "block"))

    def test_modes_and_repos_without_rules(self):
        self.assertEqual(gate.hook(self.event("git push"), "ask")["hookSpecificOutput"]["permissionDecision"], "ask")
        self.assertIsNone(gate.hook(self.event("git push"), "off"))
        os.remove(os.path.join(self.repo, gate.RULES))
        self.assertIsNone(gate.hook(self.event("git push"), "block"))

    def test_hook_entry_point_prints_json(self):
        out = subprocess.run([sys.executable, GATE], input=json.dumps(self.event("git push")),
                             capture_output=True, text=True, cwd=self.repo)
        self.assertEqual(json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        empty = subprocess.run([sys.executable, GATE], input="not json", capture_output=True, text=True)
        self.assertEqual(empty.stdout, "")


if __name__ == "__main__":
    unittest.main()


class DiffTest(unittest.TestCase):
    def test_prints_commits_and_diff_against_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            for cmd in (["git", "init", "-q", "-b", "main"], ["git", "config", "user.email", "t@example.com"],
                        ["git", "config", "user.name", "t"]):
                sh(tmp, *cmd)
            open(os.path.join(tmp, "a.txt"), "w").write("one\n")
            sh(tmp, "git", "add", ".")
            sh(tmp, "git", "commit", "-qm", "base")
            sh(tmp, "git", "checkout", "-qb", "feature")
            open(os.path.join(tmp, "a.txt"), "w").write("two\n")
            sh(tmp, "git", "commit", "-qam", "change it")
            open(os.path.join(tmp, "b.txt"), "w").write("draft\n")
            sh(tmp, "git", "add", "b.txt")
            diff = os.path.join(os.path.dirname(__file__), "..", "scripts", "diff.py")
            out = subprocess.run([sys.executable, diff], cwd=tmp, capture_output=True, text=True).stdout
            self.assertIn("# Base: main", out)
            self.assertIn("change it", out)
            self.assertIn("+two", out)
            self.assertIn("+draft", out)
