# chuk_llm/api/core.py
"""
Core ask/stream functions with unified configuration and automatic session tracking
==================================================================================

Main API functions using the unified configuration system with integrated session management.
FIXED VERSION - Enhanced streaming with full tool call support.
"""

import contextlib
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Optional

from chuk_llm.api.config import get_current_config
from chuk_llm.configuration import ConfigValidator, Feature, get_config
from chuk_llm.llm.client import get_client

# Try to import session manager
try:
    from chuk_ai_session_manager import SessionManager

    _SESSION_AVAILABLE = True
except ImportError:
    _SESSION_AVAILABLE = False
    SessionManager = None

logger = logging.getLogger(__name__)

# Global session manager instance
_global_session_manager = None


def _resolve_model_alias(provider: str, model: str) -> str:
    """Resolve model alias to actual model name.

    Args:
        provider: The provider name
        model: The model name or alias

    Returns:
        The resolved model name
    """
    if not model:
        return model

    try:
        config_manager = get_config()

        # First check global aliases
        try:
            global_aliases = config_manager.get_global_aliases()
            # Check if global_aliases is iterable (not a Mock)
            if hasattr(global_aliases, "__contains__") and model in global_aliases:
                alias_target = global_aliases[model]
                if "/" in alias_target:
                    # It's a provider/model alias
                    alias_provider, alias_model = alias_target.split("/", 1)
                    if alias_provider == provider:
                        # Same provider, use the aliased model
                        model = alias_model
                        logger.debug(
                            f"Resolved global alias '{model}' to '{alias_model}'"
                        )
        except (AttributeError, TypeError):
            # Mock object or missing method, skip global alias resolution
            pass

        # Then use _ensure_model_available which handles provider-specific aliases and discovery
        try:
            if hasattr(config_manager, "_ensure_model_available"):
                resolved_model = config_manager._ensure_model_available(provider, model)

                if resolved_model and resolved_model != model:
                    logger.debug(
                        f"Resolved model '{model}' to '{resolved_model}' for provider '{provider}'"
                    )
                    return resolved_model
                elif not resolved_model:
                    # Model couldn't be resolved, return original and let API handle error
                    logger.debug(
                        f"Could not resolve model '{model}' for provider '{provider}', using as-is"
                    )
                    return model

                return resolved_model
        except (AttributeError, TypeError):
            # Mock object or missing method, return original model
            pass
    except Exception as e:
        # Any error in resolution, just return the original model
        logger.debug(f"Error resolving model alias: {e}")

    return model


# Check if sessions should be disabled via environment variable
_SESSIONS_ENABLED = _SESSION_AVAILABLE and os.getenv(
    "CHUK_LLM_DISABLE_SESSIONS", ""
).lower() not in ("true", "1", "yes")


def _get_session_manager() -> Optional["SessionManager"]:
    """Get or create the global session manager with lazy initialization."""
    global _global_session_manager

    if not _SESSIONS_ENABLED:
        return None

    if _global_session_manager is None:
        try:
            # Get system prompt from config if available
            config = get_current_config()
            system_prompt = config.get("system_prompt")

            _global_session_manager = SessionManager(
                system_prompt=system_prompt,
                infinite_context=True,  # Enable by default
                token_threshold=4000,  # Reasonable default
            )
        except Exception as e:
            logger.debug(f"Could not create session manager: {e}")
            return None

    return _global_session_manager


def _supports_tools_by_model(model_name: str) -> bool:
    """Check if a model supports tools based on model name patterns."""
    if not model_name:
        return True  # Assume support if unknown

    model_lower = model_name.lower()

    # Old reasoning models that don't support tools
    old_reasoning_models = ["o1-preview-2024-09-12", "o1-mini-2024-09-12"]

    return all(old_model not in model_lower for old_model in old_reasoning_models)


async def _track_user_message(
    session_manager: Optional["SessionManager"], prompt: str
) -> None:
    """Safely track user message in session."""
    if session_manager:
        try:
            await session_manager.user_says(prompt)
        except Exception as e:
            logger.debug(f"Session tracking error (user): {e}")


async def _track_ai_response(
    session_manager: Optional["SessionManager"],
    response: str,
    model: str,
    provider: str,
) -> None:
    """Safely track AI response in session."""
    if session_manager:
        try:
            await session_manager.ai_responds(response, model=model, provider=provider)
        except Exception as e:
            logger.debug(f"Session tracking error (response): {e}")


