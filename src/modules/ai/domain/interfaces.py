from typing import Any, Protocol


class IAIProvider(Protocol):
    """Abstract port for AI models interpreting deterministic financial analytics."""

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        tools_context: dict[str, Any] | None = None,
    ) -> str:
        """Synthesize financial guidance given chat history and structured tool data."""
        ...
