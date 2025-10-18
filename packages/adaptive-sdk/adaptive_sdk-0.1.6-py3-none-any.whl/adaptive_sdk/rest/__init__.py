"""
This file serves the purpose of automatic SDK docs generation.
All output rest types are included in __all__ so they are exported to the reference docs.
"""
from .rest_types import AddInteractionsResponse, ChatChoice, ChatChoiceMessage, ChatResponse, ChatResponseChunk, ComparisonOutput, Delta, EmbeddingResponse, EmbeddingsResponseList, FeedbackOutput, GenerateChoice, Usage
__all__ = ['AddInteractionsResponse', 'ChatResponse', 'ChatChoice', 'ChatChoiceMessage', 'ChatResponseChunk', 'ComparisonOutput', 'Delta', 'EmbeddingResponse', 'EmbeddingsResponseList', 'FeedbackOutput', 'GenerateChoice', 'Usage']