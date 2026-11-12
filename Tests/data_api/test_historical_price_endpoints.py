import uuid

from app.models.historical_price import HistoricalPrice
from sqlalchemy import select


def create_instrument(client):
    response = client.post(
        "/api/v1/instruments",
        json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
            "quote_currency": "USD",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_save_historical_prices(client, db_session):
    instrument_id = create_instrument(client)

    response = client.post(
        f"/api/v1/instruments/{instrument_id}/prices",
        json={
            "prices": [
                {
                    "price_date": "2026-01-01",
                    "close_price": "150.25",
                    "currency": "USD",
                    "source": "provider_a",
                },
                {
                    "price_date": "2026-01-02",
                    "close_price": "155.50",
                    "currency": "USD",
                    "source": "provider_a",
                },
            ]
        },
    )

    assert response.status_code == 204

    prices = db_session.scalars(
        select(HistoricalPrice).where(HistoricalPrice.instrument_id == uuid.UUID(instrument_id))
    ).all()

    assert len(prices) == 2


def test_save_prices_updates_existing_record(client, db_session):
    instrument_id = create_instrument(client)

    payload = {
        "prices": [
            {
                "price_date": "2026-01-01",
                "close_price": "150.00",
                "currency": "USD",
                "source": "provider_a",
            }
        ]
    }

    first_response = client.post(
        f"/api/v1/instruments/{instrument_id}/prices",
        json=payload,
    )

    assert first_response.status_code == 204

    payload["prices"][0]["close_price"] = "160.00"

    second_response = client.post(
        f"/api/v1/instruments/{instrument_id}/prices",
        json=payload,
    )

    assert second_response.status_code == 204

    prices = db_session.scalars(
        select(HistoricalPrice).where(HistoricalPrice.instrument_id == uuid.UUID(instrument_id))
    ).all()

    assert len(prices) == 1
    assert str(prices[0].close_price) == "160.00000000"


def test_save_prices_with_currency_mismatch_returns_422(client):
    instrument_id = create_instrument(client)

    response = client.post(
        f"/api/v1/instruments/{instrument_id}/prices",
        json={
            "prices": [
                {
                    "price_date": "2026-01-01",
                    "close_price": "150.25",
                    "currency": "PLN",
                    "source": "provider_a",
                }
            ]
        },
    )

    assert response.status_code == 422


def test_save_prices_for_nonexistent_instrument_returns_404(client):
    response = client.post(
        f"/api/v1/instruments/{uuid.uuid4()}/prices",
        json={"prices": []},
    )

    assert response.status_code == 404


def test_save_prices_rejects_non_positive_price(client):
    instrument_id = create_instrument(client)

    response = client.post(
        f"/api/v1/instruments/{instrument_id}/prices",
        json={
            "prices": [
                {
                    "price_date": "2026-01-01",
                    "close_price": "0",
                    "currency": "USD",
                    "source": "provider_a",
                }
            ]
        },
    )

    assert response.status_code == 422


def test_save_prices_rejects_invalid_batch(client):
    instrument_id = create_instrument(client)

    response = client.post(
        f"/api/v1/instruments/{instrument_id}/prices",
        json={
            "prices": [
                {
                    "price_date": "2026-01-01",
                    "close_price": "150.25",
                    "currency": "USD",
                    "source": "provider_a",
                },
                {
                    "price_date": "2026-01-01",
                    "close_price": "151.25",
                    "currency": "USD",
                    "source": "provider_a",
                },
            ]
        },
    )

    assert response.status_code == 422


def test_get_historical_prices(client):
    instrument_id = create_instrument(client)

    client.post(
        f"/api/v1/instruments/{instrument_id}/prices",
        json={
            "prices": [
                {
                    "price_date": "2026-01-01",
                    "close_price": "150.25",
                    "currency": "USD",
                    "source": "provider_a",
                },
                {
                    "price_date": "2026-01-02",
                    "close_price": "155.50",
                    "currency": "USD",
                    "source": "provider_a",
                },
            ]
        },
    )

    response = client.get(
        f"/api/v1/instruments/{instrument_id}/prices",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-02",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["price_date"] == "2026-01-01"
    assert data[1]["price_date"] == "2026-01-02"


def test_get_historical_prices_rejects_invalid_date_range(client):
    instrument_id = create_instrument(client)

    response = client.get(
        f"/api/v1/instruments/{instrument_id}/prices",
        params={
            "start_date": "2026-01-31",
            "end_date": "2026-01-01",
        },
    )

    assert response.status_code == 422


def test_get_historical_prices_for_nonexistent_instrument_returns_404(
    client,
):
    response = client.get(
        f"/api/v1/instruments/{uuid.uuid4()}/prices",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        },
    )

    assert response.status_code == 404


def test_invalid_batch_does_not_save_any_prices(client, db_session):
    instrument_id = create_instrument(client)

    response = client.post(
        f"/api/v1/instruments/{instrument_id}/prices",
        json={
            "prices": [
                {
                    "price_date": "2026-01-01",
                    "close_price": "150.25",
                    "currency": "USD",
                    "source": "provider_a",
                },
                {
                    "price_date": "2026-01-02",
                    "close_price": "155.50",
                    "currency": "PLN",
                    "source": "provider_a",
                },
            ]
        },
    )

    assert response.status_code == 422

    prices = db_session.scalars(
        select(HistoricalPrice).where(HistoricalPrice.instrument_id == uuid.UUID(instrument_id))
    ).all()

    assert prices == []
