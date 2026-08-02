from functools import lru_cache

from hindsight.config import settings
from hindsight.llm.base import LLMProvider


@lru_cache(maxsize=1)
def get_llm() -> LLMProvider:
    if settings.llm_provider == "gemini":
        from hindsight.llm.gemini_provider import GeminiProvider

        return GeminiProvider()
    if settings.llm_provider == "anthropic":
        from hindsight.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if settings.llm_provider == "bedrock":
        from hindsight.llm.bedrock_provider import BedrockClaudeProvider

        return BedrockClaudeProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")
