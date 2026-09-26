import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.app.observability.logging import get_logger
from src.modules.communications.infrastructure.email.base import BaseEmailProvider

logger = get_logger("email.smtp")


class SMTPEmailProvider(BaseEmailProvider):
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    async def send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self.host or not self.username:
            logger.warning("SMTP host or credentials not configured; skipping email.")
            return False

        def _send() -> bool:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            part = MIMEText(html_body, "html", "utf-8")
            msg.attach(part)

            try:
                server = smtplib.SMTP(self.host, self.port, timeout=10)
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.from_email, [to_email], msg.as_string())
                server.quit()
                return True
            except Exception as e:
                logger.exception("Failed to send email via SMTP", error=str(e))
                return False

        return await asyncio.to_thread(_send)
