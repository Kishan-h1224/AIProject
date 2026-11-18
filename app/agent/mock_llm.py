
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MockResponse(BaseModel):

    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    response_type: Literal["tool_call", "final"]

    tool_name: str | None = None

    arguments: dict[str, Any] = Field(default_factory=dict)

    answer: str | None = None


class MockLLM:

    def __init__(self):
        pass

    # ---------------------------------
    # 1. Parse Arithmetic Requests
    # ---------------------------------

    def parse_request(self, user_request: str):

        patterns = [
            r"(-?\d+)\s+multiplied\s+by\s+(-?\d+)",
            r"multiply\s+(-?\d+)\s+by\s+(-?\d+)"
        ]

        match = None

        for pattern in patterns:
            match = re.search(
                pattern,
                user_request,
                re.IGNORECASE
            )

            if match:
                break

        if not match:
            raise ValueError(
                "MockLLM does not support this request"
            )

        a, b = map(int, match.groups())

        # Addition is optional.
        add_match = re.search(
            r"(?:and\s+then\s+)?add\s+(-?\d+)",
            user_request,
            re.IGNORECASE
        )

        c = int(add_match.group(1)) if add_match else None

        return a, b, c

    # ---------------------------------
    # 2. Handle Conversations
    # ---------------------------------

    def handle_conversation(
        self,
        user_request: str,
        observations: list
    ):

        name_match = re.search(
            r"\bmy name is\s+([A-Za-z][A-Za-z '-]*)",
            user_request,
            re.IGNORECASE
        )

        if name_match:

            name = name_match.group(1).strip()

            return MockResponse(
                response_type="final",
                answer=f"Nice to meet you, {name}."
            )

        asks_name = re.search(
            r"\b(what is|what's|tell me)\b.*\bmy name\b",
            user_request,
            re.IGNORECASE
        )

        if asks_name:

            history = [
                item for item in observations
                if item.get("type") == "conversation"
            ]

            for item in reversed(history):

                if item.get("role") != "user":
                    continue

                previous_match = re.search(
                    r"\bmy name is\s+([A-Za-z][A-Za-z '-]*)",
                    item.get("message", ""),
                    re.IGNORECASE
                )

                if previous_match:

                    name = previous_match.group(1).strip()

                    return MockResponse(
                        response_type="final",
                        answer=f"Your name is {name}."
                    )

            return MockResponse(
                response_type="final",
                answer="You haven't told me your name yet."
            )

        return None

    # ---------------------------------
    # 3. Main Decision Logic
    # ---------------------------------

    def decide(self, user_request: str, observations: list):

        # Handle conversational requests first.
        conversation_response = self.handle_conversation(
            user_request,
            observations
        )

        if conversation_response is not None:
            return conversation_response

        # Recognize Python execution requests.
        python_match = re.search(
            r"execute python code to print\s+(.+)",
            user_request,
            re.IGNORECASE
        )

        if python_match:

            message = python_match.group(1).strip().strip("'\"")

            code = f"print({message!r})"

            return MockResponse(
                response_type="tool_call",
                tool_name="python_executor",
                arguments={
                    "code": code,
                    "timeout_seconds": 5
                }
            )

        # Parse arithmetic request.
        a, b, c = self.parse_request(user_request)

        # Find previous tool results.
        tool_results = [
            item for item in observations
            if item.get("kind") == "tool_result"
            or (
                "tool_name" in item
                and "result" in item
            )
        ]

        # First operation: multiplication.
        if len(tool_results) == 0:

            return MockResponse(
                response_type="tool_call",
                tool_name="multiply",
                arguments={
                    "a": a,
                    "b": b
                }
            )

        previous_result = tool_results[-1]["result"]

        # If addition was not requested, return multiplication result.
        if c is None:

            return MockResponse(
                response_type="final",
                answer=f"The final answer is {previous_result}"
            )

        # Second operation: addition.
        if len(tool_results) == 1:

            return MockResponse(
                response_type="tool_call",
                tool_name="add",
                arguments={
                    "a": previous_result,
                    "b": c
                }
            )

        # Both operations completed.
        if len(tool_results) == 2:

            final_result = tool_results[-1]["result"]

            return MockResponse(
                response_type="final",
                answer=f"The final answer is {final_result}"
            )

        raise ValueError(
            "Unexpected number of tool results"
        )
