import httpx

from src.app.observability.logging import get_logger
from src.modules.communications.infrastructure.sms.base import BaseSMSProvider

logger = get_logger("sms.farazsms")


class FarazSMSProvider(BaseSMSProvider):
    """Iranian SMS Gateway Provider: FarazSMS / IPPanel (فراز اس‌ام‌اس / آی‌پی‌پنل)

    Uses IPPanel REST API for fast pattern-based verification and SMS sending.
    """

    def __init__(self, api_key: str, sender: str = "", pattern_code: str = ""):
        self.api_key = api_key
        self.sender = sender
        self.pattern_code = pattern_code
        self.base_url = "https://api2.ippanel.com/api/v1"

    async def send_sms(self, phone_number: str, message: str) -> bool:
        if not self.api_key:
            logger.warning("FarazSMS API key not configured; skipping SMS send.")
            return False

        url = f"{self.base_url}/sms/send/webservice/single"
        headers = {"apikey": self.api_key}
        payload = {
            "recipient": [phone_number],
            "sender": self.sender,
            "message": message,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code in (200, 201):
                    logger.info("SMS sent via FarazSMS", phone=phone_number)
                    return True
                logger.error("FarazSMS send error", status_code=res.status_code, body=res.text)
                return False
        except Exception as e:
            logger.exception("Failed to connect to FarazSMS API", error=str(e))
            return False

    async def send_otp_pattern(
        self, phone_number: str, code: str, template: str | None = None
    ) -> bool:
        if not self.api_key:
            logger.warning("FarazSMS API key not configured; skipping OTP pattern send.")
            return False

        pattern = template or self.pattern_code
        url = f"{self.base_url}/sms/pattern/normal/send"
        headers = {"apikey": self.api_key}
        payload = {
            "code": pattern,
            "sender": self.sender,
            "recipient": phone_number,
            "values": {"code": code},
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code in (200, 201):
                    logger.info("OTP pattern sent via FarazSMS", phone=phone_number)
                    return True
                logger.error("FarazSMS OTP pattern error", status_code=res.status_code, body=res.text)
                return False
        except Exception as e:
            logger.exception("Failed to send OTP via FarazSMS", error=str(e))
            return False
