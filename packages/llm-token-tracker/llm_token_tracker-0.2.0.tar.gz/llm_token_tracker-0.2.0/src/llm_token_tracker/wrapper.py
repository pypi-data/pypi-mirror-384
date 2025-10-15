from typing import Literal
from dataclasses import dataclass, field


@dataclass
class PromptTokens:
    completion_tokens: int = 0
    prompt_tokens: int = 0
    total_tokens: int = 0
    prompt_text_tokens: int = 0
    reasoning_tokens: int = 0
    cached_prompt_text_tokens: int = 0


@dataclass
class PromptTokensDetails:
    text_tokens: int = 0
    audio_tokens: int = 0
    image_tokens: int = 0
    cached_tokens: int = 0


@dataclass
class CompletionTokensDetails:
    reasoning_tokens: int = 0
    audio_tokens: int = 0
    accepted_prediction_tokens: int = 0
    rejected_prediction_tokens: int = 0


@dataclass
class Usage:
    prompt_tokens: PromptTokens = field(default_factory=PromptTokens)
    prompt_tokens_details: PromptTokensDetails = field(default_factory=PromptTokensDetails)
    completion_tokens_details: CompletionTokensDetails = field(default_factory=CompletionTokensDetails)
    num_sources_used: int = 0

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            prompt_tokens=PromptTokens(**data.get("prompt_tokens", {})),
            prompt_tokens_details=PromptTokensDetails(**data.get("prompt_tokens_details", {})),
            completion_tokens_details=CompletionTokensDetails(**data.get("completion_tokens_details", {})),
            num_sources_used=data.get("num_sources_used", 0),
        )

    def __str__(self) -> str:
        return f"""Usage Summary:
  Prompt Tokens: {self.prompt_tokens.prompt_tokens}
  Completion Tokens: {self.prompt_tokens.completion_tokens}
  Total Tokens: {self.prompt_tokens.total_tokens}
  Sources Used: {self.num_sources_used}

Prompt Tokens Breakdown:
  Prompt Text Tokens: {self.prompt_tokens.prompt_text_tokens}
  Reasoning Tokens: {self.prompt_tokens.reasoning_tokens}
  Cached Prompt Text Tokens: {self.prompt_tokens.cached_prompt_text_tokens}

Prompt Tokens Details:
  Text: {self.prompt_tokens_details.text_tokens}
  Audio: {self.prompt_tokens_details.audio_tokens}
  Image: {self.prompt_tokens_details.image_tokens}
  Cached: {self.prompt_tokens_details.cached_tokens}

Completion Tokens Details:
  Reasoning: {self.completion_tokens_details.reasoning_tokens}
  Audio: {self.completion_tokens_details.audio_tokens}
  Accepted Predictions: {self.completion_tokens_details.accepted_prediction_tokens}
  Rejected Predictions: {self.completion_tokens_details.rejected_prediction_tokens}"""


class TokenTracker:
    def __init__(self, llm, verbosity: Literal["minimum", "detailed", "max"] = "minimum"):
        self.llm = llm
        self.verbosity = verbosity
        self.original_sample = llm.sample
        llm.token_history = [Usage]
        llm.sample = self._patched_sample

    def _patched_sample(self, *args, **kwargs):
        response = self.original_sample(*args, **kwargs)
        self.llm.token_history = self.llm.token_history + [Usage(response.usage)]

        match self.verbosity:
            case "minimum":
                print(f"Total tokens used in context: {self.llm.token_history[-1:][0].prompt_tokens.total_tokens}")
            case "detailed":
                print(self.llm.token_history[-1:][0].__str__())

            case "max":
                for history in self.llm.token_history:
                    print(history.__str__())

        return response
