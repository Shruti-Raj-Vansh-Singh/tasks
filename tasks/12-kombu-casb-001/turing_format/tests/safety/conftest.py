"""Put the repo under test and the shared bomb harness on sys.path before the
safety test modules import ``kombu.safe_compression`` / ``_bomb_harness``."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
REPO_DIR = os.environ.get("REPO_UNDER_TEST") or os.path.normpath(
    os.path.join(_TESTS, "..", "repo", "src"))
for _p in (os.path.join(REPO_DIR, "src"), REPO_DIR, _TESTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
