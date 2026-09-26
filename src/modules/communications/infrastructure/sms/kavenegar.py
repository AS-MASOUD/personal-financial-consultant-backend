import httpx

from src.app.observability.logging import get_logger
from src.modules.communications.infrastructure.sms.base import BaseSMSProvider

logger = get_logger("sms.kavenegar")


class KavenegarSMSProvider(BaseSMSProvider):
    """Iranian SMS Gateway Provider: Kavenegar (کاوه نگار)

    Uses Kavenegar REST API for sending OTP patterns and standard SMS messages.
    """

    def __init__(self, api_key: str, sender: str = ""):
        self.api_key = api_key
        self.sender = sender
        self.base_url = f"https://api.kavenegar.com/v1/{api_key}"

    async def send_sms(self, phone_number: str, message: str) -> bool:
        if not self.api_key:
            logger.warning("Kavenegar API key not configured; skipping SMS send.")
            return False

        url = f"{self.base_url}/sms/send.json"
        params = {
            "receptor": phone_number,
            "message": message,
        }
        if self.sender:
            params["sender"] = self.sender

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, data=params)
                data = res.json()
                status = data.get("return", {}).get("status", 0)
                if status == 200:
                    logger.info("SMS sent via Kavenegar", phone=phone_number)
                    return True
                logger.error("Kavenegar SMS send error", response=data)
                return False
        except Exception as e:
            logger.exception("Failed to connect to Kavenegar API", error=str(e))
            return False

    async def send_otp_pattern(
        self, phone_number: str, code: str, template: str | None = None
    ) -> bool:
        if not self.api_key:
            logger.warning("Kavenegar API key not configured; skipping OTP pattern send.")
            return False

        url = f"{self.base_url}/verify/lookup.json"
        params = {
            "receptor": phone_number,
            "token": code,
            "template": template or "verify",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, data=params)
                data = res.json()
                status = data.get("return", {}).get("status", 0)
                if status == 200:
                    logger.info("OTP pattern sent via Kavenegar", phone=phone_number)
                    return True
                logger.error("Kavenegar OTP pattern send error", response=data)
                return False
        except Exception as e:
            logger.exception("Failed to send OTP via Kavenegar", error=str(e))
            return False
