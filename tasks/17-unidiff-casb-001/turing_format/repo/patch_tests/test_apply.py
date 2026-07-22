# -*- coding: utf-8 -*-
"""Behavioural tests for applying a patch set to a working copy.

Run with:  python -m pytest patch_tests/test_apply.py -q
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unidiff import apply_patchset_to_dir


def make_tree(files):
    """Create a temp dir seeded with ``{relpath: content}`` and return its root."""
    root = tempfile.mkdtemp()
    for rel, content in files.items():
        path = os.path.join(root, rel)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w") as fh:
            fh.write(content)
    return root


def read(root, rel):
    with open(os.path.join(root, rel)) as fh:
        return fh.read()


def test_modify_single_hunk():
    """A one-hunk edit whose context matches is applied to the file."""
    root = make_tree({"app.py": "import os\nvalue = 1\nprint(value)\n"})
    patch = (
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1,3 +1,3 @@\n"
        " import os\n"
        "-value = 1\n"
        "+value = 2\n"
        " print(value)\n"
    )
    apply_patchset_to_dir(patch, root)
    assert read(root, "app.py") == "import os\nvalue = 2\nprint(value)\n"


def test_modify_two_hunks_same_file():
    """Two hunks in one file are both applied."""
    original = "".join("line %d\n" % i for i in range(1, 11))
    root = make_tree({"data.txt": original})
    patch = (
        "--- a/data.txt\n"
        "+++ b/data.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " line 1\n"
        "-line 2\n"
        "+line TWO\n"
        " line 3\n"
        "@@ -8,3 +8,3 @@\n"
        " line 8\n"
        "-line 9\n"
        "+line NINE\n"
        " line 10\n"
    )
    apply_patchset_to_dir(patch, root)
    result = read(root, "data.txt")
    assert "line TWO\n" in result
    assert "line NINE\n" in result
    assert "line 2\n" not in result


def test_add_new_file():
    """A patch that introduces a file creates it with the given contents."""
    root = make_tree({"existing.py": "keep = True\n"})
    patch = (
        "--- /dev/null\n"
        "+++ b/new_module.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+def hello():\n"
        "+    return 'hi'\n"
    )
    apply_patchset_to_dir(patch, root)
    assert os.path.exists(os.path.join(root, "new_module.py"))
    assert read(root, "new_module.py") == "def hello():\n    return 'hi'\n"


def test_add_new_file_in_subdir():
    """A new file under a not-yet-existing subdirectory is created."""
    root = make_tree({})
    patch = (
        "--- /dev/null\n"
        "+++ b/pkg/sub/mod.py\n"
        "@@ -0,0 +1,1 @@\n"
        "+X = 1\n"
    )
    apply_patchset_to_dir(patch, root)
    assert read(root, os.path.join("pkg", "sub", "mod.py")) == "X = 1\n"


def test_remove_file():
    """A patch that removes a file deletes it from the working copy."""
    root = make_tree({"old.py": "gone = 1\n", "stays.py": "here = 1\n"})
    patch = (
        "--- a/old.py\n"
        "+++ /dev/null\n"
        "@@ -1,1 +0,0 @@\n"
        "-gone = 1\n"
    )
    apply_patchset_to_dir(patch, root)
    assert not os.path.exists(os.path.join(root, "old.py"))
    assert os.path.exists(os.path.join(root, "stays.py"))


def test_multi_file_patch():
    """A patch touching several files applies to each of them."""
    root = make_tree({
        "a.txt": "alpha\nbeta\ngamma\n",
        "b.txt": "one\ntwo\nthree\n",
    })
    patch = (
        "--- a/a.txt\n"
        "+++ b/a.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " alpha\n"
        "-beta\n"
        "+BETA\n"
        " gamma\n"
        "--- a/b.txt\n"
        "+++ b/b.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " one\n"
        "-two\n"
        "+TWO\n"
        " three\n"
    )
    apply_patchset_to_dir(patch, root)
    assert read(root, "a.txt") == "alpha\nBETA\ngamma\n"
    assert read(root, "b.txt") == "one\nTWO\nthree\n"


def test_report_covers_each_named_file():
    """The returned report has an entry for every file the patch names."""
    root = make_tree({"m.py": "x = 1\n"})
    patch = (
        "--- a/m.py\n"
        "+++ b/m.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-x = 1\n"
        "+x = 2\n"
    )
    report = apply_patchset_to_dir(patch, root)
    assert "m.py" in report
