
# from pydantic import BaseModel, Field, ValidationError
from pydantic import BaseModel, Field, ConfigDict

from app.tools.registry import (
    register_tool,
    execute_tool,
    list_tools,
    get_tool_schemas
)


# Argument schemas

class StrictArgs(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )


class AddArgs(StrictArgs):
    a: int = Field(description="First number")
    b: int = Field(description="Second number")


class SubtractArgs(StrictArgs):
    a: int
    b: int


class MultiplyArgs(StrictArgs):
    a: int
    b: int


# Register tools

@register_tool("add", AddArgs)
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@register_tool("subtract", SubtractArgs)
def subtract(a: int, b: int) -> int:
    """Subtract two numbers."""
    return a - b


@register_tool("multiply", MultiplyArgs)
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


if __name__ == "__main__":

    allowed_tools = {
        "add",
        "subtract",
        "multiply"
    }

    print("Registered Tools:")
    print(list_tools())

    print("\nExecuting Tools:")

    print(
        "Addition:",
        execute_tool(
            "add",
            {"a": 10, "b": 20},
            allowed_tools=allowed_tools
        )
    )

    print(
        "Subtraction:",
        execute_tool(
            "subtract",
            {"a": 20, "b": 10},
            allowed_tools=allowed_tools
        )
    )

    print(
        "Multiplication:",
        execute_tool(
            "multiply",
            {"a": 5, "b": 4},
            allowed_tools=allowed_tools
        )
    )
