# chuk_llm/llm/core/base.py
"""
Common abstract interface for every LLM adapter.
"""

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from typing import Any


class BaseLLMClient(abc.ABC):
    """Abstract base class for LLM chat clients."""

    @abc.abstractmethod
    def create_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        *,
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]] | Any:
        """
        Generate (or continue) a chat conversation.

        Parameters
        ----------
        messages
            List of ChatML-style message dicts.
        tools
            Optional list of OpenAI-function-tool schemas.
        stream
            Whether to stream the response or return complete response.
        **kwargs
            Additional parameters to pass to the underlying LLM.

        Returns
        -------
        When stream=True: AsyncIterator that yields chunks as they arrive
        When stream=False: Awaitable that resolves to standardised payload
                          with keys ``response`` and ``tool_calls``.

        CRITICAL: When stream=True, this method MUST NOT be async and
                 MUST return the async iterator directly (no awaiting).
        """
        ...
