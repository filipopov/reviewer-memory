"""Finds a git that runs. On macOS /usr/bin/git is an xcrun shim that can fail in restricted environments
(it writes a cache in TMPDIR); the real binary may be in the Command Line Tools or Homebrew. Override with
REVIEWER_MEMORY_GIT. Strict sandboxes can block every git binary; the check skill then falls back to reading files."""
import functools
import os
import shutil
import subprocess

CANDIDATES = (
    "/Library/Developer/CommandLineTools/usr/bin/git",
    "/opt/homebrew/bin/git",
    "/usr/local/bin/git",
)


@functools.lru_cache(maxsize=1)
def git_binary():
    preferred = [os.environ.get("REVIEWER_MEMORY_GIT"), shutil.which("git")]
    for candidate in [c for c in preferred if c] + list(CANDIDATES):
        if not os.path.exists(candidate):
            continue
        try:
            if subprocess.run([candidate, "--version"], capture_output=True, timeout=10).returncode == 0:
                return candidate
        except (OSError, subprocess.TimeoutExpired):
            continue  # try the next candidate
    return "git"
