"""Tests for merchant parser detection, extraction, and plugin auto-discovery."""

from __future__ import annotations

from importer.parsers import detect, get_parsers


def test_registry_discovers_all_twelve_merchant_parsers():
    names = {parser.name for parser in get_parsers()}
    assert names == {
        "Amazon",
        "eBay",
        "Otto",
        "MediaMarkt",
        "Saturn",
        "IKEA",
        "Temu",
        "Kaufland",
        "AliExpress",
        "Decathlon",
        "Zalando",
        "Alternate",
    }


def test_unrecognized_sender_is_not_detected(make_email):
    email = make_email("noreply@some-random-shop.example", "Your order", "no useful content here")
    assert detect(email) is None


def test_amazon(make_email):
    email = make_email(
        "versand@amazon.de",
        "Ihre Bestellung wurde versandt",
        "Bestellnummer: 302-1234567-1234567\n"
        "Gesamtbetrag: 29,99 EUR\n"
        "Ihre Sendungsverfolgungsnummer lautet: 1Z999AA10123456784",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "Amazon"
    assert order.order_number == "302-1234567-1234567"
    assert order.invoice_amount == "29,99"
    assert order.currency == "EUR"
    assert order.tracking_numbers == ["1Z999AA10123456784"]
    assert order.carrier_hint == "UPS"


def test_ebay(make_email):
    email = make_email(
        "ebay@ebay.de",
        "Dein Artikel wurde versendet",
        "Bestellnummer: 12-34567-56789\nSendungsnummer: 123456789012",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "eBay"
    assert order.order_number == "12-34567-56789"
    assert order.tracking_numbers == ["123456789012"]
    assert order.carrier_hint == "DHL"


def test_otto(make_email):
    email = make_email(
        "service@otto.de",
        "Ihre Bestellung ist unterwegs",
        "Bestellnummer: 123456789\nTracking: 12345678901234",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "Otto"
    assert order.order_number == "123456789"
    assert order.carrier_hint == "DPD"


def test_mediamarkt(make_email):
    email = make_email(
        "service@mediamarkt.de",
        "Deine Bestellung wurde versendet",
        "Bestellnummer: DE12345678\nSendungsverfolgung: 12345678901",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "MediaMarkt"
    assert order.order_number == "DE12345678"
    assert order.carrier_hint == "GLS"


def test_saturn(make_email):
    email = make_email(
        "service@saturn.de",
        "Deine Bestellung wurde versendet",
        "Bestellnummer: DE87654321\nSendungsverfolgung: H1234567890",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "Saturn"
    assert order.order_number == "DE87654321"
    assert order.carrier_hint == "Hermes"


def test_ikea(make_email):
    email = make_email(
        "no-reply@ikea.de",
        "Deine IKEA Bestellung",
        "Bestellnummer: 123.456.78\nTracking: TBA123456789012",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "IKEA"
    assert order.order_number == "123.456.78"
    assert order.carrier_hint == "Amazon Logistics"


def test_temu(make_email):
    email = make_email(
        "order@temu.com",
        "Your Temu order has shipped",
        "Order ID: PO-123456789012345\nTracking number: YT1234567890123456",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "Temu"
    assert order.order_number == "PO-123456789012345"
    assert order.carrier_hint == "YunExpress"


def test_kaufland(make_email):
    email = make_email(
        "service@kaufland.de",
        "Ihre Bestellung ist unterwegs",
        "Bestellnummer: KL-2026-000123456\nTracking: 987654321098",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "Kaufland"
    assert order.order_number == "KL-2026-000123456"
    assert order.carrier_hint == "DHL"


def test_aliexpress(make_email):
    email = make_email(
        "noreply@aliexpress.com",
        "Your order has been shipped",
        "Order number: 812345678901234567\nTracking: LP00123456789012",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "AliExpress"
    assert order.order_number == "812345678901234567"
    assert order.carrier_hint == "Cainiao"


def test_decathlon(make_email):
    email = make_email(
        "service@decathlon.de",
        "Deine Bestellung wurde versendet",
        "Bestellnummer: DEC123456789\nTracking: 12345678901",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "Decathlon"
    assert order.order_number == "DEC123456789"
    assert order.carrier_hint == "GLS"


def test_zalando(make_email):
    email = make_email(
        "versand@zalando.de",
        "Deine Bestellung ist unterwegs",
        "Bestellnummer: 123456789\nTracking: 1234567890",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "Zalando"
    assert order.order_number == "123456789"
    assert order.carrier_hint == "DHL"


def test_alternate(make_email):
    email = make_email(
        "versand@alternate.de",
        "Deine Bestellung wurde versendet",
        "Bestellnummer: 1234567\nTracking: 1Z888AA10123456785",
    )
    order = detect(email)
    assert order is not None
    assert order.merchant == "Alternate"
    assert order.order_number == "1234567"
    assert order.carrier_hint == "UPS"
