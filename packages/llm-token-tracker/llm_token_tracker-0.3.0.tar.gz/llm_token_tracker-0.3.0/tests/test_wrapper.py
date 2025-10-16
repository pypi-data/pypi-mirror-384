import unittest
import logging
from unittest.mock import Mock, patch
from llm_token_tracker import wrap_llm


class TestTokenTracker(unittest.TestCase):
    def test_wrap_llm(self):
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Hello world"
        mock_response.usage = {
            "prompt_tokens": {
                "total_tokens": 10,
                "completion_tokens": 5,
                "prompt_tokens": 3,
                "prompt_text_tokens": 3,
                "reasoning_tokens": 0,
                "cached_prompt_text_tokens": 0,
            },
            "prompt_tokens_details": {"text_tokens": 3, "audio_tokens": 0, "image_tokens": 0, "cached_tokens": 0},
            "completion_tokens_details": {
                "reasoning_tokens": 0,
                "audio_tokens": 0,
                "accepted_prediction_tokens": 0,
                "rejected_prediction_tokens": 0,
            },
            "num_sources_used": 1,
        }
        mock_llm.sample.return_value = mock_response
        wrapped = wrap_llm(mock_llm)
        response = wrapped.sample()
        self.assertEqual(response, mock_response)
        self.assertEqual(len(wrapped.token_history), 2)  # initial + one usage
        self.assertEqual(wrapped.token_history[1].prompt_tokens.total_tokens, 10)

    def test_wrap_llm_with_logger(self):
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.usage = {"prompt_tokens": {"total_tokens": 5}}
        mock_llm.sample.return_value = mock_response
        logger = logging.getLogger("test_logger")
        with patch.object(logger, "log") as mock_log:
            wrapped = wrap_llm(mock_llm, logger=logger)
            response = wrapped.sample()
            mock_log.assert_called_with(logging.INFO, "Total tokens used in context: 5")

    def test_wrap_llm_quiet(self):
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.usage = {"prompt_tokens": {"total_tokens": 5}}
        mock_llm.sample.return_value = mock_response
        logger = logging.getLogger("test_logger")
        with patch.object(logger, "log") as mock_log:
            wrapped = wrap_llm(mock_llm, logger=logger, quiet=True)
            response = wrapped.sample()
            mock_log.assert_not_called()

    def test_wrap_llm_detailed_verbosity(self):
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.usage = {
            "prompt_tokens": {
                "total_tokens": 100,
                "completion_tokens": 50,
                "prompt_tokens": 40,
                "prompt_text_tokens": 35,
                "reasoning_tokens": 5,
                "cached_prompt_text_tokens": 10,
            },
            "prompt_tokens_details": {"text_tokens": 35, "audio_tokens": 0, "image_tokens": 0, "cached_tokens": 10},
            "completion_tokens_details": {
                "reasoning_tokens": 5,
                "audio_tokens": 0,
                "accepted_prediction_tokens": 0,
                "rejected_prediction_tokens": 0,
            },
            "num_sources_used": 2,
        }
        mock_llm.sample.return_value = mock_response
        logger = logging.getLogger("test_logger")
        with patch.object(logger, "log") as mock_log:
            wrapped = wrap_llm(mock_llm, logger=logger, verbosity="detailed", max_tokens=1000)
            response = wrapped.sample()
            usage = wrapped.token_history[-1]
            expected = usage.__pretty_str__(1000)
            mock_log.assert_called_with(logging.INFO, expected)


if __name__ == "__main__":
    unittest.main()
