"""Tests that every request is logged through our own logger (and thus the
rotating file handler), not left to Uvicorn's separate access log."""

from __future__ import annotations

import logging


def test_request_is_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.main"):
        response = client.get("/health")

    assert response.status_code == 200
    assert any("GET /health -> 200" in record.getMessage() for record in caplog.records)
