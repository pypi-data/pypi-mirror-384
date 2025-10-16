"""Pydantic AI-based LLM Provider - Modern agent framework integration"""

import os
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Optional

from pydantic_ai import Agent
from pydantic_ai.models import Model, infer_model

from .llm_provider import LLMProvider, LLMResponse

# Debug mode flag
DEBUG_MODE = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")


@dataclass
class PydanticAIResponse:
    """Enhanced response with Pydantic AI integration"""

    content: str
    model: str
    usage: dict[str, int] = None
    finish_reason: str = "stop"
    run_id: str = None


class PydanticAIProvider(LLMProvider):
    """Pydantic AI-powered LLM provider with modern agent capabilities"""

    def __init__(self, api_key: str, model_name: str = "gpt-4", provider_name: str = None):
        super().__init__(api_key, model_name)
        self._model: Model = None
        self._agent: Agent = None

        # Extract provider and model from model_name (e.g., "anthropic:claude-sonnet-4-5-20250929")
        if provider_name:
            # Provider explicitly provided (preferred method)
            self._underlying_provider_name = provider_name
            # Extract model from model_name if it has a prefix, otherwise use as-is
            if ":" in model_name:
                _, self._underlying_model_name = model_name.split(":", 1)
            else:
                self._underlying_model_name = model_name
        elif ":" in model_name:
            # Provider prefix in model_name (e.g., "anthropic:claude-sonnet-4-5-20250929")
            self._underlying_provider_name, self._underlying_model_name = model_name.split(":", 1)
        else:
            # Fallback for models without provider prefix (shouldn't happen with new code)
            self._underlying_provider_name = "unknown"
            self._underlying_model_name = model_name

        self._initialize_client()

    def _initialize_client(self):
        """Initialize Pydantic AI model and agent"""
        try:
            # Infer the model from the model name
            self._model = infer_model(self.model)

            # Create a basic agent for text completion
            self._agent = Agent(
                model=self._model,
                system_prompt="You are a helpful AI assistant that provides accurate and concise responses.",
            )

        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Pydantic AI provider: {str(e)}"
            ) from e

    @property
    def provider_name(self) -> str:
        """Get the underlying provider name (e.g., 'anthropic', 'openai')"""
        return self._underlying_provider_name

    @property
    def model_name(self) -> str:
        """Get the underlying model name (e.g., 'claude-sonnet-4-5-20250929')"""
        return self._underlying_model_name

    @property
    def model_info(self) -> str:
        """Get formatted model information"""
        return f"PydanticAI:{self.model}"

    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt using Pydantic AI"""
        if not self._agent:
            raise RuntimeError("Pydantic AI agent not initialized")

        try:
            # Run the agent with the prompt
            result = await self._agent.run(prompt)
            return result.output

        except Exception as e:
            raise RuntimeError(f"Pydantic AI completion failed: {str(e)}") from e

    async def _complete_with_streaming(
        self,
        prompt: str,
        on_token: Callable[[str], Awaitable[None]],
        **kwargs
    ):
        """Internal method to complete with streaming support"""
        try:
            # Use Pydantic AI's streaming support
            accumulated_text = ""
            last_content = ""

            async with self._agent.run_stream(prompt) as stream:
                # Iterate over the stream's text chunks
                # Note: stream.stream() may send cumulative text (snapshots) not deltas
                async for text_chunk in stream.stream():
                    if text_chunk:
                        # Check if this is a delta or cumulative
                        if text_chunk.startswith(last_content):
                            # This is cumulative - extract only the new part
                            delta = text_chunk[len(last_content):]
                            if delta:
                                accumulated_text += delta
                                await on_token(delta)  # Await async callback
                            last_content = text_chunk
                        else:
                            # This is a delta
                            accumulated_text += text_chunk
                            await on_token(text_chunk)  # Await async callback
                            last_content += text_chunk

                # StreamedRunResult doesn't need get_final(), just use accumulated text
                # Return the final result
                return type('StreamResult', (), {'output': accumulated_text})()

        except Exception as e:
            # Fallback: if streaming fails, use non-streaming
            if DEBUG_MODE:
                print(f"DEBUG: Streaming failed, falling back to non-streaming: {e}")
            result = await self._agent.run(prompt)
            # Still call on_token with the full response
            await on_token(result.output)  # Await async callback
            return result

    async def complete_with_usage(
        self,
        prompt: str,
        on_token: Optional[Callable[[str], Awaitable[None]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion with detailed usage information using Pydantic AI"""
        if not self._agent:
            raise RuntimeError("Pydantic AI agent not initialized")

        try:
            # Check if streaming is requested and supported
            if on_token is not None:
                # Use streaming path
                result = await self._complete_with_streaming(prompt, on_token, **kwargs)
            else:
                # Use non-streaming path
                result = await self._agent.run(prompt)

            # Extract usage information from the result
            usage = {}

            # Call the usage() method to get actual usage data
            usage_data = None
            if hasattr(result, "usage"):
                try:
                    usage_data = result.usage()  # Call the method!
                except Exception as e:
                    # Fallback if usage() method fails
                    pass

            if usage_data:
                # Pydantic AI usage structure may vary
                # Use new field names first, fall back to deprecated ones
                import warnings
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=DeprecationWarning)

                    if hasattr(usage_data, "input_tokens"):
                        usage["input_tokens"] = usage_data.input_tokens or 0
                    elif hasattr(usage_data, "request_tokens"):
                        usage["input_tokens"] = usage_data.request_tokens or 0

                    if hasattr(usage_data, "output_tokens"):
                        usage["output_tokens"] = usage_data.output_tokens or 0
                    elif hasattr(usage_data, "response_tokens"):
                        usage["output_tokens"] = usage_data.response_tokens or 0

                if hasattr(usage_data, "total_tokens"):
                    usage["total_tokens"] = usage_data.total_tokens or 0
                else:
                    # Calculate total if not available
                    usage["total_tokens"] = usage.get("input_tokens", 0) + usage.get(
                        "output_tokens", 0
                    )
            else:
                if DEBUG_MODE: print("DEBUG: Using fallback token estimation")
                # Fallback: estimate token usage
                input_estimate = len(prompt.split()) * 1.3
                output_estimate = (
                    len(result.output.split()) * 1.3
                    if isinstance(result.output, str)
                    else 0
                )
                if DEBUG_MODE: print(f"DEBUG: Input estimate: {input_estimate} (prompt words: {len(prompt.split())})")
                if DEBUG_MODE: print(f"DEBUG: Output estimate: {output_estimate} (result words: {len(result.output.split()) if isinstance(result.output, str) else 0})")
                usage = {
                    "input_tokens": int(input_estimate),
                    "output_tokens": int(output_estimate),
                    "total_tokens": int(input_estimate + output_estimate),
                }
                if DEBUG_MODE: print(f"DEBUG: Final estimated usage: {usage}")

            return LLMResponse(
                content=result.output,
                model=self.model,
                usage=usage,
                finish_reason="stop",
            )

        except Exception as e:
            # Add debug information
            if DEBUG_MODE: print(f"Debug: Pydantic AI error: {type(e).__name__}: {str(e)}")
            if hasattr(e, "__dict__"):
                if DEBUG_MODE: print(f"Debug: Error attributes: {e.__dict__}")
            raise RuntimeError(
                f"Pydantic AI completion with usage failed: {str(e)}"
            ) from e

    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate completion with function calling support"""
        # For now, convert to simple completion
        # TODO: Implement proper tool calling with Pydantic AI tools
        if messages:
            last_message = messages[-1]
            if last_message.get("role") == "user":
                result = await self.complete_with_usage(
                    last_message["content"], **kwargs
                )
                return {
                    "content": result.content,
                    "usage": result.usage,
                    "finish_reason": result.finish_reason,
                }

        return {"content": "", "usage": {}, "finish_reason": "stop"}

    async def stream_complete(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion from prompt using Pydantic AI"""
        if not self._agent:
            raise RuntimeError("Pydantic AI agent not initialized")

        try:
            # Use Pydantic AI streaming support
            async with self._agent.run_stream(prompt) as stream:
                async for message in stream:
                    # Handle different message types from Pydantic AI stream
                    if hasattr(message, "snapshot"):
                        # This is a streaming event with partial content
                        if (
                            hasattr(message.snapshot, "all_messages")
                            and message.snapshot.all_messages
                        ):
                            last_message = message.snapshot.all_messages[-1]
                            if (
                                hasattr(last_message, "content")
                                and last_message.content
                            ):
                                yield last_message.content
                    elif hasattr(message, "content") and message.content:
                        # Direct content message
                        yield message.content
                    elif hasattr(message, "delta") and message.delta:
                        # Delta content (incremental updates)
                        yield message.delta

        except Exception as e:
            # Fallback to regular completion if streaming fails
            try:
                result = await self.complete(prompt, **kwargs)
                yield result
            except Exception as fallback_error:
                raise RuntimeError(
                    f"Both streaming and fallback completion failed. Streaming: {str(e)}, Fallback: {str(fallback_error)}"
                ) from e

    async def close(self) -> None:
        """Close provider connections"""
        # Pydantic AI handles cleanup automatically
        pass


