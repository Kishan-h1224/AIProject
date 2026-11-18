
import unittest

from unittest.mock import patch, Mock

from pydantic import ValidationError

from app.tools.web_search import (
    web_search,
    WebSearchArgs
)


class TestWebSearch(unittest.TestCase):

    def test_argument_validation(self):

        args = WebSearchArgs(
            query="Python tutorials",
            max_results=5
        )

        self.assertEqual(
            args.query,
            "Python tutorials"
        )

    def test_invalid_max_results(self):

        with self.assertRaises(ValidationError):

            WebSearchArgs(
                query="Python",
                max_results=50
            )

    def test_empty_query(self):

        with self.assertRaises(ValidationError):

            WebSearchArgs(
                query="",
                max_results=5
            )

    @patch("app.tools.web_search.DDGS")
    def test_search_execution(self, mock_ddgs):

        # Mock provider response
        mock_client = Mock()

        mock_client.text.return_value = [

            {
                "title": "Python Official Documentation",
                "href": "https://docs.python.org/",
                "body": "Official Python documentation"
            }

        ]

        mock_ddgs.return_value = mock_client

        # Execute our tool
        result = web_search(
            query="Python documentation",
            max_results=5
        )

        # Verify output
        self.assertEqual(result["count"], 1)

        self.assertEqual(
            result["results"][0]["title"],
            "Python Official Documentation"
        )

        self.assertEqual(
            result["results"][0]["url"],
            "https://docs.python.org/"
        )

        # Verify provider was called
        mock_client.text.assert_called_once()


if __name__ == "__main__":
    unittest.main()
