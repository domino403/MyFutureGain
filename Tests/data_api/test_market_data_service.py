from datetime import date
from decimal import Decimal

import pytest

from app.repositories.historical_price_repository import (
    HistoricalPriceRepository,
)
from app.repositories.instrument_repository import InstrumentRepository
from app.services.market_data_service import (
    HistoricalPriceData,
    InstrumentAlreadyExistsError,
    InstrumentNotFoundError,
    InvalidMarketDataError,
    MarketDataService,
)


@pytest.fixture
def market_data_service(db_session):
    return MarketDataService(
        instrument_repository=InstrumentRepository(db_session),
        historical_price_repository=HistoricalPriceRepository(db_session),
    )


@pytest.fixture
def instrument(market_data_service):
    return market_data_service.create_instrument(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        quote_currency="USD",
    )


def test_create_instrument(market_data_service):
    result = market_data_service.create_instrument(
        symbol="aapl",
        name="Apple Inc.",
        exchange="nasdaq",
        quote_currency="usd",
    )

    assert result.symbol == "AAPL"
    assert result.exchange == "NASDAQ"
    assert result.quote_currency == "USD"


def test_create_instrument_rejects_duplicate(
    market_data_service,
    instrument,
):
    with pytest.raises(InstrumentAlreadyExistsError):
        market_data_service.create_instrument(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            quote_currency="USD",
        )


def test_create_instrument_rejects_invalid_currency(
    market_data_service,
):
    with pytest.raises(InvalidMarketDataError):
        market_data_service.create_instrument(
            symbol="ABC",
            name="Example Company",
            exchange="NYSE",
            quote_currency="CHF",
        )


def test_get_instrument_returns_instrument(
    market_data_service,
    instrument,
):
    result = market_data_service.get_instrument(instrument.id)

    assert result.id == instrument.id


def test_get_instrument_raises_when_not_found(market_data_service):
    import uuid

    with pytest.raises(InstrumentNotFoundError):
        market_data_service.get_instrument(uuid.uuid4())


def test_get_instrument_by_symbol(market_data_service, instrument):
    result = market_data_service.get_instrument_by_symbol(
        symbol="aapl",
        exchange="nasdaq",
    )

    assert result is not None
    assert result.id == instrument.id


def test_save_historical_prices(market_data_service, instrument):
    prices = [
        HistoricalPriceData(
            price_date=date(2026, 1, 1),
            close_price=Decimal("150.25"),
            currency="USD",
            source="provider_a",
        ),
        HistoricalPriceData(
            price_date=date(2026, 1, 2),
            close_price=Decimal("155.50"),
            currency="USD",
            source="provider_a",
        ),
    ]

    market_data_service.save_historical_prices(
        instrument.id,
        prices,
    )

    result = market_data_service.get_historical_prices(
        instrument.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 2),
    )

    assert len(result) == 2


def test_save_prices_rejects_currency_mismatch(
    market_data_service,
    instrument,
):
    prices = [
        HistoricalPriceData(
            price_date=date(2026, 1, 1),
            close_price=Decimal("150.25"),
            currency="PLN",
            source="provider_a",
        )
    ]

    with pytest.raises(InvalidMarketDataError):
        market_data_service.save_historical_prices(
            instrument.id,
            prices,
        )


@pytest.mark.parametrize(
    "price",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_save_prices_rejects_invalid_price(
    market_data_service,
    instrument,
    price,
):
    prices = [
        HistoricalPriceData(
            price_date=date(2026, 1, 1),
            close_price=price,
            currency="USD",
            source="provider_a",
        )
    ]

    with pytest.raises(InvalidMarketDataError):
        market_data_service.save_historical_prices(
            instrument.id,
            prices,
        )


def test_save_prices_rejects_duplicate_batch_entries(
    market_data_service,
    instrument,
):
    prices = [
        HistoricalPriceData(
            price_date=date(2026, 1, 1),
            close_price=Decimal("150.00"),
            currency="USD",
            source="provider_a",
        ),
        HistoricalPriceData(
            price_date=date(2026, 1, 1),
            close_price=Decimal("151.00"),
            currency="USD",
            source="provider_a",
        ),
    ]

    with pytest.raises(InvalidMarketDataError):
        market_data_service.save_historical_prices(
            instrument.id,
            prices,
        )


def test_get_historical_prices_rejects_invalid_date_range(
    market_data_service,
    instrument,
):
    with pytest.raises(InvalidMarketDataError):
        market_data_service.get_historical_prices(
            instrument.id,
            start_date=date(2026, 1, 31),
            end_date=date(2026, 1, 1),
        )


def test_save_empty_price_list(market_data_service, instrument):
    market_data_service.save_historical_prices(instrument.id, [])
