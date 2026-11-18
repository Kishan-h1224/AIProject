
import unittest

from pydantic import ValidationError

from app.tools.python_executor import (
    python_executor,
    PythonExecutorArgs
)


class TestPythonExecutor(unittest.TestCase):

    def test_argument_validation(self):

        args = PythonExecutorArgs(
            code="print(10)",
            timeout_seconds=5
        )

        self.assertEqual(args.timeout_seconds, 5)

    def test_invalid_timeout(self):

        with self.assertRaises(ValidationError):

            PythonExecutorArgs(
                code="print(10)",
                timeout_seconds=100
            )

    def test_empty_code(self):

        with self.assertRaises(ValidationError):

            PythonExecutorArgs(
                code="",
                timeout_seconds=5
            )

    def test_successful_execution(self):

        result = python_executor(
            code="print('Hello AutoAgent')",
            timeout_seconds=5
        )

        self.assertEqual(result["status"], "success")

        self.assertEqual(
            result["stdout"],
            "Hello AutoAgent"
        )

        self.assertEqual(result["return_code"], 0)

    def test_execution_error(self):

        result = python_executor(
            code="invalid_code",
            timeout_seconds=5
        )

        self.assertEqual(result["status"], "error")

        self.assertNotEqual(result["return_code"], 0)

        self.assertIn(
            "NameError",
            result["stderr"]
        )

    def test_execution_timeout(self):

        with self.assertRaises(TimeoutError):

            python_executor(
                code="while True: pass",
                timeout_seconds=1
            )


if __name__ == "__main__":
    unittest.main()
