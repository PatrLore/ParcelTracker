"""Carrier schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CarrierBase(BaseModel):
    name: str
    api_identifier: str | None = None
    tracking_url_template: str | None = None
    logo_url: str | None = None


class CarrierCreate(CarrierBase):
    pass


class CarrierRead(CarrierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
