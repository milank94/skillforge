"""LLM client abstraction for Anthropic and OpenAI APIs.

This module provides a unified interface for interacting with different LLM providers,
with built-in retry logic, error handling, and rate limiting.
"""

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from anthropic import Anthropic, APIError, APITimeoutError, RateLimitError
from openai import (
    APIError as OpenAIAPIError,
)
from openai import (
    OpenAI,
)
from openai import (
    RateLimitError as OpenAIRateLimitError,
)

from skillforge.models.config import LLMConfig
from skillforge.models.enums import LLMProvider


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients.

    Provides a unified interface for different LLM providers with common
    functionality like retry logic and error handling.
    """

    def __init__(self, config: LLMConfig):
        """Initialize the LLM client.

        Args:
            config: LLM configuration including provider, model, and temperature
        """
        self.config = config
        self.max_retries = 3
        self.base_delay = 1.0

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2048,
    ) -> str:
        """Generate completion from prompt.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt to set context
            temperature: Optional temperature override (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If API call fails after retries
        """
        pass

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Generate structured JSON response.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt to set context
            schema: Optional JSON schema to enforce structure

        Returns:
            Parsed JSON response as dictionary

        Raises:
            ValueError: If parameters are invalid or JSON is malformed
            RuntimeError: If API call fails after retries
        """
        pass

    def _make_request_with_retry(
        self, request_func: Callable[[], Any], operation: str = "API request"
    ) -> Any:
        """Execute request with exponential backoff retry logic.

        Args:
            request_func: Function that makes the API request
            operation: Description of the operation for error messages

        Returns:
            Result from the request function

        Raises:
            RuntimeError: If all retries fail
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                return request_func()
            except (RateLimitError, OpenAIRateLimitError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2**attempt)
                    time.sleep(delay)
                    continue
                raise RuntimeError(
                    f"{operation} failed after {self.max_retries} attempts "
                    "due to rate limiting"
                ) from e
            except (APITimeoutError, TimeoutError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2**attempt)
                    time.sleep(delay)
                    continue
                raise RuntimeError(
                    f"{operation} failed after {self.max_retries} attempts "
                    "due to timeout"
                ) from e
            except (APIError, OpenAIAPIError, Exception) as e:
                # For other errors, fail immediately without retry
                raise RuntimeError(f"{operation} failed: {str(e)}") from e

        # Should not reach here, but just in case
        raise RuntimeError(
            f"{operation} failed after {self.max_retries} attempts"
        ) from last_error


class AnthropicClient(BaseLLMClient):
    """Anthropic (Claude) client implementation.

    Provides access to Claude models via the Anthropic API with retry logic
    and error handling.
    """

    def __init__(self, config: LLMConfig):
        """Initialize the Anthropic client.

        Args:
            config: LLM configuration

        Raises:
            ValueError: If ANTHROPIC_API_KEY environment variable is not set
        """
        super().__init__(config)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Please set it with: export ANTHROPIC_API_KEY=your-key"
            )

        self.client = Anthropic(api_key=api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2048,
    ) -> str:
        """Generate completion from prompt using Claude.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt to set context
            temperature: Optional temperature override (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If API call fails after retries
        """
        temp = temperature if temperature is not None else self.config.temperature

        def make_request() -> str:
            params = {
                "model": self.config.model,
                "max_tokens": max_tokens,
                "temperature": temp,
                "messages": [{"role": "user", "content": prompt}],
            }

            if system_prompt:
                params["system"] = system_prompt

            response = self.client.messages.create(**params)  # type: ignore[call-overload]
            return response.content[0].text

        return self._make_request_with_retry(make_request, "Anthropic text generation")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Generate structured JSON response using Claude.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt to set context
            schema: Optional JSON schema (included in system prompt)

        Returns:
            Parsed JSON response as dictionary

        Raises:
            ValueError: If JSON is malformed
            RuntimeError: If API call fails after retries
        """

        def make_request() -> dict[str, Any]:
            # Build system prompt with JSON instructions
            json_system_prompt = system_prompt or ""
            json_system_prompt += (
                "\n\nYou must respond with valid JSON only. Do not include any "
                "explanations or markdown formatting, just the raw JSON."
            )

            if schema:
                json_system_prompt += (
                    f"\n\nThe JSON must conform to this schema:\n"
                    f"{json.dumps(schema, indent=2)}"
                )

            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=4096,  # JSON responses may be longer
                temperature=self.config.temperature,
                system=json_system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text  # type: ignore[union-attr]

            # Parse JSON response
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to parse JSON response: {e}\nResponse: {text}"
                )

        return self._make_request_with_retry(make_request, "Anthropic JSON generation")


class OpenAIClient(BaseLLMClient):
    """OpenAI client implementation.

    Provides access to GPT models via the OpenAI API with retry logic
    and error handling.
    """

    def __init__(self, config: LLMConfig):
        """Initialize the OpenAI client.

        Args:
            config: LLM configuration

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
        """
        super().__init__(config)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it with: export OPENAI_API_KEY=your-key"
            )

        self.client = OpenAI(api_key=api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2048,
    ) -> str:
        """Generate completion from prompt using GPT.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt to set context
            temperature: Optional temperature override (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If API call fails after retries
        """
        temp = temperature if temperature is not None else self.config.temperature

        def make_request() -> str:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=max_tokens,
                temperature=temp,
                messages=messages,  # type: ignore[arg-type]
            )

            return response.choices[0].message.content or ""

        return self._make_request_with_retry(make_request, "OpenAI text generation")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Generate structured JSON response using GPT.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt to set context
            schema: Optional JSON schema (not enforced by OpenAI API currently)

        Returns:
            Parsed JSON response as dictionary

        Raises:
            ValueError: If JSON is malformed
            RuntimeError: If API call fails after retries
        """

        def make_request() -> dict[str, Any]:
            # Build system prompt with JSON instructions
            json_system_prompt = system_prompt or ""
            json_system_prompt += (
                "\n\nYou must respond with valid JSON only. Do not include any "
                "explanations or markdown formatting, just the raw JSON."
            )

            if schema:
                json_system_prompt += (
                    f"\n\nThe JSON must conform to this schema:\n"
                    f"{json.dumps(schema, indent=2)}"
                )

            messages = [
                {"role": "system", "content": json_system_prompt},
                {"role": "user", "content": prompt},
            ]

            response = self.client.chat.completions.create(  # type: ignore[call-overload]
                model=self.config.model,
                max_tokens=4096,  # JSON responses may be longer
                temperature=self.config.temperature,
                messages=messages,
                response_format={"type": "json_object"},  # Enable JSON mode
            )

            text = response.choices[0].message.content or "{}"

            # Parse JSON response
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to parse JSON response: {e}\nResponse: {text}"
                )

        return self._make_request_with_retry(make_request, "OpenAI JSON generation")


class LLMClientFactory:
    """Factory for creating appropriate LLM client based on provider."""

    @staticmethod
    def create_client(config: LLMConfig) -> BaseLLMClient:
        """Create LLM client based on provider in config.

        Args:
            config: LLM configuration with provider specification

        Returns:
            Appropriate LLM client instance (Anthropic or OpenAI)

        Raises:
            ValueError: If provider is not supported or API key is missing
        """
        if config.provider == LLMProvider.ANTHROPIC:
            return AnthropicClient(config)
        elif config.provider == LLMProvider.OPENAI:
            return OpenAIClient(config)
        else:
            raise ValueError(
                f"Unknown provider: {config.provider}. "
                f"Supported providers: {LLMProvider.ANTHROPIC}, {LLMProvider.OPENAI}"
            )
