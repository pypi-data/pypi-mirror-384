"""LLM configuration for agents (SDK version)."""

from typing import Optional


class LLMConfig:
    """Configuration for LLM generation parameters.

    Note: Model selection, API keys, and base URLs are managed by the platform.
    SDK users can only configure generation parameters.

    Attributes:
        temperature: Sampling temperature (0.0 to 2.0, default 0.7)
        max_tokens: Maximum tokens to generate (optional)
        top_p: Nucleus sampling parameter (0.0-1.0, optional)
        frequency_penalty: Reduce repetition (-2.0 to 2.0, optional)
        presence_penalty: Encourage topic diversity (-2.0 to 2.0, optional)

    Example:
        >>> config = LLMConfig(
        ...     temperature=0.7,
        ...     max_tokens=2000,
        ...     top_p=0.9
        ... )
    """

    def __init__(
        self,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
    ):
        """Initialize LLM configuration.

        Args:
            temperature: Sampling temperature between 0.0 and 2.0
            max_tokens: Maximum tokens to generate (optional)
            top_p: Nucleus sampling parameter (optional)
            frequency_penalty: Repetition penalty (optional)
            presence_penalty: Topic diversity penalty (optional)

        Raises:
            ValueError: If parameters are out of valid range
        """
        if not (0.0 <= temperature <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if top_p is not None and not (0.0 <= top_p <= 1.0):
            raise ValueError("top_p must be between 0.0 and 1.0")
        if frequency_penalty is not None and not (-2.0 <= frequency_penalty <= 2.0):
            raise ValueError("frequency_penalty must be between -2.0 and 2.0")
        if presence_penalty is not None and not (-2.0 <= presence_penalty <= 2.0):
            raise ValueError("presence_penalty must be between -2.0 and 2.0")

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

    def __repr__(self) -> str:
        """Return string representation."""
        return f"LLMConfig(temperature={self.temperature}, max_tokens={self.max_tokens})"
