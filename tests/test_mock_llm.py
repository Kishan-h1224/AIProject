
import unittest

from app.agent.mock_llm import MockLLM


class TestMockLLM(unittest.TestCase):

    def setUp(self):
        self.llm = MockLLM()

        self.request = (
            "Calculate 25 multiplied by 4 "
            "and then add 10"
        )

    def test_first_tool_decision(self):

        response = self.llm.decide(
            self.request,
            []
        )

        self.assertEqual(
            response.response_type,
            "tool_call"
        )

        self.assertEqual(
            response.tool_name,
            "multiply"
        )

        self.assertEqual(
            response.arguments,
            {"a": 25, "b": 4}
        )

    def test_second_tool_decision(self):

        observations = [
            {
                "tool_name": "multiply",
                "result": 100
            }
        ]

        response = self.llm.decide(
            self.request,
            observations
        )

        self.assertEqual(
            response.tool_name,
            "add"
        )

        self.assertEqual(
            response.arguments,
            {"a": 100, "b": 10}
        )

    def test_final_decision(self):

        observations = [
            {
                "tool_name": "multiply",
                "result": 100
            },
            {
                "tool_name": "add",
                "result": 110
            }
        ]

        response = self.llm.decide(
            self.request,
            observations
        )

        self.assertEqual(
            response.response_type,
            "final"
        )

        self.assertEqual(
            response.answer,
            "The final answer is 110"
        )

    def test_unsupported_request(self):

        with self.assertRaises(ValueError):

            self.llm.decide(
                "Tell me about Python",
                []
            )


if __name__ == "__main__":
    unittest.main()
