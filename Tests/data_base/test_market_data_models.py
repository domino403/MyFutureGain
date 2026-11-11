from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.models import HistoricalPrice, Instrument


def create_instrument(
    db_session,
    *,
    symbol="AAPL",
    name="Apple Inc.",
    exchange="NASDAQ",
    quote_currency="USD",
):
    instrument = Instrument(
        symbol=symbol,
        name=name,
        exchange=exchange,
        quote_currency=quote_currency,
    )

    db_session.add(instrument)
    db_session.flush()

    return instrument


def create_historical_price(
    db_session,
    *,
    instrument_id,
    price_date=date(2026, 1, 15),
    close_price=Decimal("250.50000000"),
    currency="USD",
    source="test_provider",
):
    historical_price = HistoricalPrice(
        instrument_id=instrument_id,
        price_date=price_date,
        close_price=close_price,
        currency=currency,
        source=source,
    )

    db_session.add(historical_price)
    db_session.flush()

    return historical_price


# Instrument tests


def test_create_instrument(db_session):
    instrument = create_instrument(db_session)

    assert instrument.id is not None
    assert instrument.symbol == "AAPL"
    assert instrument.name == "Apple Inc."
    assert instrument.exchange == "NASDAQ"
    assert instrument.quote_currency == "USD"


def test_instrument_can_have_same_symbol_on_different_exchanges(
    db_session,
):
    nasdaq_instrument = create_instrument(
        db_session,
        symbol="ABC",
        exchange="NASDAQ",
    )

    nyse_instrument = create_instrument(
        db_session,
        symbol="ABC",
        exchange="NYSE",
    )

    assert nasdaq_instrument.id != nyse_instrument.id


def test_instrument_rejects_duplicate_exchange_and_symbol(
    db_session,
):
    create_instrument(
        db_session,
        symbol="AAPL",
        exchange="NASDAQ",
    )

    with pytest.raises(IntegrityError), db_session.begin_nested():
        create_instrument(
            db_session,
            symbol="AAPL",
            exchange="NASDAQ",
        )


@pytest.mark.parametrize(
    "currency",
    ["PLN", "EUR", "GBP", "USD"],
)
def test_instrument_accepts_supported_currencies(
    db_session,
    currency,
):
    instrument = create_instrument(
        db_session,
        quote_currency=currency,
    )

    assert instrument.quote_currency == currency


def test_instrument_rejects_unsupported_currency(db_session):
    with pytest.raises(IntegrityError), db_session.begin_nested():
        create_instrument(
            db_session,
            quote_currency="CHF",
        )


# HistoricalPrice tests


def test_create_historical_price(db_session):
    instrument = create_instrument(db_session)

    price = create_historical_price(
        db_session,
        instrument_id=instrument.id,
    )

    assert price.id is not None
    assert price.instrument_id == instrument.id
    assert price.price_date == date(2026, 1, 15)
    assert price.close_price == Decimal("250.50000000")
    assert price.currency == "USD"
    assert price.source == "test_provider"


def test_instrument_can_have_multiple_historical_prices(
    db_session,
):
    instrument = create_instrument(db_session)

    first_price = create_historical_price(
        db_session,
        instrument_id=instrument.id,
        price_date=date(2026, 1, 14),
        close_price=Decimal("248.50"),
    )

    second_price = create_historical_price(
        db_session,
        instrument_id=instrument.id,
        price_date=date(2026, 1, 15),
        close_price=Decimal("250.50"),
    )

    assert first_price.id != second_price.id


def test_historical_price_allows_different_sources(
    db_session,
):
    instrument = create_instrument(db_session)

    first_price = create_historical_price(
        db_session,
        instrument_id=instrument.id,
        source="provider_a",
    )

    second_price = create_historical_price(
        db_session,
        instrument_id=instrument.id,
        source="provider_b",
    )

    assert first_price.id != second_price.id


def test_historical_price_rejects_duplicate_instrument_date_source(
    db_session,
):
    instrument = create_instrument(db_session)

    create_historical_price(
        db_session,
        instrument_id=instrument.id,
        price_date=date(2026, 1, 15),
        source="provider_a",
    )

    with pytest.raises(IntegrityError), db_session.begin_nested():
        create_historical_price(
            db_session,
            instrument_id=instrument.id,
            price_date=date(2026, 1, 15),
            source="provider_a",
        )


@pytest.mark.parametrize(
    "price",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("-100.50"),
    ],
)
def test_historical_price_rejects_non_positive_price(
    db_session,
    price,
):
    instrument = create_instrument(db_session)

    with pytest.raises(IntegrityError), db_session.begin_nested():
        create_historical_price(
            db_session,
            instrument_id=instrument.id,
            close_price=price,
        )


@pytest.mark.parametrize(
    "currency",
    ["PLN", "EUR", "GBP", "USD"],
)
def test_historical_price_accepts_supported_currencies(
    db_session,
    currency,
):
    instrument = create_instrument(db_session)

    price = create_historical_price(
        db_session,
        instrument_id=instrument.id,
        currency=currency,
    )

    assert price.currency == currency


def test_historical_price_rejects_unsupported_currency(
    db_session,
):
    instrument = create_instrument(db_session)

    with pytest.raises(IntegrityError), db_session.begin_nested():
        create_historical_price(
            db_session,
            instrument_id=instrument.id,
            currency="CHF",
        )


def test_historical_price_requires_existing_instrument(
    db_session,
):
    with pytest.raises(IntegrityError), db_session.begin_nested():
        create_historical_price(
            db_session,
            instrument_id=__import__("uuid").uuid4(),
        )


def test_instrument_cannot_be_deleted_while_prices_exist(
    db_session,
):
    instrument = create_instrument(db_session)

    create_historical_price(
        db_session,
        instrument_id=instrument.id,
    )

    with pytest.raises(IntegrityError), db_session.begin_nested():  # noqa: PT012
        db_session.execute(delete(Instrument).where(Instrument.id == instrument.id))
        db_session.flush()


def test_instrument_relationship_returns_historical_prices(
    db_session,
):
    instrument = create_instrument(db_session)

    create_historical_price(
        db_session,
        instrument_id=instrument.id,
        price_date=date(2026, 1, 14),
    )

    create_historical_price(
        db_session,
        instrument_id=instrument.id,
        price_date=date(2026, 1, 15),
    )

    assert len(instrument.historical_prices) == 2