def create_pydantic_ai_provider(
    provider_name: str, api_key: str, model: str
) -> PydanticAIProvider:
    """Factory function to create Pydantic AI providers"""

    # Map provider names to model strings that Pydantic AI understands
    model_mapping = {
        "openai": {
            # GPT-5 models (frontier models - latest)
            "gpt-5": "openai:gpt-5",
            "gpt-5-mini": "openai:gpt-5-mini",
            "gpt-5-nano": "openai:gpt-5-nano",
            # GPT-4.1 models
            "gpt-4.1": "openai:gpt-4.1",
            "gpt-4.1-mini": "openai:gpt-4.1-mini",
            "gpt-4.1-nano": "openai:gpt-4.1-nano",
            # GPT-4o models
            "gpt-4o": "openai:gpt-4o",
            "gpt-4o-mini": "openai:gpt-4o-mini",
            # Legacy models
            "gpt-4": "openai:gpt-4",
            "gpt-4-turbo": "openai:gpt-4-turbo-preview",
            "gpt-3.5-turbo": "openai:gpt-3.5-turbo",
        },
        "anthropic": {
            "claude-3-5-sonnet-20241022": "anthropic:claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022": "anthropic:claude-3-5-haiku-20241022",
            "claude-3-opus-20240229": "anthropic:claude-3-opus-20240229",
            "claude-3-7-sonnet-20250219": "anthropic:claude-3-7-sonnet-20250219",
        },
        "gemini": {
            # Gemini 2.5 models (latest)
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2.5-pro": "gemini-2.5-pro",
            "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
            # Gemini 2.0 models
            "gemini-2.0-flash-001": "gemini-2.0-flash-001",
            "gemini-2.0-flash-lite-001": "gemini-2.0-flash-lite-001",
            "gemini-2.0-flash-exp": "gemini-2.0-flash-exp",  # Legacy experimental
            # Legacy preview models
            "gemini-2.5-flash-preview-09-2025": "gemini-2.5-flash-preview-09-2025",
            # Gemini 1.5 models (legacy)
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash",
        },
    }

    # Get the appropriate model string with improved fallback logic
    provider_models = model_mapping.get(provider_name.lower(), {})

    if model in provider_models:
        # Model found in mapping - use the mapped value
        pydantic_model = provider_models[model]
    else:
        # Model not in mapping - use the configured model directly with provider prefix
        # This allows for new models that aren't in our mapping yet
        pydantic_model = f"{provider_name.lower()}:{model}"

    # Set API key in environment for Pydantic AI
    import os

    if provider_name.lower() == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
    elif provider_name.lower() == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = api_key
    elif provider_name.lower() == "gemini":
        os.environ["GEMINI_API_KEY"] = api_key

    # Pass provider_name explicitly to ensure proper cost tracking
    return PydanticAIProvider(api_key, pydantic_model, provider_name=provider_name.lower())
