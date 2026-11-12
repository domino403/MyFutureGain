import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SUPPORTED_CURRENCIES = {"PLN", "EUR", "GBP", "USD"}


class HistoricalPriceInput(BaseModel):
    price_date: date
    close_price: Decimal = Field(gt=0, max_digits=20, decimal_places=8)
    currency: str = Field(min_length=3, max_length=3)
    source: str = Field(min_length=1, max_length=50)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        currency = value.strip().upper()

        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError("Unsupported currency.")

        return currency

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        return value.strip()


class HistoricalPriceBatchCreate(BaseModel):
    prices: list[HistoricalPriceInput] = Field(max_length=500)


class HistoricalPriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    instrument_id: uuid.UUID
    price_date: date
    close_price: Decimal
    currency: str
    source: str
    created_at: datetime
