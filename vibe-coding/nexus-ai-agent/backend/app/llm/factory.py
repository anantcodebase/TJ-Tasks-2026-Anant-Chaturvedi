from app.config import settings
from app.llm.base import LLMClient
from app.llm.gemini import GeminiClient
from app.llm.ollama import OllamaClient
from app.llm.nvidia import NvidiaClient


def create_llm_client() -> LLMClient:
    provider = settings.ai_provider.lower()
    if provider == "gemini":
        return GeminiClient()
    if provider == "ollama":
        return OllamaClient()
    if provider == "nvidia":
        return NvidiaClient()
    raise ValueError(f"Unsupported AI_PROVIDER: {settings.ai_provider}")
