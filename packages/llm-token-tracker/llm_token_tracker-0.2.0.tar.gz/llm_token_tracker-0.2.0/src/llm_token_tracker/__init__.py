from .wrapper import TokenTracker
from typing import Literal


def wrap_llm(llm, verbosity: Literal["minimum", "detailed", "max"] = "minimum"):
    TokenTracker(llm, verbosity)
    return llm