async def ask(
    prompt: str,
    *,
    provider: str | None = None,
    model: str | None = None,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    tools: list[dict[str, Any]] | None = None,
    json_mode: bool = False,
    context: str | None = None,
    previous_messages: list[dict[str, str]] | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    **kwargs: Any,
) -> str | dict[str, Any]:
    """
    Ask a question and get a response with unified configuration and automatic session tracking.

    Args:
        prompt: The question/prompt to send
        provider: LLM provider (uses config default if not specified)
        model: Model name (uses provider default if not specified)
        system_prompt: System prompt override
        temperature: Temperature override
        max_tokens: Max tokens override
        tools: Function tools for the LLM (OpenAI format)
        json_mode: Enable JSON mode response
        context: Additional context for the question (stateless)
        previous_messages: Previous messages for context (stateless)
        base_url: Override the API base URL
        api_key: Override the API key
        **kwargs: Additional arguments

    Returns:
        If tools provided: dict with 'response' and 'tool_calls' keys
        Otherwise: The LLM's response as a string
    """
    # Get session manager
    session_manager = _get_session_manager()

    # Track user message if session is available
    await _track_user_message(session_manager, prompt)

    # Get base configuration
    config = get_current_config()

    # Determine effective provider and model
    effective_provider = provider or config["provider"]
    effective_model = model or config["model"]

    # Resolve model alias if provider is specified
    if effective_provider and effective_model:
        effective_model = _resolve_model_alias(effective_provider, effective_model)

    # Resolve provider-specific settings when provider is overridden
    config_manager = get_config()

    if provider is not None:
        # Provider override - resolve all provider-specific settings
        try:
            provider_config = config_manager.get_provider(provider)
            effective_api_key = config_manager.get_api_key(provider)
            effective_api_base = provider_config.api_base

            # Resolve model if needed
            if model is None:
                effective_model = provider_config.default_model

        except Exception as e:
            logger.warning(f"Could not resolve provider '{provider}': {e}")
            # Fallback to cached config
            effective_api_key = config["api_key"]
            effective_api_base = config["api_base"]
    else:
        # No provider override - use cached config
        effective_api_key = config["api_key"]
        effective_api_base = config["api_base"]

        # Still resolve model if needed
        if not effective_model:
            try:
                provider_config = config_manager.get_provider(effective_provider)
                effective_model = provider_config.default_model
            except Exception:
                pass

    # Update session system prompt if provided
    if system_prompt and session_manager:
        try:
            await session_manager.update_system_prompt(system_prompt)
        except Exception as e:
            logger.debug(f"Could not update session system prompt: {e}")

    # Build effective configuration with dynamic overrides
    effective_config = {
        "provider": effective_provider,
        "model": effective_model,
        "api_key": api_key or effective_api_key,  # Dynamic override takes precedence
        "api_base": base_url or effective_api_base,  # Dynamic override takes precedence
        "system_prompt": system_prompt or config.get("system_prompt"),
        "temperature": temperature
        if temperature is not None
        else config.get("temperature"),
        "max_tokens": max_tokens
        if max_tokens is not None
        else config.get("max_tokens"),
    }

    # Validate request compatibility
    is_valid, issues = ConfigValidator.validate_request_compatibility(
        provider_name=effective_provider,
        model=effective_model,
        tools=tools,
        stream=False,
        **{"response_format": "json" if json_mode else None},
    )

    if not is_valid:
        # Log warnings but don't fail - allow fallbacks
        for issue in issues:
            logger.warning(f"Request compatibility issue: {issue}")

    # Get client with correct parameters
    client = get_client(
        provider=effective_config["provider"],
        model=effective_config["model"],
        api_key=effective_config["api_key"],
        api_base=effective_config["api_base"],
    )

    # Build messages with intelligent system prompt handling
    messages = _build_messages(
        prompt=prompt,
        system_prompt=effective_config.get("system_prompt"),
        tools=tools,
        provider=effective_provider,
        model=effective_model,
        context=context,
        previous_messages=previous_messages,
    )

    # Remove context and previous_messages from kwargs if present
    completion_kwargs = kwargs.copy()
    completion_kwargs.pop("context", None)
    completion_kwargs.pop("previous_messages", None)

    # Prepare completion arguments
    completion_args = {"messages": messages}

    # Add tools if supported - FIXED: Better tool support detection
    if tools:
        try:
            # First check our internal knowledge
            model_supports_tools = _supports_tools_by_model(effective_model)

            # Then check configuration if available
            config_supports_tools = True
            with contextlib.suppress(Exception):
                # Unknown provider/model, use our internal logic
                config_supports_tools = config_manager.supports_feature(
                    effective_provider, Feature.TOOLS, effective_model
                )

            if model_supports_tools and config_supports_tools:
                completion_args["tools"] = tools
            else:
                if not model_supports_tools:
                    logger.debug(
                        f"{effective_model} is an old reasoning model without tool support"
                    )
                else:
                    logger.warning(
                        f"{effective_provider}/{effective_model} doesn't support tools according to config"
                    )

        except Exception:
            # Unknown provider, try anyway
            completion_args["tools"] = tools

    # Add JSON mode if requested and supported
    if json_mode:
        try:
            if config_manager.supports_feature(
                effective_provider, Feature.JSON_MODE, effective_model
            ):
                if effective_provider == "openai":
                    completion_args["response_format"] = {"type": "json_object"}
                elif effective_provider == "gemini":
                    completion_args.setdefault("generation_config", {})[
                        "response_mime_type"
                    ] = "application/json"
                # For other providers, we'll add instruction to system message
            else:
                logger.warning(
                    f"{effective_provider}/{effective_model} doesn't support JSON mode"
                )
                # Add JSON instruction to system message
                _add_json_instruction_to_messages(messages)
        except Exception:
            # Unknown provider, try anyway
            if effective_provider == "openai":
                completion_args["response_format"] = {"type": "json_object"}

    # Add temperature and max_tokens - Let provider client handle parameter mapping
    if effective_config.get("temperature") is not None:
        completion_args["temperature"] = effective_config["temperature"]
    if effective_config.get("max_tokens") is not None:
        completion_args["max_tokens"] = effective_config["max_tokens"]

    # Add any additional kwargs
    completion_args.update(completion_kwargs)

    # Make the request
    try:
        response = await client.create_completion(**completion_args)

        # Extract response
        if isinstance(response, dict):
            if response.get("error"):
                raise Exception(
                    f"LLM Error: {response.get('error_message', 'Unknown error')}"
                )
            response_text = response.get("response", "")
        else:
            response_text = str(response)

        # Track AI response if session is available
        await _track_ai_response(
            session_manager, response_text, effective_model, effective_provider
        )

        # Track tool usage if tools were provided
        if (
            tools
            and isinstance(response, dict)
            and "tool_calls" in response
            and session_manager
        ):
            try:
                for tool_call in response["tool_calls"]:
                    await session_manager.tool_used(
                        tool_name=tool_call.get("name", "unknown"),
                        arguments=tool_call.get("arguments", {}),
                        result=tool_call.get("result", {}),
                    )
            except Exception as e:
                logger.debug(f"Session tool tracking error: {e}")

        # Return full response dict when tools are provided
        if tools and isinstance(response, dict):
            # Ensure response has expected structure
            if "response" not in response:
                response["response"] = response_text
            if "tool_calls" not in response:
                response["tool_calls"] = []
            return response

        return response_text

    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise


