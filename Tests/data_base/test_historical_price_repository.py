from datetime import date
from decimal import Decimal

from app.models.historical_price import HistoricalPrice
from app.models.instrument import Instrument
from app.repositories.historical_price_repository import (
    HistoricalPriceRepository,
)
from sqlalchemy import select


def create_instrument(db_session) -> Instrument:
    instrument = Instrument(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        quote_currency="USD",
    )
    db_session.add(instrument)
    db_session.flush()

    return instrument


def create_price(
    db_session,
    instrument_id,
    *,
    price_date: date,
    close_price: Decimal = Decimal("150.00"),
    source: str = "test_provider",
) -> HistoricalPrice:
    price = HistoricalPrice(
        instrument_id=instrument_id,
        price_date=price_date,
        close_price=close_price,
        currency="USD",
        source=source,
    )
    db_session.add(price)
    db_session.flush()

    return price


def test_get_by_instrument_and_date_range_returns_prices(db_session):
    instrument = create_instrument(db_session)

    create_price(
        db_session,
        instrument.id,
        price_date=date(2026, 1, 1),
    )
    create_price(
        db_session,
        instrument.id,
        price_date=date(2026, 1, 2),
        close_price=Decimal("155.00"),
    )
    create_price(
        db_session,
        instrument.id,
        price_date=date(2026, 1, 3),
    )

    repository = HistoricalPriceRepository(db_session)

    result = repository.get_by_instrument_and_date_range(
        instrument.id,
        start_date=date(2026, 1, 2),
        end_date=date(2026, 1, 3),
    )

    assert len(result) == 2
    assert [price.price_date for price in result] == [
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]


def test_get_by_instrument_and_date_range_returns_empty_list(db_session):
    instrument = create_instrument(db_session)
    repository = HistoricalPriceRepository(db_session)

    result = repository.get_by_instrument_and_date_range(
        instrument.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    assert result == []


def test_get_latest_returns_most_recent_price(db_session):
    instrument = create_instrument(db_session)

    create_price(
        db_session,
        instrument.id,
        price_date=date(2026, 1, 1),
    )
    latest_price = create_price(
        db_session,
        instrument.id,
        price_date=date(2026, 1, 5),
        close_price=Decimal("175.00"),
    )

    repository = HistoricalPriceRepository(db_session)

    result = repository.get_latest(instrument.id)

    assert result is not None
    assert result.id == latest_price.id
    assert result.price_date == date(2026, 1, 5)


def test_get_latest_returns_none_when_no_prices_exist(db_session):
    instrument = create_instrument(db_session)
    repository = HistoricalPriceRepository(db_session)

    result = repository.get_latest(instrument.id)

    assert result is None


def test_upsert_many_inserts_multiple_prices(db_session):
    instrument = create_instrument(db_session)
    repository = HistoricalPriceRepository(db_session)

    repository.upsert_many(
        [
            {
                "instrument_id": instrument.id,
                "price_date": date(2026, 1, 1),
                "close_price": Decimal("150.00"),
                "currency": "USD",
                "source": "provider_a",
            },
            {
                "instrument_id": instrument.id,
                "price_date": date(2026, 1, 2),
                "close_price": Decimal("155.00"),
                "currency": "USD",
                "source": "provider_a",
            },
        ]
    )

    result = db_session.scalars(select(HistoricalPrice).where(HistoricalPrice.instrument_id == instrument.id)).all()

    assert len(result) == 2


def test_upsert_many_updates_existing_price(db_session):
    instrument = create_instrument(db_session)

    existing_price = create_price(
        db_session,
        instrument.id,
        price_date=date(2026, 1, 1),
        close_price=Decimal("150.00"),
        source="provider_a",
    )

    repository = HistoricalPriceRepository(db_session)

    repository.upsert_many(
        [
            {
                "instrument_id": instrument.id,
                "price_date": date(2026, 1, 1),
                "close_price": Decimal("160.00"),
                "currency": "USD",
                "source": "provider_a",
            }
        ]
    )

    db_session.refresh(existing_price)

    assert existing_price.close_price == Decimal("160.00000000")


def test_upsert_many_allows_different_sources_for_same_date(db_session):
    instrument = create_instrument(db_session)
    repository = HistoricalPriceRepository(db_session)

    repository.upsert_many(
        [
            {
                "instrument_id": instrument.id,
                "price_date": date(2026, 1, 1),
                "close_price": Decimal("150.00"),
                "currency": "USD",
                "source": "provider_a",
            },
            {
                "instrument_id": instrument.id,
                "price_date": date(2026, 1, 1),
                "close_price": Decimal("151.00"),
                "currency": "USD",
                "source": "provider_b",
            },
        ]
    )

    result = db_session.scalars(select(HistoricalPrice).where(HistoricalPrice.instrument_id == instrument.id)).all()

    assert len(result) == 2


def test_upsert_many_does_nothing_for_empty_list(db_session):
    repository = HistoricalPriceRepository(db_session)

    repository.upsert_many([])

    assert True
