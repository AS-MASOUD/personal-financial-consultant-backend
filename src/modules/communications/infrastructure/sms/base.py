from abc import ABC, abstractmethod


class BaseSMSProvider(ABC):
    """Abstract interface for SMS gateway providers (Supports Iranian providers such as Kavenegar, FarazSMS, etc.)."""

    @abstractmethod
    async def send_sms(self, phone_number: str, message: str) -> bool:
        """Send regular text SMS message."""
        pass

    @abstractmethod
    async def send_otp_pattern(
        self, phone_number: str, code: str, template: str | None = None
    ) -> bool:
        """Send OTP verification code using provider-approved pattern/template (for fast delivery in Iran without blocking)."""
        pass
