import logging
from .wrapper import TokenTracker
from typing import Literal, Optional


def wrap_llm(
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
    """
    Wrap an LLM to track token usage.

    Args:
        llm: The LLM object to wrap.
        max_tokens: The maximum amount of tokens the llm can use.
        input_pricing: The price for 1mil input tokens.
        output_pricing: The price for 1mil output tokens.
        calculate_pricing: If the price should be estimated / calculated.
        verbosity: Level of logging verbosity.
            - "minimum": Log only total tokens.
            - "detailed": Log detailed usage summary.
            - "max": Log full history of all usages.
        logger: Optional logger to use instead of print. If None, uses print.
        log_level: Logging level (e.g., logging.INFO).
        quiet: If True, disable all logging.

    Returns:
        The wrapped LLM.
    """
    TokenTracker(llm, max_tokens, input_pricing, output_pricing, calculate_pricing, verbosity, logger, log_level, quiet)
    return llm