async def stream(
    prompt: str,
    context: str | None = None,
    previous_messages: list[dict[str, str]] | None = None,
    return_tool_calls: bool | None = None,  # NEW: Control whether to return tool calls
    base_url: str | None = None,
    api_key: str | None = None,
    **kwargs: Any,
) -> AsyncIterator[str | dict[str, Any]]:
    """
    Stream a response token by token with unified configuration and automatic session tracking.
    ENHANCED VERSION - Now properly handles tool calls when requested.

    Args:
        prompt: The question/prompt to send
        context: Additional context for the question (stateless)
        previous_messages: Previous messages for context (stateless)
        return_tool_calls: Whether to return full chunks with tool calls (auto-detected if None)
        **kwargs: Same arguments as ask() plus streaming-specific options

    Yields:
        When return_tool_calls=False or no tools: str chunks
        When return_tool_calls=True or tools provided: Dict with 'response' and 'tool_calls'
    """
    # Auto-detect whether to return tool calls
    tools = kwargs.get("tools")
    if return_tool_calls is None:
        return_tool_calls = bool(tools)

    # Get session manager
    session_manager = _get_session_manager()

    # Track user message if session is available
    await _track_user_message(session_manager, prompt)

    # Collect full response for session tracking
    full_response = ""
    all_tool_calls = []

    # Get base configuration
    config = get_current_config()

    # Extract parameters
    provider = kwargs.get("provider")
    model = kwargs.get("model")

    # Determine effective provider and settings (same logic as ask())
    effective_provider = provider or config["provider"]
    effective_model = model or config["model"]

    # Resolve model alias if provider is specified
    if effective_provider and effective_model:
        effective_model = _resolve_model_alias(effective_provider, effective_model)

    # Resolve provider-specific settings
    config_manager = get_config()

    if provider is not None:
        try:
            provider_config = config_manager.get_provider(provider)
            effective_api_key = config_manager.get_api_key(provider)
            effective_api_base = provider_config.api_base

            if model is None:
                effective_model = provider_config.default_model

        except Exception as e:
            logger.warning(f"Could not resolve provider '{provider}': {e}")
            effective_api_key = config["api_key"]
            effective_api_base = config["api_base"]
    else:
        effective_api_key = config["api_key"]
        effective_api_base = config["api_base"]

        if not effective_model:
            try:
                provider_config = config_manager.get_provider(effective_provider)
                effective_model = provider_config.default_model
            except Exception:
                pass

    # Apply dynamic overrides if provided
    if api_key:
        effective_api_key = api_key
    if base_url:
        effective_api_base = base_url

    # Update session system prompt if provided
    system_prompt = kwargs.get("system_prompt")
    if system_prompt and session_manager:
        try:
            await session_manager.update_system_prompt(system_prompt)
        except Exception as e:
            logger.debug(f"Could not update session system prompt: {e}")

    # Build effective configuration
    effective_config = {
        "provider": effective_provider,
        "model": effective_model,
        "api_key": effective_api_key,
        "api_base": effective_api_base,
        "system_prompt": system_prompt or config.get("system_prompt"),
        "temperature": kwargs.get("temperature")
        if "temperature" in kwargs
        else config.get("temperature"),
        "max_tokens": kwargs.get("max_tokens")
        if "max_tokens" in kwargs
        else config.get("max_tokens"),
    }

    # Validate streaming support
    try:
        if not config_manager.supports_feature(
            effective_provider, Feature.STREAMING, effective_model
        ):
            logger.warning(
                f"{effective_provider}/{effective_model} doesn't support streaming"
            )
            # Fall back to non-streaming
            response = await ask(prompt, **kwargs)

            # Track the response if session is available
            await _track_ai_response(
                session_manager, response, effective_model, effective_provider
            )

            if return_tool_calls:
                yield {"response": response, "tool_calls": []}
            else:
                yield response
            return
    except Exception:
        pass  # Unknown provider, proceed anyway

    # Get client
    client = get_client(
        provider=effective_config["provider"],
        model=effective_config["model"],
        api_key=effective_config["api_key"],
        api_base=effective_config["api_base"],
    )

    # Build messages
    messages = _build_messages(
        prompt=prompt,
        system_prompt=effective_config.get("system_prompt"),
        tools=tools,
        provider=effective_provider,
        model=effective_model,
        context=context,
        previous_messages=previous_messages,
    )

    # Remove context and previous_messages from kwargs if present
    completion_kwargs = kwargs.copy()
    completion_kwargs.pop("context", None)
    completion_kwargs.pop("previous_messages", None)

    # Prepare streaming arguments
    completion_args = {
        "messages": messages,
        "stream": True,
    }

    # Add tools if supported
    if tools:
        try:
            # Check configuration-based tool support
            if config_manager.supports_feature(
                effective_provider, Feature.TOOLS, effective_model
            ):
                completion_args["tools"] = tools
            else:
                logger.debug(
                    f"{effective_provider}/{effective_model} doesn't support tools according to configuration"
                )

        except Exception:
            # Unknown provider/model in configuration, let the client handle it
            completion_args["tools"] = tools

    # Add JSON mode if requested and supported
    json_mode = kwargs.get("json_mode", False)
    if json_mode:
        try:
            if config_manager.supports_feature(
                effective_provider, Feature.JSON_MODE, effective_model
            ):
                if effective_provider == "openai":
                    completion_args["response_format"] = {"type": "json_object"}
                elif effective_provider == "gemini":
                    completion_args.setdefault("generation_config", {})[
                        "response_mime_type"
                    ] = "application/json"
            else:
                logger.warning(
                    f"{effective_provider}/{effective_model} doesn't support JSON mode"
                )
                _add_json_instruction_to_messages(messages)
        except Exception:
            if effective_provider == "openai":
                completion_args["response_format"] = {"type": "json_object"}

    # Add temperature and max_tokens
    if effective_config.get("max_tokens") is not None:
        completion_args["max_tokens"] = effective_config["max_tokens"]
    if effective_config.get("temperature") is not None:
        completion_args["temperature"] = effective_config["temperature"]

    # Remove parameters that we've already handled from completion_kwargs
    for param in [
        "provider",
        "model",
        "system_prompt",
        "max_tokens",
        "temperature",
        "tools",
        "json_mode",
        "max_completion_tokens",
        "return_tool_calls",
    ]:
        completion_kwargs.pop(param, None)

    # Add remaining kwargs
    completion_args.update(completion_kwargs)

    # Stream the response with proper error handling
    try:
        logger.debug(
            f"Starting streaming with {effective_provider}/{effective_model}, return_tool_calls={return_tool_calls}"
        )

        # Call client.create_completion with stream=True - this returns an async generator
        response_stream = client.create_completion(**completion_args)

        chunk_count = 0

        async for chunk in response_stream:
            chunk_count += 1

            try:
                if return_tool_calls:
                    # ENHANCED: Return full chunks with tool calls preserved
                    if isinstance(chunk, dict):
                        # Track response text for session
                        response_text = chunk.get("response", "")
                        if response_text:
                            full_response += response_text

                        # Track tool calls
                        chunk_tool_calls = chunk.get("tool_calls", [])
                        if chunk_tool_calls:
                            all_tool_calls.extend(chunk_tool_calls)

                        # Yield the full chunk
                        yield chunk
                    else:
                        # Convert non-dict chunks to proper format
                        chunk_str = str(chunk)
                        full_response += chunk_str
                        yield {"response": chunk_str, "tool_calls": []}
                else:
                    # BACKWARD COMPATIBLE: Text-only streaming
                    content = _extract_streaming_content(chunk)

                    if content:
                        full_response += content
                        yield content

            except Exception as chunk_error:
                logger.debug(f"Error processing chunk {chunk_count}: {chunk_error}")
                continue  # Skip problematic chunks

        logger.debug(
            f"Streaming completed: {chunk_count} chunks, {len(full_response)} total chars, {len(all_tool_calls)} tool calls"
        )

        # Track complete response if session is available
        if full_response:
            await _track_ai_response(
                session_manager, full_response, effective_model, effective_provider
            )

        # Track tool calls if any
        if all_tool_calls and session_manager:
            try:
                for tool_call in all_tool_calls:
                    func_info = tool_call.get("function", {})
                    await session_manager.tool_used(
                        tool_name=func_info.get("name", "unknown"),
                        arguments=func_info.get("arguments", "{}"),
                        result={},
                    )
            except Exception as e:
                logger.debug(f"Session tool tracking error: {e}")

    except Exception as e:
        logger.error(f"Streaming failed: {e}")

        # Try fallback to non-streaming
        try:
            logger.info("Attempting fallback to non-streaming mode")
            fallback_kwargs = {k: v for k, v in kwargs.items() if k != "stream"}
            fallback_response = await ask(
                prompt,
                context=context,
                previous_messages=previous_messages,
                **fallback_kwargs,
            )

            if return_tool_calls:
                yield {"response": fallback_response, "tool_calls": []}
            else:
                yield fallback_response
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            error_msg = f"[Error: {str(e)}]"

            if return_tool_calls:
                yield {"response": error_msg, "tool_calls": [], "error": True}
            else:
                yield error_msg


