from src.app.core.settings import Settings, get_settings
from src.modules.communications.infrastructure.sms.base import BaseSMSProvider
from src.modules.communications.infrastructure.sms.farazsms import FarazSMSProvider
from src.modules.communications.infrastructure.sms.kavenegar import KavenegarSMSProvider
from src.modules.communications.infrastructure.sms.mock_provider import MockSMSProvider

_sms_instance: BaseSMSProvider | None = None


def get_sms_provider(settings: Settings | None = None) -> BaseSMSProvider:
    global _sms_instance
    if _sms_instance is not None:
        return _sms_instance

    if settings is None:
        settings = get_settings()

    provider_name = settings.SMS_PROVIDER.lower().strip()

    if provider_name == "kavenegar":
        _sms_instance = KavenegarSMSProvider(
            api_key=settings.KAVENEGAR_API_KEY,
            sender=settings.KAVENEGAR_SENDER,
        )
    elif provider_name in ("farazsms", "ippanel"):
        _sms_instance = FarazSMSProvider(
            api_key=settings.FARAZSMS_API_KEY,
            sender=settings.FARAZSMS_SENDER,
            pattern_code=settings.FARAZSMS_PATTERN_CODE,
        )
    else:
        _sms_instance = MockSMSProvider()

    return _sms_instance
