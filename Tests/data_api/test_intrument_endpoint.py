def test_create_instrument(client):
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

    data = response.json()

    assert data["symbol"] == "AAPL"
    assert data["name"] == "Apple Inc."
    assert data["exchange"] == "NASDAQ"
    assert data["quote_currency"] == "USD"
    assert "id" in data


def test_create_instrument_normalizes_input(client):
    response = client.post(
        "/api/v1/instruments",
        json={
            "symbol": " aapl ",
            "name": " Apple Inc. ",
            "exchange": " nasdaq ",
            "quote_currency": "usd",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["symbol"] == "AAPL"
    assert data["name"] == "Apple Inc."
    assert data["exchange"] == "NASDAQ"
    assert data["quote_currency"] == "USD"


def test_create_duplicate_instrument_returns_conflict(client):
    payload = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "quote_currency": "USD",
    }

    first_response = client.post("/api/v1/instruments", json=payload)
    second_response = client.post("/api/v1/instruments", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_create_instrument_rejects_unsupported_currency(client):
    response = client.post(
        "/api/v1/instruments",
        json={
            "symbol": "ABC",
            "name": "Example Company",
            "exchange": "NYSE",
            "quote_currency": "CHF",
        },
    )

    assert response.status_code == 422


def test_create_instrument_rejects_missing_fields(client):
    response = client.post(
        "/api/v1/instruments",
        json={
            "symbol": "AAPL",
        },
    )

    assert response.status_code == 422


def test_get_existing_instrument(client):
    create_response = client.post(
        "/api/v1/instruments",
        json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
            "quote_currency": "USD",
        },
    )

    instrument_id = create_response.json()["id"]

    response = client.get(f"/api/v1/instruments/{instrument_id}")

    assert response.status_code == 200
    assert response.json()["id"] == instrument_id


def test_get_nonexistent_instrument_returns_not_found(client):
    import uuid

    response = client.get(f"/api/v1/instruments/{uuid.uuid4()}")

    assert response.status_code == 404


def test_get_instrument_rejects_invalid_uuid(client):
    response = client.get("/api/v1/instruments/not-a-uuid")

    assert response.status_code == 422
