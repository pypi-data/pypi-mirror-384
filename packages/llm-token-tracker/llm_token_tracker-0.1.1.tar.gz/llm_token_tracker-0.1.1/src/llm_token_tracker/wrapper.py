class TokenTracker:
    def __init__(self, llm):
        self.llm = llm
        self.original_sample = llm.sample
        llm.total_tokens = 0
        llm.sample = self._patched_sample

    def _patched_sample(self, *args, **kwargs):
        response = self.original_sample(*args, **kwargs)
        self.llm.total_tokens += response.usage.total_tokens
        print(f"Total tokens used in context: {self.llm.total_tokens}")
        return response
