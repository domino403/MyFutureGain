import uuid

import pytest
from app.models.instrument import Instrument
from app.repositories.instrument_repository import InstrumentRepository
from sqlalchemy.exc import IntegrityError


def create_instrument(
    db_session,
    *,
    symbol: str = "AAPL",
    name: str = "Apple Inc.",
    exchange: str = "NASDAQ",
    quote_currency: str = "USD",
) -> Instrument:
    instrument = Instrument(
        symbol=symbol,
        name=name,
        exchange=exchange,
        quote_currency=quote_currency,
    )
    db_session.add(instrument)
    db_session.flush()

    return instrument


def test_get_by_id_returns_instrument(db_session):
    instrument = create_instrument(db_session)
    repository = InstrumentRepository(db_session)

    result = repository.get_by_id(instrument.id)

    assert result is not None
    assert result.id == instrument.id
    assert result.symbol == "AAPL"


def test_get_by_id_returns_none_for_nonexistent_instrument(db_session):
    repository = InstrumentRepository(db_session)

    result = repository.get_by_id(uuid.uuid4())

    assert result is None


def test_get_by_symbol_and_exchange_returns_instrument(db_session):
    instrument = create_instrument(db_session)
    repository = InstrumentRepository(db_session)

    result = repository.get_by_symbol_and_exchange(
        symbol="AAPL",
        exchange="NASDAQ",
    )

    assert result is not None
    assert result.id == instrument.id


def test_get_by_symbol_and_exchange_returns_none_when_not_found(
    db_session,
):
    repository = InstrumentRepository(db_session)

    result = repository.get_by_symbol_and_exchange(
        symbol="UNKNOWN",
        exchange="NASDAQ",
    )

    assert result is None


def test_get_all_returns_all_instruments_ordered_by_symbol(db_session):
    create_instrument(
        db_session,
        symbol="MSFT",
        name="Microsoft Corporation",
    )
    create_instrument(
        db_session,
        symbol="AAPL",
        name="Apple Inc.",
    )

    repository = InstrumentRepository(db_session)

    result = repository.get_all()

    assert len(result) == 2
    assert [instrument.symbol for instrument in result] == [
        "AAPL",
        "MSFT",
    ]


def test_create_saves_instrument(db_session):
    repository = InstrumentRepository(db_session)

    result = repository.create(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        quote_currency="USD",
    )

    assert result.id is not None
    assert result.symbol == "AAPL"
    assert result.name == "Apple Inc."
    assert result.exchange == "NASDAQ"
    assert result.quote_currency == "USD"

    saved_instrument = db_session.get(Instrument, result.id)

    assert saved_instrument is not None


def test_create_rejects_duplicate_exchange_and_symbol(db_session):
    create_instrument(db_session)
    repository = InstrumentRepository(db_session)

    with pytest.raises(IntegrityError), db_session.begin_nested():
        repository.create(
            symbol="AAPL",
            name="Another Apple",
            exchange="NASDAQ",
            quote_currency="USD",
        )


def test_create_rejects_unsupported_currency(db_session):
    repository = InstrumentRepository(db_session)

    with pytest.raises(IntegrityError), db_session.begin_nested():
        repository.create(
            symbol="ABC",
            name="Example Company",
            exchange="NYSE",
            quote_currency="CHF",
        )
