"""Tests for the HTTP-based notification channels (webhook, Discord,
Telegram, Signal). Each test injects an ``httpx.Client`` backed by
``httpx.MockTransport`` - no real network calls are made."""

from __future__ import annotations

import httpx
from notification.channels.discord import DiscordChannel
from notification.channels.signal import SignalChannel
from notification.channels.telegram import TelegramChannel
from notification.channels.webhook import WebhookChannel
from notification.message import NotificationMessage

_MESSAGE = NotificationMessage(
    event="shipment_delivered",
    title="Parcel delivered",
    body="Your Amazon parcel has been delivered.",
    metadata={"tracking_number": "1Z999AA10123456784"},
)


def test_webhook_channel_posts_json_payload():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        return httpx.Response(200)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    channel = WebhookChannel(url="https://example.com/hook", client=client)

    channel.send(_MESSAGE)

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/hook"
    assert b"shipment_delivered" in captured["body"]


def test_discord_channel_posts_content():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        return httpx.Response(204)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    channel = DiscordChannel(webhook_url="https://discord.com/api/webhooks/x/y", client=client)

    channel.send(_MESSAGE)

    assert captured["url"] == "https://discord.com/api/webhooks/x/y"
    assert b"Parcel delivered" in captured["body"]


def test_telegram_channel_sends_to_configured_chat():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(
        base_url="https://api.telegram.org/bottest-token",
        transport=httpx.MockTransport(handler),
    )
    channel = TelegramChannel(bot_token="test-token", chat_id="12345", client=client)

    channel.send(_MESSAGE)

    assert captured["url"].endswith("/sendMessage")
    assert b'"chat_id":"12345"' in captured["body"]


def test_signal_channel_sends_via_rest_api():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        return httpx.Response(201)

    client = httpx.Client(
        base_url="http://signal-cli-rest-api:8080", transport=httpx.MockTransport(handler)
    )
    channel = SignalChannel(
        base_url="http://signal-cli-rest-api:8080",
        sender_number="+10000000000",
        recipient_number="+19999999999",
        client=client,
    )

    channel.send(_MESSAGE)

    assert captured["url"].endswith("/v2/send")
    assert b"+19999999999" in captured["body"]
