from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, cast

import instructor
from instructor import Instructor
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from pydantic import BaseModel


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    model: str
    api_key_env_var: str | None = None

    client_kwargs: dict[str, Any] = field(default_factory=dict)
    request_defaults: dict[str, Any] = field(default_factory=dict)

    @cached_property
    def client(self) -> OpenAI:
        """OpenAI client (or compatible) for this config."""
        api_key = os.getenv(self.api_key_env_var, "") if self.api_key_env_var else ""
        return OpenAI(base_url=self.base_url, api_key=api_key, **self.client_kwargs)

    @classmethod
    def openrouter(cls, model: str) -> LLMConfig:
        """OpenRouter config with cost saving and app defaults."""
        return cls(
            model=model,
            base_url="https://openrouter.ai/api/v1",
            api_key_env_var="OPENROUTER_API_KEY",
            request_defaults={
                "extra_headers": {
                    "HTTP-Referer": "https://github.com/MaxWolf-01/omni-x",
                    "X-Title": "omni-x",
                },
                "extra_body": {
                    "usage": {"include": True},
                    "provider": {"data_collection": "allow"},  # 1% savings + models become better over time
                },
            },
        )

    @classmethod
    def vllm(cls, model: str) -> LLMConfig:
        """Local vLLM config."""
        return cls(
            model=model,
            base_url=os.getenv("VLLM_API_BASE_URL", "http://localhost:8000/v1"),
            api_key_env_var="VLLM_API_KEY",
        )


class InstructorClient:
    @dataclass(frozen=True)
    class Config:
        llm: LLMConfig
        mode: instructor.Mode  # https://python.useinstructor.com/modes-comparison/

    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = instructor.from_openai(self.config.llm.client, mode=self.config.mode)

    def create_with_completion[T: BaseModel](
        self,
        response_model: type[T],
        messages: list[ChatCompletionMessageParam],
        **kwargs: Any,
    ) -> tuple[T, ChatCompletion]:
        """Get structured output from LLM along with the full raw response.

        Args:
            response_model: Pydantic model defining the expected output structure
            messages: Chat messages following OpenAI format
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Tuple of (validated instance of response_model, full raw ChatCompletion response)
        """
        return self._client.chat.completions.create_with_completion(
            model=self.config.llm.model,
            response_model=response_model,
            messages=messages,
            **{**self.config.llm.request_defaults, **kwargs},
        )
