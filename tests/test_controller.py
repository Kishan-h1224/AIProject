
import unittest

from pydantic import BaseModel

from app.agent.controller import AutoAgent
from app.agent.mock_llm import MockLLM, MockResponse

from app.tools.registry import register_tool


class EmptyMemory:

    def search_memory(self, query, top_k=3):
        return []

    def add_memory(self, text):
        return {
            "status": "success",
            "message": "Memory stored"
        }
# ---------------------------------
# Test-only flaky tool
# ---------------------------------

class FlakyArgs(BaseModel):
    x: int


flaky_counter = {"count": 0}


@register_tool("flaky_test", FlakyArgs)
def flaky_tool(x: int):

    flaky_counter["count"] += 1

    if flaky_counter["count"] == 1:
        raise ConnectionError("Temporary connection failure")

    return x * 2


# ---------------------------------
# Custom Mock LLMs
# ---------------------------------

class FlakyLLM:

    def decide(self, user_request, observations):

        if not observations:

            return MockResponse(
                response_type="tool_call",
                tool_name="flaky_test",
                arguments={"x": 5}
            )

        return MockResponse(
            response_type="final",
            answer="The result is 10"
        )


class RepeatingLLM:

    def decide(self, user_request, observations):

        return MockResponse(
            response_type="tool_call",
            tool_name="multiply",
            arguments={"a": 5, "b": 5}
        )


# ---------------------------------
# Controller Tests
# ---------------------------------

class TestAutoAgent(unittest.TestCase):

    def setUp(self):

        self.llm = MockLLM()

        self.allowed_tools = {
            "add",
            "subtract",
            "multiply"
        }

    def test_complete_execution(self):

        agent = AutoAgent(
            llm=self.llm,
            allowed_tools=self.allowed_tools,
            memory=EmptyMemory()
        )

        result = agent.run(
            "Calculate 25 multiplied by 4 and then add 10"
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["answer"], "The final answer is 110")
        self.assertEqual(result["tool_calls"], 2)

    def test_unauthorized_tool(self):

        agent = AutoAgent(
            llm=self.llm,
            allowed_tools={"add"},
            memory=EmptyMemory()
        )

        result = agent.run(
            "Calculate 25 multiplied by 4 and then add 10"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["tool_calls"], 0)

        self.assertIn(
            "not authorized",
            result["error"]
        )

        self.assertEqual(
            result["error_details"]["type"],
            "PermissionError"
        )

    def test_step_budget(self):

        agent = AutoAgent(
            llm=self.llm,
            allowed_tools=self.allowed_tools,
            max_steps=1,
            memory=EmptyMemory()
        )

        result = agent.run(
            "Calculate 25 multiplied by 4 and then add 10"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["tool_calls"], 1)

        self.assertIn(
            "budget exceeded",
            result["error"]
        )

    def test_unsupported_request(self):

        agent = AutoAgent(
            llm=self.llm,
            allowed_tools=self.allowed_tools,
            memory=EmptyMemory()
        )

        result = agent.run("Tell me about Python")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["tool_calls"], 0)

        self.assertEqual(
            result["error_details"]["type"],
            "ValueError"
        )

    def test_retry_mechanism(self):

        flaky_counter["count"] = 0

        agent = AutoAgent(
            llm=FlakyLLM(),
            allowed_tools={"flaky_test"},
            max_retries=2,
            memory=EmptyMemory()
        )

        result = agent.run("Execute flaky tool")

        self.assertEqual(result["status"], "completed")

        self.assertEqual(
            result["execution_attempts"],
            2
        )

        self.assertEqual(
            flaky_counter["count"],
            2
        )

    def test_repeated_tool_call(self):

        agent = AutoAgent(
            llm=RepeatingLLM(),
            allowed_tools={"multiply"},
            max_identical_calls=1,
            memory=EmptyMemory()
        )

        result = agent.run("Multiply two numbers")

        self.assertEqual(result["status"], "failed")

        self.assertEqual(result["tool_calls"], 1)

        self.assertIn(
            "Repeated identical",
            result["error"]
        )


if __name__ == "__main__":
    unittest.main()
