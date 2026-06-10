"""
Thin wrapper around the Ollama Python client.
Enforces JSON-schema-constrained output so all responses match our Pydantic models.
"""
import json
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
import ollama as _ollama
from loguru import logger
from ..config import settings

T = TypeVar("T", bound=BaseModel)


class OllamaClient:
    def __init__(self):
        self._client = _ollama.Client(host=settings.ollama_host)

    def structured(self, prompt: str, schema: Type[T], system: str = "") -> T:
        """
        Call the text model with JSON-schema enforcement.
        Returns a validated instance of `schema`.
        Raises RuntimeError if the model returns unparseable JSON after retries.
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(3):
            try:
                response = self._client.chat(
                    model=settings.llm_text_model,
                    messages=messages,
                    format=schema.model_json_schema(),
                    options={"temperature": 0.1},
                )
                raw = response.message.content
                return schema.model_validate_json(raw)
            except ValidationError as e:
                logger.warning(f"Ollama response validation failed (attempt {attempt+1}): {e}")
                if attempt == 2:
                    raise RuntimeError(f"Ollama structured call failed after 3 attempts: {e}") from e
            except Exception as e:
                logger.error(f"Ollama call error (attempt {attempt+1}): {e}")
                if attempt == 2:
                    raise

        raise RuntimeError("Ollama structured call failed")

    def is_available(self) -> bool:
        try:
            self._client.list()
            return True
        except Exception:
            return False


# Module-level singleton — one connection, reused across the process
_client: OllamaClient | None = None


def get_client() -> OllamaClient:
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
