"""Email delivery adapter (stub for portfolio — SMTP-ready interface)."""

from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class EmailMessage:
    to_email: str
    subject: str
    body: str


class EmailSender:
    """Abstract email sender — replace with SMTP/SendGrid in production."""

    async def send(self, message: EmailMessage) -> bool:
        raise NotImplementedError


class StubEmailSender(EmailSender):
    """Logs email instead of sending — suitable for dev and portfolio demos."""

    async def send(self, message: EmailMessage) -> bool:
        logger.info(
            "email.stub_sent",
            to=message.to_email,
            subject=message.subject,
            body_preview=message.body[:120],
        )
        return True
