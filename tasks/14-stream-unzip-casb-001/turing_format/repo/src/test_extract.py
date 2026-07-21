import io
import os
import shutil
import tempfile
import unittest
import zipfile

from stream_unzip_extract import extract_to_dir


def _zip_bytes(entries):
    """Build an in-memory ZIP from a list of (name, content_bytes)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in entries:
            z.writestr(name, content)
    return buf.getvalue()


def _chunks(blob, size=32):
    for i in range(0, len(blob), size):
        yield blob[i : i + size]


class ExtractToDirTests(unittest.TestCase):
    def setUp(self):
        self.dest = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dest, ignore_errors=True)

    def test_single_file_written_with_content(self):
        blob = _zip_bytes([("hello.txt", b"hello world")])
        extract_to_dir(_chunks(blob), self.dest)
        path = os.path.join(self.dest, "hello.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"hello world")

    def test_nested_directories_recreated(self):
        blob = _zip_bytes(
            [
                ("a/b/c/deep.txt", b"deep"),
                ("a/top.txt", b"top"),
            ]
        )
        extract_to_dir(_chunks(blob), self.dest)
        deep = os.path.join(self.dest, "a", "b", "c", "deep.txt")
        top = os.path.join(self.dest, "a", "top.txt")
        self.assertTrue(os.path.isfile(deep))
        self.assertTrue(os.path.isfile(top))
        with open(deep, "rb") as f:
            self.assertEqual(f.read(), b"deep")

    def test_multiple_files_all_written(self):
        entries = [(f"dir/file_{i}.bin", bytes([i]) * (i + 1)) for i in range(5)]
        blob = _zip_bytes(entries)
        extract_to_dir(_chunks(blob), self.dest)
        for name, content in entries:
            path = os.path.join(self.dest, *name.split("/"))
            self.assertTrue(os.path.isfile(path), name)
            with open(path, "rb") as f:
                self.assertEqual(f.read(), content)

    def test_returns_written_paths(self):
        blob = _zip_bytes([("one.txt", b"1"), ("sub/two.txt", b"2")])
        written = extract_to_dir(_chunks(blob), self.dest)
        self.assertEqual(len(written), 2)
        for p in written:
            self.assertTrue(os.path.isfile(p))

    def test_dest_dir_created_if_missing(self):
        target = os.path.join(self.dest, "does", "not", "exist", "yet")
        blob = _zip_bytes([("f.txt", b"x")])
        extract_to_dir(_chunks(blob), target)
        self.assertTrue(os.path.isfile(os.path.join(target, "f.txt")))

    def test_larger_content_streamed(self):
        payload = os.urandom(200000)
        blob = _zip_bytes([("big.bin", payload)])
        extract_to_dir(_chunks(blob, size=64), self.dest)
        with open(os.path.join(self.dest, "big.bin"), "rb") as f:
            self.assertEqual(f.read(), payload)


if __name__ == "__main__":
    unittest.main()
