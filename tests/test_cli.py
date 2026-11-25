import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from ml_split_audit import main


class SplitAuditTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        for name, content in {"first.txt": b"same", "second.txt": b"same", "third.txt": b"different"}.items():
            (self.root / name).write_bytes(content)

    def run_audit(self, csv):
        path = self.root / "files.csv"
        path.write_text(csv, encoding="utf-8")
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = main([str(path)])
            except SystemExit as error:
                code = error.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_flags_duplicates_and_groups_across_splits_without_names(self):
        code, output, error = self.run_audit("path,split,group_id\nfirst.txt,train,sensitive-group\nsecond.txt,test,other\nthird.txt,validation,sensitive-group\n")
        self.assertEqual(code, 1, error)
        self.assertNotIn("sensitive-group", output)
        self.assertNotIn("first.txt", output)
        self.assertEqual(json.loads(output)["findings"], [
            {"reason": "identical_bytes", "records": [{"line": 2, "split": "train"}, {"line": 3, "split": "test"}]},
            {"reason": "group_overlap", "records": [{"line": 2, "split": "train"}, {"line": 4, "split": "validation"}]},
        ])

    def test_duplicate_bytes_within_one_split_are_allowed(self):
        code, output, error = self.run_audit("path,split\nfirst.txt,train\nsecond.txt,train\nthird.txt,test\n")
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)["findings"], [])

    def test_invalid_manifest_and_paths_fail(self):
        for bad in ("missing.txt,train", "../first.txt,train", "first.txt,dev", "first.txt", "first.txt,train\nfirst.txt,train"):
            self.assertEqual(self.run_audit("path,split\n" + bad + "\n")[0], 2)

    def test_refuses_symlink_outside_manifest_directory(self):
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "external.txt"
            external.write_text("other", encoding="utf-8")
            (self.root / "link.txt").symlink_to(external)
            self.assertEqual(self.run_audit("path,split\nlink.txt,train\n")[0], 2)
