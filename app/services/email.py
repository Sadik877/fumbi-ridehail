from flask import current_app
from flask_mail import Message

from app.extensions import mail


def send_email(to: str, subject: str, body: str) -> None:
    """Sends transactional email (password reset, verification, receipts).

    Falls back to logging the message when MAIL_SUPPRESS_SEND is true
    (the default) so registration/reset flows work end-to-end in every
    environment before real SMTP credentials are configured."""
    if current_app.config.get("MAIL_SUPPRESS_SEND", True):
        current_app.logger.info("[email suppressed] to=%s subject=%s\n%s", to, subject, body)
        return
    msg = Message(subject=subject, recipients=[to], body=body)
    mail.send(msg)
