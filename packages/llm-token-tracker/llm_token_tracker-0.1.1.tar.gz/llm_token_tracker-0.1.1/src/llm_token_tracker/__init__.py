from .wrapper import TokenTracker

def wrap_llm(llm):
    TokenTracker(llm)
    return llm