import unittest
from unittest.mock import Mock
from llm_token_tracker import wrap_llm

class TestTokenTracker(unittest.TestCase):
    def test_wrap_llm(self):
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Hello world"
        mock_response.usage.total_tokens = 10
        mock_llm.sample.return_value = mock_response
        wrapped = wrap_llm(mock_llm)
        response = wrapped.sample("Hi")
        self.assertEqual(response, mock_response)
        self.assertEqual(wrapped.total_tokens, 10)

if __name__ == '__main__':
    unittest.main()