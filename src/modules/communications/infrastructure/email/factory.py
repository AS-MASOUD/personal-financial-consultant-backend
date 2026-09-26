from src.app.core.settings import Settings, get_settings
from src.modules.communications.infrastructure.email.base import BaseEmailProvider
from src.modules.communications.infrastructure.email.mock_provider import MockEmailProvider
from src.modules.communications.infrastructure.email.smtp import SMTPEmailProvider

_email_instance: BaseEmailProvider | None = None


def get_email_provider(settings: Settings | None = None) -> BaseEmailProvider:
    global _email_instance
    if _email_instance is not None:
        return _email_instance

    if settings is None:
        settings = get_settings()

    provider_name = settings.EMAIL_PROVIDER.lower().strip()

    if provider_name == "smtp":
        _email_instance = SMTPEmailProvider(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            from_email=settings.SMTP_FROM_EMAIL,
            use_tls=settings.SMTP_USE_TLS,
        )
    else:
        _email_instance = MockEmailProvider()

    return _email_instance
