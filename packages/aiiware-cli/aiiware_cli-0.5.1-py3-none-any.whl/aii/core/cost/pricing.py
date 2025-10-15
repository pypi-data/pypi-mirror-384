"""
LLM Model Pricing Data

Maintains up-to-date pricing information for all supported LLM providers.
Prices are in USD per million tokens (MTok).

Reference:
- Anthropic: https://www.anthropic.com/pricing
- OpenAI: https://openai.com/pricing
- Google Gemini: https://ai.google.dev/pricing
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """
    Pricing information for an LLM model.

    All prices are in USD per million tokens (MTok).
    """
    input_price: float  # Price per MTok for input tokens
    output_price: float  # Price per MTok for output tokens
    cache_write_price: Optional[float] = None  # Price per MTok for cache writes (5-minute cache)
    cache_read_price: Optional[float] = None   # Price per MTok for cache reads

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_write_tokens: int = 0,
        cache_read_tokens: int = 0
    ) -> float:
        """
        Calculate total cost based on token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_write_tokens: Number of cache write tokens (optional)
            cache_read_tokens: Number of cache read tokens (optional)

        Returns:
            Total cost in USD
        """
        cost = 0.0

        # Base input/output costs
        cost += (input_tokens / 1_000_000) * self.input_price
        cost += (output_tokens / 1_000_000) * self.output_price

        # Cache costs (if applicable)
        if cache_write_tokens and self.cache_write_price:
            cost += (cache_write_tokens / 1_000_000) * self.cache_write_price

        if cache_read_tokens and self.cache_read_price:
            cost += (cache_read_tokens / 1_000_000) * self.cache_read_price

        return cost


# Anthropic Claude Pricing (as of 2025-10-03)
ANTHROPIC_PRICING: Dict[str, ModelPricing] = {
    # Claude Opus 4.1
    "claude-opus-4-1-20250805": ModelPricing(
        input_price=15.00,
        output_price=75.00,
        cache_write_price=18.75,
        cache_read_price=1.50
    ),
    # Claude Opus 4 (deprecated but still available)
    "claude-opus-4-20241022": ModelPricing(
        input_price=15.00,
        output_price=75.00,
        cache_write_price=18.75,
        cache_read_price=1.50
    ),
    # Claude Sonnet 4.5
    "claude-sonnet-4-5-20250929": ModelPricing(
        input_price=3.00,
        output_price=15.00,
        cache_write_price=3.75,
        cache_read_price=0.30
    ),
    # Claude Sonnet 4
    "claude-sonnet-4-20250514": ModelPricing(
        input_price=3.00,
        output_price=15.00,
        cache_write_price=3.75,
        cache_read_price=0.30
    ),
    # Claude Sonnet 3.7
    "claude-3-7-sonnet-20250219": ModelPricing(
        input_price=3.00,
        output_price=15.00,
        cache_write_price=3.75,
        cache_read_price=0.30
    ),
    # Claude Sonnet 3.5 (deprecated)
    "claude-3-5-sonnet-20241022": ModelPricing(
        input_price=3.00,
        output_price=15.00,
        cache_write_price=3.75,
        cache_read_price=0.30
    ),
    # Claude Haiku 3.5
    "claude-3-5-haiku-20241022": ModelPricing(
        input_price=0.80,
        output_price=4.00,
        cache_write_price=1.00,
        cache_read_price=0.08
    ),
    # Claude Opus 3 (deprecated)
    "claude-3-opus-20240229": ModelPricing(
        input_price=15.00,
        output_price=75.00,
        cache_write_price=18.75,
        cache_read_price=1.50
    ),
    # Claude Haiku 3 (deprecated)
    "claude-3-haiku-20240307": ModelPricing(
        input_price=0.25,
        output_price=1.25,
        cache_write_price=0.30,
        cache_read_price=0.03
    ),
}

# OpenAI Pricing (as of 2025-10-03)
# Note: OpenAI doesn't have separate cache pricing yet
OPENAI_PRICING: Dict[str, ModelPricing] = {
    # GPT-5 series (estimated - update when official pricing released)
    "gpt-5": ModelPricing(
        input_price=10.00,  # Estimated
        output_price=30.00   # Estimated
    ),
    "gpt-5-mini": ModelPricing(
        input_price=3.00,   # Estimated
        output_price=9.00    # Estimated
    ),
    "gpt-5-nano": ModelPricing(
        input_price=1.00,   # Estimated
        output_price=3.00    # Estimated
    ),
    # GPT-4.1 series (estimated - update when official pricing released)
    "gpt-4.1": ModelPricing(
        input_price=5.00,   # Estimated
        output_price=15.00   # Estimated
    ),
    "gpt-4.1-mini": ModelPricing(
        input_price=2.00,   # Estimated
        output_price=6.00    # Estimated
    ),
    "gpt-4.1-nano": ModelPricing(
        input_price=0.50,   # Estimated
        output_price=1.50    # Estimated
    ),
    # GPT-4o series
    "gpt-4o": ModelPricing(
        input_price=5.00,
        output_price=15.00
    ),
    "gpt-4o-mini": ModelPricing(
        input_price=0.15,
        output_price=0.60
    ),
    # GPT-4 Turbo
    "gpt-4-turbo": ModelPricing(
        input_price=10.00,
        output_price=30.00
    ),
    # GPT-4
    "gpt-4": ModelPricing(
        input_price=30.00,
        output_price=60.00
    ),
    # GPT-3.5 Turbo
    "gpt-3.5-turbo": ModelPricing(
        input_price=0.50,
        output_price=1.50
    ),
}

# Google Gemini Pricing (as of 2025-10-03)
GEMINI_PRICING: Dict[str, ModelPricing] = {
    # Gemini 2.5 Pro
    "gemini-2.5-pro": ModelPricing(
        input_price=1.25,    # Estimated
        output_price=5.00     # Estimated
    ),
    # Gemini 2.5 Flash
    "gemini-2.5-flash": ModelPricing(
        input_price=0.075,   # Free tier: 1500 requests/day
        output_price=0.30     # After free tier
    ),
    # Gemini 2.5 Flash-Lite
    "gemini-2.5-flash-lite": ModelPricing(
        input_price=0.04,    # Estimated
        output_price=0.15     # Estimated
    ),
    # Gemini 2.0 Flash
    "gemini-2.0-flash-001": ModelPricing(
        input_price=0.10,    # Estimated
        output_price=0.40     # Estimated
    ),
    # Gemini 2.0 Flash-Lite
    "gemini-2.0-flash-lite-001": ModelPricing(
        input_price=0.05,    # Estimated
        output_price=0.20     # Estimated
    ),
    # Legacy models
    "gemini-1.5-pro": ModelPricing(
        input_price=1.25,
        output_price=5.00
    ),
    "gemini-1.5-flash": ModelPricing(
        input_price=0.075,
        output_price=0.30
    ),
}

# Unified pricing lookup
MODEL_PRICING: Dict[str, Dict[str, ModelPricing]] = {
    "anthropic": ANTHROPIC_PRICING,
    "openai": OPENAI_PRICING,
    "gemini": GEMINI_PRICING,
}


def get_model_pricing(provider: str, model: str) -> Optional[ModelPricing]:
    """
    Get pricing information for a specific model.

    Args:
        provider: Provider name (anthropic, openai, gemini)
        model: Model identifier

    Returns:
        ModelPricing object if found, None otherwise
    """
    provider_lower = provider.lower()

    if provider_lower in MODEL_PRICING:
        return MODEL_PRICING[provider_lower].get(model)

    return None


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0
) -> Optional[float]:
    """
    Calculate cost for a given token usage.

    Args:
        provider: Provider name (anthropic, openai, gemini)
        model: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cache_write_tokens: Number of cache write tokens (optional)
        cache_read_tokens: Number of cache read tokens (optional)

    Returns:
        Total cost in USD, or None if pricing not found
    """
    pricing = get_model_pricing(provider, model)

    if not pricing:
        return None

    return pricing.calculate_cost(
        input_tokens,
        output_tokens,
        cache_write_tokens,
        cache_read_tokens
    )


def format_cost(cost: float) -> str:
    """
    Format cost for display.

    Args:
        cost: Cost in USD

    Returns:
        Formatted cost string
    """
    if cost < 0.0001:
        return f"${cost:.6f}"  # Show more decimals for very small costs
    elif cost < 0.01:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"