def _extract_streaming_content(chunk: Any) -> str:
    """
    Extract text content from a streaming chunk with enhanced tool call formatting.
    FIXED: Single comprehensive implementation matching diagnostic output.
    """
    try:
        # Handle dictionary responses from OpenAI client
        if isinstance(chunk, dict):
            # Handle error responses
            if chunk.get("error"):
                return f"[Error: {chunk.get('error_message', 'Unknown error')}]"

            # FIXED: Handle tool calls with format matching diagnostic expectations
            if chunk.get("tool_calls"):
                tool_calls = chunk["tool_calls"]
                content_parts = []

                for tc in tool_calls:
                    if tc.get("function", {}).get("name"):
                        func_name = tc["function"]["name"]
                        args_portion = tc["function"].get("arguments", "")

                        if tc.get("incremental") and args_portion:
                            # For incremental updates, show the JSON being built
                            # Format to match: [Calling execute_sql]: {"query":"..."}
                            if args_portion.strip().startswith("{"):
                                content_parts.append(
                                    f"[Calling {func_name}]: {args_portion}"
                                )
                            else:
                                content_parts.append(args_portion)

                        elif not tc.get("incremental"):
                            # This is a complete tool call
                            try:
                                import json

                                json.loads(args_portion) if args_portion else {}
                                # For complete calls, show the formatted JSON
                                if args_portion:
                                    content_parts.append(
                                        f"[Calling {func_name}]: {args_portion}"
                                    )
                                else:
                                    content_parts.append(f"[Calling {func_name}]")
                            except Exception:
                                if args_portion:
                                    content_parts.append(
                                        f"[Calling {func_name}]: {args_portion}"
                                    )
                                else:
                                    content_parts.append(f"[Calling {func_name}]")

                if content_parts:
                    return "".join(content_parts)

            # Handle standard response format
            if "response" in chunk:
                content = chunk["response"]
                if content:  # Only return non-empty content
                    return content

            # Handle choices format (direct from OpenAI API)
            if "choices" in chunk and chunk["choices"]:
                choice = chunk["choices"][0]
                if "delta" in choice and choice["delta"]:
                    delta = choice["delta"]
                    if "content" in delta:
                        content = delta["content"]
                        if content:  # Only return non-empty content
                            return content
                elif "message" in choice:
                    content = choice["message"].get("content", "")
                    if content:  # Only return non-empty content
                        return content

            return ""

        elif isinstance(chunk, str):
            return chunk

        else:
            # Try to extract from object attributes (for OpenAI SDK objects)
            if hasattr(chunk, "choices") and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, "delta") and choice.delta:
                    if hasattr(choice.delta, "content") and choice.delta.content:
                        return choice.delta.content

                    # Handle tool calls in SDK object format
                    if hasattr(choice.delta, "tool_calls") and choice.delta.tool_calls:
                        content_parts = []
                        for tc in choice.delta.tool_calls:
                            if hasattr(tc, "function") and tc.function:
                                func_name = getattr(tc.function, "name", "")
                                args_str = getattr(tc.function, "arguments", "")

                                if func_name and args_str:
                                    # Format to match diagnostic: [Calling execute_sql]: {"query":"..."}
                                    content_parts.append(
                                        f"[Calling {func_name}]: {args_str}"
                                    )
                                elif func_name:
                                    content_parts.append(f"[Calling {func_name}]")

                        if content_parts:
                            return "".join(content_parts)

                elif hasattr(choice, "message") and choice.message:
                    if hasattr(choice.message, "content"):
                        content = choice.message.content
                        if content:
                            return content

            return ""

    except Exception as e:
        logger.debug(f"Error extracting streaming content: {e}")
        return ""


