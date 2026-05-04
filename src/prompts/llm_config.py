"""Shared LLM client configuration with retry logic and structured logging.

Supports per-agent LLM configuration via AGENT_LLM_CONFIG_<AGENT> JSON env vars.
Each agent can use a different model provider (DeepSeek, OpenAI, Anthropic, etc.)
via OpenAI-compatible API. Falls back to global DEEPSEEK_* defaults.

Per-agent config format:
  AGENT_LLM_CONFIG_INTAKE={"api_key":"sk-xxx","base_url":"https://api.openai.com","model":"gpt-4o"}
  AGENT_LLM_CONFIG_SYNTHESIS={"model":"claude-sonnet-4-20250514"}

All fields per agent are optional. Missing fields fall back to global defaults.
Unconfigured agents use global defaults entirely.
"""

from __future__ import annotations

import asyncio
import json as json_module
import time
from functools import lru_cache
from typing import Any

import structlog
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)

_AGENT_NAMES = ("intake", "dispatch", "feasibility", "resource", "risk", "synthesis", "review")


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

    # Per-agent LLM config (JSON strings, optional)
    agent_llm_config_intake: str = ""
    agent_llm_config_dispatch: str = ""
    agent_llm_config_feasibility: str = ""
    agent_llm_config_resource: str = ""
    agent_llm_config_risk: str = ""
    agent_llm_config_synthesis: str = ""
    agent_llm_config_review: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def _parse_agent_json(raw: str) -> dict[str, str]:
    """Parse a single agent's JSON config string. Returns {} on empty or invalid."""
    raw = raw.strip()
    if not raw:
        return {}
    try:
        data = json_module.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json_module.JSONDecodeError, TypeError):
        logger.warning("agent_llm_config_parse_failed", raw=raw[:100])
        return {}


def _get_agent_llm_params(agent_name: str) -> dict[str, str]:
    settings = get_settings()

    field_map: dict[str, str] = {
        "intake": settings.agent_llm_config_intake,
        "dispatch": settings.agent_llm_config_dispatch,
        "feasibility": settings.agent_llm_config_feasibility,
        "resource": settings.agent_llm_config_resource,
        "risk": settings.agent_llm_config_risk,
        "synthesis": settings.agent_llm_config_synthesis,
        "review": settings.agent_llm_config_review,
    }

    agent_config = _parse_agent_json(field_map.get(agent_name, ""))

    api_key = agent_config.get("api_key") or settings.deepseek_api_key
    if not api_key:
        raise RuntimeError(
            f"DEEPSEEK_API_KEY is not set, and no api_key configured for agent '{agent_name}'. "
            "Please configure it in your .env file."
        )

    return {
        "api_key": api_key,
        "base_url": agent_config.get("base_url") or settings.deepseek_base_url,
        "model": agent_config.get("model") or settings.llm_model,
        "timeout": float(settings.llm_timeout),
    }


@lru_cache(maxsize=8)
def _get_agent_client(agent_name: str) -> AsyncOpenAI:
    params = _get_agent_llm_params(agent_name)
    return AsyncOpenAI(
        api_key=params["api_key"],
        base_url=params["base_url"],
        timeout=params["timeout"],
    )


async def llm_call(
    system_prompt: str,
    user_message: str,
    agent_name: str = "intake",
    model: str | None = None,
    max_tokens: int = 4096,
) -> str:
    params = _get_agent_llm_params(agent_name)
    model = model or params["model"]
    client = _get_agent_client(agent_name)
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
                agent=agent_name,
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
                agent=agent_name,
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
                agent=agent_name,
                model=model,
                status_code=e.status_code,
                error=str(e),
            )
            raise

    raise RuntimeError(f"LLM call failed after {max_retries} retries")
