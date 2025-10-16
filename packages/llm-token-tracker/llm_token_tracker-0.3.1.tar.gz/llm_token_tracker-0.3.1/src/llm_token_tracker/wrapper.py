import logging
from typing import Literal, Optional
from dataclasses import dataclass, field
from xai_sdk.proto import usage_pb2


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
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            prompt_tokens=PromptTokens(**data.get("prompt_tokens", {})),
            prompt_tokens_details=PromptTokensDetails(**data.get("prompt_tokens_details", {})),
            completion_tokens_details=CompletionTokensDetails(**data.get("completion_tokens_details", {})),
            num_sources_used=data.get("num_sources_used", 0),
            input_cost=data.get("input_cost", 0.0),
            output_cost=data.get("output_cost", 0.0),
            total_cost=data.get("total_cost", 0.0),
        )

    @classmethod
    def from_sampling_usage(cls, sampling_usage: usage_pb2.SamplingUsage):
        return cls(
            prompt_tokens=PromptTokens(
                completion_tokens=sampling_usage.completion_tokens,
                prompt_tokens=sampling_usage.prompt_tokens,
                total_tokens=sampling_usage.total_tokens,
                prompt_text_tokens=sampling_usage.prompt_text_tokens,
                reasoning_tokens=sampling_usage.reasoning_tokens,
                cached_prompt_text_tokens=sampling_usage.cached_prompt_text_tokens,
            ),
            prompt_tokens_details=PromptTokensDetails(
                text_tokens=sampling_usage.prompt_text_tokens,
                cached_tokens=sampling_usage.cached_prompt_text_tokens,
                image_tokens=sampling_usage.prompt_image_tokens,
            ),
            completion_tokens_details=CompletionTokensDetails(
                reasoning_tokens=sampling_usage.reasoning_tokens,
            ),
            num_sources_used=sampling_usage.num_sources_used,
        )

    def __str__(self) -> str:
        cost_str = ""
        if self.input_cost or self.output_cost or self.total_cost:
            cost_str = f"""

Cost Summary:
   Input Cost: ${self.input_cost:.10f}
   Output Cost: ${self.output_cost:.10f}
   Total Cost: ${self.total_cost:.10f}"""

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
   Rejected Predictions: {self.completion_tokens_details.rejected_prediction_tokens}{cost_str}"""

    def __pretty_str__(self, max_tokens: int) -> str:
        unfilled_square = "･"
        half_filled_square = "￭"
        filled_square = "◼"

        percent = (self.prompt_tokens.total_tokens / max_tokens) * 100
        squares = "".join(
            filled_square if percent >= (i + 1) * 10 else half_filled_square if percent >= i * 10 else unfilled_square for i in range(10)
        )

        total_used = f"Total Tokens used:\n {squares} ({percent:.2f}%) {self.prompt_tokens.total_tokens}/{max_tokens}"

        details = [
            f"Prompt Tokens: {self.prompt_tokens.prompt_tokens}",
            f"Completion Tokens: {self.prompt_tokens.completion_tokens}",
            f"Sources Used: {self.num_sources_used}",
        ]
        if self.prompt_tokens.cached_prompt_text_tokens:
            details.append(f"Cached Tokens: {self.prompt_tokens.cached_prompt_text_tokens}")

        cost_str = ""
        if self.input_cost or self.output_cost or self.total_cost:
            cost_str = f"Total Cost: ${self.total_cost:.10f}".rstrip("0")

        base = [total_used]
        if cost_str:
            base.append(cost_str)
        lines = base + details

        return "\n".join(lines)


class TokenTracker:
    def __init__(
        self,
        llm,
        max_tokens: int = 132000,
        input_pricing: float = 0.2,
        output_pricing: float = 0.5,
        calculate_pricing: bool = False,
        verbosity: Literal["minimum", "detailed", "max"] = "minimum",
        logger: Optional[logging.Logger] = None,
        log_level: int = logging.INFO,
        quiet: bool = False,
    ):
        self.llm = llm
        self.max_tokens = max_tokens
        self.input_pricing = input_pricing
        self.output_pricing = output_pricing
        self.calculate_pricing = calculate_pricing
        self.verbosity = verbosity
        self.logger = logger
        self.log_level = log_level
        self.quiet = quiet

        self.original_sample = llm.sample
        llm.token_history = [Usage()]
        llm.sample = self._patched_sample

    def _calculate_cost(self, usage: Usage) -> Usage:
        if self.calculate_pricing:
            input_tokens = usage.prompt_tokens.prompt_tokens
            output_tokens = usage.prompt_tokens.completion_tokens
            usage.input_cost = input_tokens / 1000000 * self.input_pricing
            usage.output_cost = output_tokens / 1000000 * self.output_pricing
            usage.total_cost = usage.input_cost + usage.output_cost
        return usage

    def _patched_sample(self, *args, **kwargs):
        response = self.original_sample(*args, **kwargs)

        if isinstance(response.usage, dict):
            usage = Usage.from_dict(response.usage)
        else:
            usage = Usage.from_sampling_usage(response.usage)
        usage = self._calculate_cost(usage)
        self.llm.token_history = self.llm.token_history + [usage]

        if not self.quiet:
            match self.verbosity:
                case "minimum":
                    message = f"Total tokens used in context: {self.llm.token_history[-1:][0].prompt_tokens.total_tokens}"
                    self._log(logging.INFO, message)
                case "detailed":
                    message = self.llm.token_history[-1:][0].__pretty_str__(self.max_tokens)
                    self._log(logging.INFO, message)
                case "max":
                    message = self.llm.token_history[-1:][0].__str__()
                    self._log(logging.DEBUG, message)

        return response

    def _log(self, level: int, message: str):
        if self.logger:
            self.logger.log(level, message)
        else:
            print(message)
