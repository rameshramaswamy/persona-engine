import httpx
import json
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from src.core.config import settings

logger = logging.getLogger("uvicorn")

class InferenceClient:
    _instance = None
    _client: httpx.AsyncClient = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InferenceClient, cls).__new__(cls)
        return cls._instance

    @classmethod
    @asynccontextmanager
    async def lifespan(cls):
        """Manage global HTTP client lifecycle."""
        # OPTIMIZATION: Connection pooling and keep-alive
        cls._client = httpx.AsyncClient(
            base_url=settings.VLLM_ENDPOINT,
            timeout=60.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        yield
        await cls._client.aclose()

    async def stream_chat(self, prompt: str, request_id: str, max_tokens: int = 512) -> AsyncGenerator[str, None]:
        """
        Streams tokens. Supports external cancellation via generator close.
        """
        payload = {
            "model": settings.MODEL_NAME,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "stream": True,
            "temperature": 0.8, # Slightly higher for RP creativity
            "top_p": 0.95,
            "stop": ["<|eot_id|>"],
            # OPTIMIZATION: Tag request for tracing
            "user_id": request_id 
        }

        try:
            # OPTIMIZATION: stream() allows us to disconnect midway if needed
            async with self._client.stream("POST", "/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            # Handle different vLLM response formats
                            token = data.get("text") or data["choices"][0]["text"]
                            yield token
                        except (KeyError, json.JSONDecodeError):
                            continue
        except httpx.ConnectError:
            logger.error("Failed to connect to vLLM engine.")
            yield " [System Error: Engine Offline]"
        except Exception as e:
            logger.error(f"Inference error: {e}")
            yield f" [Error: {str(e)}]"