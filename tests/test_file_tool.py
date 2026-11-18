
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from app.tools.file_tool import (
    file_io,
    FileToolArgs,
    get_safe_path
)


class TestFileTool(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()

        self.patcher = patch(
            "app.tools.file_tool.DATA_DIR",
            Path(self.temp_dir.name)
        )

        self.patcher.start()

    def tearDown(self):

        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_argument_validation(self):

        args = FileToolArgs(
            operation="read",
            filename="notes.txt"
        )

        self.assertEqual(args.operation, "read")

    def test_invalid_operation(self):

        with self.assertRaises(ValidationError):

            FileToolArgs(
                operation="delete",
                filename="notes.txt"
            )

    def test_write_file(self):

        result = file_io(
            operation="write",
            filename="notes.txt",
            content="Hello AutoAgent"
        )

        self.assertEqual(result["status"], "success")

    def test_read_file(self):

        file_io(
            operation="write",
            filename="notes.txt",
            content="Hello AutoAgent"
        )

        result = file_io(
            operation="read",
            filename="notes.txt"
        )

        self.assertEqual(
            result["content"],
            "Hello AutoAgent"
        )

    def test_append_file(self):

        file_io(
            operation="write",
            filename="notes.txt",
            content="Hello"
        )

        file_io(
            operation="append",
            filename="notes.txt",
            content=" World"
        )

        result = file_io(
            operation="read",
            filename="notes.txt"
        )

        self.assertEqual(
            result["content"],
            "Hello World"
        )

    def test_path_traversal(self):

        with self.assertRaises(PermissionError):

            get_safe_path("../../secret.txt")

    def test_absolute_path(self):

        with self.assertRaises(PermissionError):

            get_safe_path("C:/Windows/test.txt")

    def test_invalid_extension(self):

        with self.assertRaises(PermissionError):

            get_safe_path("program.exe")

    def test_missing_file(self):

        with self.assertRaises(FileNotFoundError):

            file_io(
                operation="read",
                filename="missing.txt"
            )

    def test_append_missing_file(self):

        with self.assertRaises(FileNotFoundError):

            file_io(
                operation="append",
                filename="missing.txt",
                content="Hello"
            )


if __name__ == "__main__":
    unittest.main()
