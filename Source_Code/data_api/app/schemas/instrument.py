import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


SUPPORTED_CURRENCIES = {"PLN", "EUR", "GBP", "USD"}


class InstrumentCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=255)
    exchange: str = Field(min_length=1, max_length=50)
    quote_currency: str = Field(min_length=3, max_length=3)

    @field_validator("symbol", "exchange")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("quote_currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        currency = value.strip().upper()

        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError("Unsupported currency.")

        return currency


class InstrumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    name: str
    exchange: str
    quote_currency: str
