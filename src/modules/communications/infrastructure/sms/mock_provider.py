from src.app.observability.logging import get_logger
from src.modules.communications.infrastructure.sms.base import BaseSMSProvider

logger = get_logger("sms.mock")


class MockSMSProvider(BaseSMSProvider):
    """Development / Testing SMS Provider. Logs messages to console & system logs."""

    def __init__(self):
        self.sent_messages: list[dict[str, str]] = []

    async def send_sms(self, phone_number: str, message: str) -> bool:
        logger.info(
            "[DEV/MOCK SMS SENT]",
            phone=phone_number,
            message=message,
        )
        self.sent_messages.append({"phone": phone_number, "message": message, "type": "sms"})
        return True

    async def send_otp_pattern(
        self, phone_number: str, code: str, template: str | None = None
    ) -> bool:
        logger.info(
            "==================================================",
            phone=phone_number,
            otp_code=code,
            template=template or "default_otp",
        )
        logger.info(f"🔑 [MOCK OTP CODE DISPATCHED] Phone: {phone_number} | Code: {code}")
        logger.info("==================================================")
        self.sent_messages.append(
            {"phone": phone_number, "code": code, "template": template or "default", "type": "otp"}
        )
        return True
