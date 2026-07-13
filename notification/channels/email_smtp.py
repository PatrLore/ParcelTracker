"""Email channel: sends via SMTP (stdlib ``smtplib``), independent of any
particular email-provider API."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from notification.channel import NotificationChannel
from notification.message import NotificationMessage


class EmailChannel(NotificationChannel):
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_address: str,
        to_address: str,
        use_tls: bool = True,
        smtp_client_factory: type[smtplib.SMTP] = smtplib.SMTP,
    ) -> None:
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._username = username
        self._password = password
        self._from_address = from_address
        self._to_address = to_address
        self._use_tls = use_tls
        self._smtp_client_factory = smtp_client_factory

    def send(self, message: NotificationMessage) -> None:
        email_message = EmailMessage()
        email_message["Subject"] = message.title
        email_message["From"] = self._from_address
        email_message["To"] = self._to_address
        email_message.set_content(message.body)

        with self._smtp_client_factory(self._smtp_host, self._smtp_port) as client:
            if self._use_tls:
                client.starttls()
            if self._username:
                client.login(self._username, self._password)
            client.send_message(email_message)
