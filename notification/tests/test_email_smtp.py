"""Tests for the SMTP email channel, using a fake SMTP client (no real
network/SMTP connection)."""

from __future__ import annotations

from notification.channels.email_smtp import EmailChannel
from notification.message import NotificationMessage


class FakeSmtpClient:
    instances: list[FakeSmtpClient] = []

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.started_tls = False
        self.login_calls: list[tuple[str, str]] = []
        self.sent_messages = []
        FakeSmtpClient.instances.append(self)

    def starttls(self) -> None:
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        self.login_calls.append((username, password))

    def send_message(self, message) -> None:
        self.sent_messages.append(message)

    def __enter__(self) -> FakeSmtpClient:
        return self

    def __exit__(self, *exc_info) -> None:
        pass


def test_email_channel_sends_via_smtp():
    FakeSmtpClient.instances.clear()
    channel = EmailChannel(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="bot@example.com",
        password="secret",
        from_address="bot@example.com",
        to_address="you@example.com",
        smtp_client_factory=FakeSmtpClient,
    )
    message = NotificationMessage(
        event="new_confirmation", title="New order", body="Amazon order placed."
    )

    channel.send(message)

    client = FakeSmtpClient.instances[0]
    assert client.host == "smtp.example.com"
    assert client.started_tls is True
    assert client.login_calls == [("bot@example.com", "secret")]
    assert len(client.sent_messages) == 1
    assert client.sent_messages[0]["Subject"] == "New order"
    assert client.sent_messages[0]["To"] == "you@example.com"


def test_email_channel_skips_login_without_credentials():
    FakeSmtpClient.instances.clear()
    channel = EmailChannel(
        smtp_host="smtp.example.com",
        smtp_port=25,
        username="",
        password="",
        from_address="bot@example.com",
        to_address="you@example.com",
        use_tls=False,
        smtp_client_factory=FakeSmtpClient,
    )

    channel.send(NotificationMessage(event="x", title="x", body="x"))

    client = FakeSmtpClient.instances[0]
    assert client.started_tls is False
    assert client.login_calls == []
