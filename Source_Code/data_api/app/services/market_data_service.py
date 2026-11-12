import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.historical_price import HistoricalPrice
from app.models.instrument import Instrument
from app.repositories.historical_price_repository import (
    HistoricalPriceRepository,
)
from app.repositories.instrument_repository import InstrumentRepository


SUPPORTED_CURRENCIES = {"PLN", "EUR", "GBP", "USD"}


@dataclass(frozen=True)
class HistoricalPriceData:
    price_date: date
    close_price: Decimal
    currency: str
    source: str


class MarketDataError(Exception):
    """Base exception for market data operations."""


class InstrumentNotFoundError(MarketDataError):
    pass


class InstrumentAlreadyExistsError(MarketDataError):
    pass


class InvalidMarketDataError(MarketDataError):
    pass


class MarketDataService:
    def __init__(
        self,
        instrument_repository: InstrumentRepository,
        historical_price_repository: HistoricalPriceRepository,
    ) -> None:
        self.instrument_repository = instrument_repository
        self.historical_price_repository = historical_price_repository

    def get_instrument(
        self,
        instrument_id: uuid.UUID,
    ) -> Instrument:
        instrument = self.instrument_repository.get_by_id(instrument_id)

        if instrument is None:
            raise InstrumentNotFoundError(f"Instrument {instrument_id} was not found.")

        return instrument

    def get_instrument_by_symbol(
        self,
        symbol: str,
        exchange: str,
    ) -> Instrument | None:
        return self.instrument_repository.get_by_symbol_and_exchange(
            symbol=symbol.strip().upper(),
            exchange=exchange.strip().upper(),
        )

    def create_instrument(
        self,
        *,
        symbol: str,
        name: str,
        exchange: str,
        quote_currency: str,
    ) -> Instrument:
        symbol = symbol.strip().upper()
        name = name.strip()
        exchange = exchange.strip().upper()
        quote_currency = quote_currency.strip().upper()

        if not symbol or not name or not exchange:
            raise InvalidMarketDataError("Symbol, name and exchange cannot be empty.")

        if quote_currency not in SUPPORTED_CURRENCIES:
            raise InvalidMarketDataError(f"Unsupported currency: {quote_currency}.")

        existing = self.instrument_repository.get_by_symbol_and_exchange(
            symbol=symbol,
            exchange=exchange,
        )

        if existing is not None:
            raise InstrumentAlreadyExistsError(f"Instrument {symbol} on {exchange} already exists.")

        return self.instrument_repository.create(
            symbol=symbol,
            name=name,
            exchange=exchange,
            quote_currency=quote_currency,
        )

    def get_historical_prices(
        self,
        instrument_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[HistoricalPrice]:
        if start_date > end_date:
            raise InvalidMarketDataError("Start date cannot be later than end date.")

        self.get_instrument(instrument_id)

        return self.historical_price_repository.get_by_instrument_and_date_range(
            instrument_id=instrument_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_latest_price(
        self,
        instrument_id: uuid.UUID,
    ) -> HistoricalPrice | None:
        self.get_instrument(instrument_id)

        return self.historical_price_repository.get_latest(instrument_id)

    def save_historical_prices(
        self,
        instrument_id: uuid.UUID,
        prices: list[HistoricalPriceData],
    ) -> None:
        instrument = self.get_instrument(instrument_id)

        self._validate_prices(instrument, prices)

        if not prices:
            return

        price_records = [
            {
                "instrument_id": instrument_id,
                "price_date": price.price_date,
                "close_price": price.close_price,
                "currency": price.currency,
                "source": price.source,
            }
            for price in prices
        ]

        self.historical_price_repository.upsert_many(price_records)

    @staticmethod
    def _validate_prices(
        instrument: Instrument,
        prices: list[HistoricalPriceData],
    ) -> None:
        seen_keys: set[tuple[date, str]] = set()

        for price in prices:
            if not isinstance(price.close_price, Decimal):
                raise InvalidMarketDataError("Price must be represented as Decimal.")

            if not price.close_price.is_finite() or price.close_price <= 0:
                raise InvalidMarketDataError("Price must be a finite positive number.")

            currency = price.currency.strip().upper()

            if currency not in SUPPORTED_CURRENCIES:
                raise InvalidMarketDataError(f"Unsupported currency: {currency}.")

            if currency != instrument.quote_currency:
                raise InvalidMarketDataError("Price currency must match instrument quote currency.")

            source = price.source.strip()

            if not source or len(source) > 50:
                raise InvalidMarketDataError("Source must contain between 1 and 50 characters.")

            key = (price.price_date, source)

            if key in seen_keys:
                raise InvalidMarketDataError("Duplicate instrument, date and source in price batch.")

            seen_keys.add(key)
