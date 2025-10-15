# chuk_llm/api/sync.py
"""
Clean synchronous wrappers using event loop manager
===================================================

Simple sync wrappers for the async API.
"""

from typing import Any

from .core import ask, stream
from .event_loop_manager import run_sync


def ask_sync(prompt: str, **kwargs) -> str | dict[str, Any]:
    """
    Synchronous version of ask().

    Args:
        prompt: The message to send
        **kwargs: All the same arguments as ask()

    Returns:
        The LLM's response as a string, or dict if tools are provided
    """
    return run_sync(ask(prompt, **kwargs))


def stream_sync(prompt: str, **kwargs) -> list[str]:
    """
    Synchronous version of stream() - returns list of chunks.

    Args:
        prompt: The message to send
        **kwargs: All the same arguments as stream()

    Returns:
        List of response chunks
    """

    async def collect_chunks():
        chunks = []
        async for chunk in stream(prompt, **kwargs):
            chunks.append(chunk)
        return chunks

    return run_sync(collect_chunks())


def stream_sync_iter(prompt: str, **kwargs):
    """
    Synchronous streaming iterator.

    Args:
        prompt: The message to send
        **kwargs: All the same arguments as stream()

    Yields:
        Response chunks as they arrive
    """
    import queue
    import threading

    chunk_queue = queue.Queue()  # type: ignore[var-annotated]
    exception = None

    def run_stream():
        nonlocal exception

        async def async_stream():
            try:
                async for chunk in stream(prompt, **kwargs):
                    chunk_queue.put(chunk)
            except Exception:
                pass
            finally:
                chunk_queue.put(None)  # Sentinel

        try:
            run_sync(async_stream())
        except Exception as e:
            exception = e
            chunk_queue.put(None)

    # Start streaming in a thread
    thread = threading.Thread(target=run_stream)
    thread.start()

    # Yield chunks as they arrive
    while True:
        chunk = chunk_queue.get()
        if chunk is None:  # Sentinel
            break
        yield chunk

    thread.join()

    if exception:
        raise exception from None


def compare_providers(question: str, providers: list[str] = None) -> dict[str, Any]:
    """
    Ask the same question to multiple providers.

    Args:
        question: The question to ask
        providers: List of provider names (uses available providers if not specified)

    Returns:
        Dictionary mapping provider names to responses (string or dict if tools provided)
    """
    if providers is None:
        from chuk_llm.configuration import get_config

        config = get_config()
        all_providers = config.get_all_providers()
        providers = all_providers[:3] if len(all_providers) >= 3 else all_providers

    results = {}
    for provider in providers:
        try:
            results[provider] = ask_sync(question, provider=provider)
        except Exception as e:
            results[provider] = f"Error: {str(e)}"

    return results


def quick_question(question: str, provider: str = None) -> str | dict[str, Any]:
    """
    Quick one-off question using default or specified provider.

    Args:
        question: The question to ask
        provider: Provider to use (uses global default if not specified)

    Returns:
        The response (string or dict if tools provided)
    """
    if not provider:
        from chuk_llm.configuration import get_config

        config = get_config()
        settings = config.global_settings
        provider = settings.get("active_provider", "openai")

    return ask_sync(question, provider=provider)
