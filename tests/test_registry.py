
import unittest

from pydantic import ValidationError

# Importing this module registers our tools
from app.tools import basic_tools

from app.tools.registry import execute_tool


class TestToolRegistry(unittest.TestCase):

    def setUp(self):
        self.allowed_tools = {
            "add",
            "subtract",
            "multiply"
        }

    def test_valid_execution(self):

        result = execute_tool(
            "add",
            {"a": 10, "b": 20},
            allowed_tools=self.allowed_tools
        )

        self.assertEqual(result, 30)

    def test_invalid_type(self):

        with self.assertRaises(ValidationError):

            execute_tool(
                "add",
                {"a": "hello", "b": 20},
                allowed_tools=self.allowed_tools
            )

    def test_extra_argument(self):

        with self.assertRaises(ValidationError):

            execute_tool(
                "add",
                {"a": 10, "b": 20, "c": 30},
                allowed_tools=self.allowed_tools
            )

    def test_missing_argument(self):

        with self.assertRaises(ValidationError):

            execute_tool(
                "add",
                {"a": 10},
                allowed_tools=self.allowed_tools
            )

    def test_unauthorized_tool(self):

        with self.assertRaises(PermissionError):

            execute_tool(
                "multiply",
                {"a": 5, "b": 5},
                allowed_tools={"add"}
            )

    def test_unknown_tool(self):

        with self.assertRaises(ValueError):

            execute_tool(
                "unknown_tool",
                {},
                allowed_tools={"unknown_tool"}
            )


if __name__ == "__main__":
    unittest.main()
