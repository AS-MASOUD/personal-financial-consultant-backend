from abc import ABC, abstractmethod


class BaseEmailProvider(ABC):
    """Abstract interface for Email delivery."""

    @abstractmethod
    async def send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        pass
