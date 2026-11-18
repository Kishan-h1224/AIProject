
import unittest
import tempfile

from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from app.tools.sql_tool import (
    sql_executor,
    SQLExecutorArgs,
    initialize_demo_database,
    validate_query
)


class TestSQLExecutor(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()

        self.db_path = Path(self.temp_dir.name) / "test.db"

        self.patcher = patch(
            "app.tools.sql_tool.DB_PATH",
            self.db_path
        )

        self.patcher.start()

        initialize_demo_database()

    def tearDown(self):

        self.patcher.stop()

        self.temp_dir.cleanup()

    def test_argument_validation(self):

        args = SQLExecutorArgs(
            mode="read",
            query="SELECT * FROM employees"
        )

        self.assertEqual(args.mode, "read")

    def test_invalid_mode(self):

        with self.assertRaises(ValidationError):

            SQLExecutorArgs(
                mode="delete",
                query="DELETE FROM employees"
            )

    def test_read_query(self):

        result = sql_executor(
            mode="read",
            query="SELECT * FROM employees"
        )

        self.assertEqual(result["status"], "success")

        self.assertEqual(result["row_count"], 5)

    def test_parameterized_query(self):

        result = sql_executor(
            mode="read",
            query="""
                SELECT name
                FROM employees
                WHERE salary > :salary
            """,
            parameters={"salary": 50000}
        )

        self.assertEqual(result["row_count"], 3)

    def test_insert_query(self):

        result = sql_executor(
            mode="write",
            query="""
                INSERT INTO employees
                (name, department, salary)
                VALUES (:name, :department, :salary)
            """,
            parameters={
                "name": "Test User",
                "department": "Engineering",
                "salary": 70000
            }
        )

        self.assertEqual(result["affected_rows"], 1)

    def test_write_restriction(self):

        with self.assertRaises(PermissionError):

            validate_query(
                "DROP TABLE employees",
                "write"
            )

    def test_read_restriction(self):

        with self.assertRaises(PermissionError):

            validate_query(
                "DELETE FROM employees",
                "read"
            )

    def test_parameterized_injection_string(self):

        result = sql_executor(
            mode="read",
            query="""
                SELECT * FROM employees
                WHERE name = :name
            """,
            parameters={
                "name": "' OR 1=1 --"
            }
        )

        self.assertEqual(result["row_count"], 0)


if __name__ == "__main__":
    unittest.main()
