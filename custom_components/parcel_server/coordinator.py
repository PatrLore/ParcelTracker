"""Polls the Parcel Server backend and derives the values every sensor reads."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ParcelServerApiClient, ParcelServerError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

#: Shipment statuses that no longer need to be considered for "next delivery".
_TERMINAL_STATUSES = {"delivered", "returned"}


@dataclass
class NextOrLastDelivery:
    """The shipment nearest to (or most recently at) delivery, plus the
    order-level context Home Assistant shows as sensor attributes."""

    date: date | None = None
    merchant: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    order_id: int | None = None
    shipment_id: int | None = None


class ParcelServerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches dashboard/statistics summaries plus the order list once per
    interval, and derives next/last delivery from the order list client-side
    (the backend doesn't expose a single "next delivery" endpoint scoped to
    one user - see ``docs/architecture.md``)."""

    def __init__(self, hass: HomeAssistant, client: ParcelServerApiClient) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=DEFAULT_SCAN_INTERVAL)
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            dashboard = await self.client.async_get_dashboard_summary()
            statistics = await self.client.async_get_statistics_summary()
            orders = await self.client.async_list_orders(limit=200)
        except ParcelServerError as exc:
            raise UpdateFailed(str(exc)) from exc

        return {
            "dashboard": dashboard,
            "statistics": statistics,
            "next_delivery": _find_next_delivery(orders),
            "last_delivery": _find_last_delivery(orders),
        }


def _find_next_delivery(orders: list[dict[str, Any]]) -> NextOrLastDelivery:
    """Soonest ``estimated_delivery_date`` among non-terminal shipments."""
    best: NextOrLastDelivery | None = None
    for order in orders:
        for shipment in order.get("shipments", []):
            if shipment.get("tracking_status") in _TERMINAL_STATUSES:
                continue
            estimated = _parse_date(shipment.get("estimated_delivery_date"))
            if estimated is None:
                continue
            if best is None or estimated < best.date:
                best = _to_delivery(order, shipment, estimated)
    return best or NextOrLastDelivery()


def _find_last_delivery(orders: list[dict[str, Any]]) -> NextOrLastDelivery:
    """Most recent ``delivery_date`` among delivered shipments."""
    best: NextOrLastDelivery | None = None
    for order in orders:
        for shipment in order.get("shipments", []):
            if shipment.get("tracking_status") != "delivered":
                continue
            delivered = _parse_date(shipment.get("delivery_date"))
            if delivered is None:
                continue
            if best is None or delivered > best.date:
                best = _to_delivery(order, shipment, delivered)
    return best or NextOrLastDelivery()


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _to_delivery(
    order: dict[str, Any], shipment: dict[str, Any], the_date: date
) -> NextOrLastDelivery:
    carrier = shipment.get("carrier")
    return NextOrLastDelivery(
        date=the_date,
        merchant=order.get("merchant"),
        carrier=carrier.get("name") if carrier else None,
        tracking_number=shipment.get("tracking_number"),
        order_id=order.get("id"),
        shipment_id=shipment.get("id"),
    )
