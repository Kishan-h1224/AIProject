
import re
import sqlite3

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.registry import register_tool


# ---------------------------------
# 1. Database configuration
# ---------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "autoagent.db"

MAX_ROWS = 100
MAX_QUERY_LENGTH = 5000


# ---------------------------------
# 2. SQL argument validation
# ---------------------------------

class SQLExecutorArgs(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    mode: Literal["read", "write"]

    query: str = Field(
        min_length=1,
        max_length=MAX_QUERY_LENGTH
    )

    parameters: dict[
        str,
        str | int | float | bool | None
    ] = Field(default_factory=dict)


# ---------------------------------
# 3. Query validation
# ---------------------------------

def validate_query(query: str, mode: str):
    if mode not in {"read", "write"}:
        raise ValueError("Invalid SQL execution mode")

    # Remove SQL comments before checking the first keyword.
    cleaned = re.sub(
        r"/\*.*?\*/|--[^\r\n]*",
        " ",
        query,
        flags=re.DOTALL
    ).strip()

    match = re.match(r"([A-Za-z]+)", cleaned)

    if not match:
        raise ValueError("Invalid SQL query")

    keyword = match.group(1).upper()

    if mode == "read" and keyword != "SELECT":
        raise PermissionError(
            "Only SELECT queries are allowed in read mode"
        )

    if mode == "write" and keyword not in {
        "INSERT", "UPDATE", "DELETE"
    }:
        raise PermissionError(
            "Only INSERT, UPDATE and DELETE queries "
            "are allowed in write mode"
        )


# ---------------------------------
# 4. SQLite authorizer
# ---------------------------------

def create_authorizer(mode: str):
    # Operations allowed in both modes.
    allowed_actions = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
    }

    # Allow recursive queries if supported by this Python version.
    recursive_action = getattr(sqlite3, "SQLITE_RECURSIVE", None)

    if recursive_action is not None:
        allowed_actions.add(recursive_action)

    # Write mode additionally permits data modifications.
    if mode == "write":
        allowed_actions.update({
            sqlite3.SQLITE_INSERT,
            sqlite3.SQLITE_UPDATE,
            sqlite3.SQLITE_DELETE,
            sqlite3.SQLITE_TRANSACTION,
        })

    def authorize(action, arg1, arg2, database_name, trigger_name):
        if action in allowed_actions:
            return sqlite3.SQLITE_OK

        # Deny everything else, including schema changes,
        # PRAGMA commands, ATTACH and DETACH.
        return sqlite3.SQLITE_DENY

    return authorize


# ---------------------------------
# 5. SQL Executor
# ---------------------------------

@register_tool(
    "sql_executor",
    SQLExecutorArgs,
    requires_approval=lambda args: args["mode"] == "write"
)
def sql_executor(
    mode: Literal["read", "write"],
    query: str,
    parameters: dict | None = None
) -> dict:

    """
    Execute controlled SQL queries using SQLite.
    """

    parameters = parameters or {}

    validate_query(query, mode)

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=5
    )

    connection.row_factory = sqlite3.Row

    try:
        # Read mode is enforced by SQLite itself.
        if mode == "read":
            connection.execute("PRAGMA query_only = ON")

        # Apply SQLite-level permission checks.
        connection.set_authorizer(create_authorizer(mode))

        cursor = connection.cursor()

        # execute() accepts only one SQL statement.
        cursor.execute(query, parameters)

        if mode == "read":
            rows = cursor.fetchmany(MAX_ROWS + 1)

            if len(rows) > MAX_ROWS:
                raise ValueError(
                    f"Query returned more than {MAX_ROWS} rows"
                )

            results = [dict(row) for row in rows]

            return {
                "status": "success",
                "row_count": len(results),
                "results": results
            }

        connection.commit()

        return {
            "status": "success",
            "affected_rows": cursor.rowcount,
            "last_insert_id": cursor.lastrowid
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ---------------------------------
# 6. Initialize demo database
# ---------------------------------

def initialize_demo_database():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(str(DB_PATH)) as connection:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                salary INTEGER NOT NULL
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM employees")

        count = cursor.fetchone()[0]

        if count == 0:
            employees = [
                ("Rahul", "Engineering", 60000),
                ("Amit", "Engineering", 75000),
                ("Priya", "HR", 45000),
                ("Neha", "Finance", 55000),
                ("Ravi", "Engineering", 40000)
            ]

            cursor.executemany("""
                INSERT INTO employees
                (name, department, salary)
                VALUES (?, ?, ?)
            """, employees)

        connection.commit()


# ---------------------------------
# 7. Test SQL Executor
# ---------------------------------

if __name__ == "__main__":

    initialize_demo_database()

    print("\nReading Employees:")

    result = sql_executor(
        mode="read",
        query="""
            SELECT name, salary
            FROM employees
            WHERE salary > :minimum_salary
        """,
        parameters={
            "minimum_salary": 50000
        }
    )

    print(result)

    print("\nInserting Employee:")

    result = sql_executor(
        mode="write",
        query="""
            INSERT INTO employees
            (name, department, salary)
            VALUES (:name, :department, :salary)
        """,
        parameters={
            "name": "Kishan",
            "department": "Engineering",
            "salary": 80000
        }
    )

    print(result)

    print("\nUpdated Employee List:")

    result = sql_executor(
        mode="read",
        query="SELECT * FROM employees"
    )

    print(result)
