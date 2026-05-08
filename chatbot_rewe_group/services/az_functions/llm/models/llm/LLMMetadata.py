
from typing import TypedDict

class LLMMetadata(TypedDict):
    """
    Tracks token usage statistics for LLM interactions.
    
    Attributes:
        prompt_tokens (int): Number of tokens in the prompt.
        completion_tokens (int): Number of tokens in the completion/output.
        total_tokens (int): Total number of tokens used (prompt + completion).
    """
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
