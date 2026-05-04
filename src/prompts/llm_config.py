"""Shared LLM client configuration with retry logic and structured logging.

Uses DeepSeek V4 Pro via OpenAI-compatible API.
"""

from __future__ import annotations

import asyncio
import time
from functools import cache

import structlog
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    qdrant_url: str = "http://localhost:6333"
    database_url: str = "postgresql://user:password@localhost:5432/launchpad"
    max_dialog_turns: int = 3
    confidence_threshold: float = 0.7
    enable_reasoning_stream: bool = True
    llm_model: str = "deepseek-v4-pro"
    llm_timeout: int = 30
    parallel_agent_timeout: int = 60
    corporate_strategy: str = "balanced"


@cache
def get_settings() -> Settings:
    return Settings()


def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not set. Please configure it in your .env file."
        )
    return AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=float(settings.llm_timeout),
    )


async def llm_call(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    max_tokens: int = 4096,
) -> str:
    settings = get_settings()
    model = model or settings.llm_model
    client = _get_client()
    max_retries = 3

    for attempt in range(max_retries):
        start_time = time.monotonic()
        try:
            response = await client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            elapsed = time.monotonic() - start_time
            text = response.choices[0].message.content or ""
            logger.info(
                "llm_call_success",
                model=model,
                attempt=attempt + 1,
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                elapsed_seconds=round(elapsed, 2),
            )
            return text

        except (APITimeoutError, APIConnectionError) as e:
            elapsed = time.monotonic() - start_time
            logger.warning(
                "llm_call_retry",
                model=model,
                attempt=attempt + 1,
                error=str(e),
                elapsed_seconds=round(elapsed, 2),
            )
            if attempt == max_retries - 1:
                raise
            wait = 2**attempt
            await asyncio.sleep(wait)

        except APIStatusError as e:
            logger.error(
                "llm_call_error",
                model=model,
                status_code=e.status_code,
                error=str(e),
            )
            raise

    raise RuntimeError(f"LLM call failed after {max_retries} retries")