def _build_messages(
    prompt: str,
    system_prompt: str | None,
    tools: list[dict[str, Any]] | None,
    provider: str,
    model: str | None,
    context: str | None = None,
    previous_messages: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Build messages array with intelligent system prompt handling"""
    messages = []

    # Determine system prompt
    if system_prompt:
        system_content = system_prompt
    elif tools:
        # Generate system prompt for tools
        try:
            from chuk_llm.llm.system_prompt_generator import SystemPromptGenerator

            generator = SystemPromptGenerator()
            system_content = generator.generate_prompt(tools)
        except ImportError:
            system_content = (
                "You are a helpful AI assistant with access to function calling tools."
            )
    else:
        # Default system prompt
        system_content = "You are a helpful AI assistant. Provide clear, accurate, and concise responses."

    # Add context to system prompt if provided
    if context:
        system_content += f"\n\nContext: {context}"

    # Add system message if provider supports it
    try:
        config_manager = get_config()
        if config_manager.supports_feature(provider, Feature.SYSTEM_MESSAGES, model):
            messages.append({"role": "system", "content": system_content})
        else:
            # Prepend system content to user message for providers that don't support system messages
            prompt = f"System: {system_content}\n\nUser: {prompt}"
    except Exception:
        # Unknown provider, assume it supports system messages
        messages.append({"role": "system", "content": system_content})

    # Add previous messages if provided (for stateless context)
    if previous_messages:
        messages.extend(previous_messages)

    messages.append({"role": "user", "content": prompt})
    return messages


def _add_json_instruction_to_messages(messages: list[dict[str, Any]]) -> None:
    """Add JSON mode instruction to system message for providers without native support"""
    json_instruction = "\n\nIMPORTANT: You must respond with valid JSON only. Do not include any text outside the JSON structure."

    # Find system message and add instruction
    for message in messages:
        if message.get("role") == "system":
            message["content"] += json_instruction
            return

    # No system message found, add one
    messages.insert(
        0,
        {
            "role": "system",
            "content": f"You are a helpful AI assistant.{json_instruction}",
        },
    )


# Session management functions
async def get_session_stats(include_all_segments: bool = False) -> dict[str, Any]:
    """Get current session statistics."""
    session_manager = _get_session_manager()
    if session_manager:
        try:
            return await session_manager.get_stats(
                include_all_segments=include_all_segments
            )
        except Exception as e:
            logger.debug(f"Could not get session stats: {e}")

    return {
        "sessions_enabled": _SESSIONS_ENABLED,
        "session_available": False,
        "message": "No active session",
    }


async def get_session_history(
    include_all_segments: bool = False,
) -> list[dict[str, Any]]:
    """Get current session conversation history."""
    session_manager = _get_session_manager()
    if session_manager:
        try:
            return await session_manager.get_conversation(
                include_all_segments=include_all_segments
            )
        except Exception as e:
            logger.debug(f"Could not get session history: {e}")

    return []


def get_current_session_id() -> str | None:
    """Get the current session ID if available."""
    session_manager = _get_session_manager()
    return session_manager.session_id if session_manager else None


def reset_session() -> None:
    """Reset the current session (start a new one)."""
    global _global_session_manager
    _global_session_manager = None
    logger.info("Session reset - new session will be created on next call")


def disable_sessions() -> None:
    """Disable session tracking for the current process."""
    global _SESSIONS_ENABLED, _global_session_manager
    _SESSIONS_ENABLED = False
    _global_session_manager = None
    logger.info("Session tracking disabled")


def enable_sessions() -> None:
    """Re-enable session tracking if available."""
    global _SESSIONS_ENABLED
    if _SESSION_AVAILABLE:
        _SESSIONS_ENABLED = True
        logger.info("Session tracking enabled")
    else:
        logger.warning("Cannot enable sessions - chuk-ai-session-manager not installed")


# Enhanced convenience functions
async def ask_json(prompt: str, **kwargs: Any) -> str:
    """Ask for a JSON response"""
    return await ask(prompt, json_mode=True, **kwargs)


async def quick_ask(prompt: str, provider: str | None = None) -> str:
    """Quick ask with optional provider override"""
    return await ask(prompt, provider=provider)


async def multi_provider_ask(prompt: str, providers: list[str]) -> dict[str, str]:
    """Ask the same question to multiple providers"""
    import asyncio

    async def ask_provider(provider: str) -> tuple[str, str]:
        try:
            response = await ask(prompt, provider=provider)
            return provider, response
        except Exception as e:
            return provider, f"Error: {e}"

    tasks = [ask_provider(provider) for provider in providers]
    results = await asyncio.gather(*tasks)

    return dict(results)


# Validation helpers
def validate_request(
    prompt: str,
    provider: str | None = None,
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Validate a request before sending"""
    config = get_current_config()
    effective_provider = provider or config["provider"]
    effective_model = model or config["model"]

    # Build fake messages to check for vision content
    messages = [{"role": "user", "content": prompt}]

    is_valid, issues = ConfigValidator.validate_request_compatibility(
        provider_name=effective_provider,
        model=effective_model,
        messages=messages,
        tools=tools,
        stream=kwargs.get("stream", False),
        **kwargs,
    )

    return {
        "valid": is_valid,
        "issues": issues,
        "provider": effective_provider,
        "model": effective_model,
    }
