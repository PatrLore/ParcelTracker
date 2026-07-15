"""Tests for the update-check service. Uses httpx.MockTransport - no real
network calls - matching the convention in tracking/tests/test_providers.py."""

from __future__ import annotations

import httpx
import pytest

from app.services import version_service


def _client_with(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def _clear_cache():
    version_service._cache.clear()
    yield
    version_service._cache.clear()


def test_reports_update_available_when_commits_differ(monkeypatch):
    monkeypatch.setattr(version_service, "get_running_commit", lambda: "aaaa111")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"sha": "bbbb222"})

    info = version_service.get_version_info(_client_with(handler))

    assert info.current_commit == "aaaa111"
    assert info.latest_commit == "bbbb222"
    assert info.update_available is True
    assert info.compare_url == "https://github.com/PatrLore/ParcelTracker/compare/aaaa111...bbbb222"
    assert info.check_failed is False


def test_reports_up_to_date_when_commits_match(monkeypatch):
    monkeypatch.setattr(version_service, "get_running_commit", lambda: "aaaa111")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"sha": "aaaa111"})

    info = version_service.get_version_info(_client_with(handler))

    assert info.update_available is False


def test_reports_check_failed_on_network_error(monkeypatch):
    monkeypatch.setattr(version_service, "get_running_commit", lambda: "aaaa111")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    info = version_service.get_version_info(_client_with(handler))

    assert info.latest_commit is None
    assert info.update_available is False
    assert info.check_failed is True


def test_reports_no_update_when_running_commit_unknown(monkeypatch):
    monkeypatch.setattr(version_service, "get_running_commit", lambda: None)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"sha": "bbbb222"})

    info = version_service.get_version_info(_client_with(handler))

    assert info.current_commit is None
    assert info.update_available is False
    assert info.check_failed is False


def test_caches_latest_commit_within_ttl(monkeypatch):
    monkeypatch.setattr(version_service, "get_running_commit", lambda: "aaaa111")
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"sha": "bbbb222"})

    version_service.get_version_info(_client_with(handler))
    version_service.get_version_info(_client_with(handler))

    assert call_count == 1
