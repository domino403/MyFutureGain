from sqlalchemy import inspect


def test_market_data_tables_exist(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "instruments" in tables
    assert "historical_prices" in tables


def test_instruments_table_has_expected_columns(engine):
    inspector = inspect(engine)

    columns = {column["name"] for column in inspector.get_columns("instruments")}

    expected_columns = {
        "id",
        "symbol",
        "name",
        "exchange",
        "quote_currency",
        "created_at",
    }

    assert expected_columns.issubset(columns)


def test_historical_prices_table_has_expected_columns(engine):
    inspector = inspect(engine)

    columns = {column["name"] for column in inspector.get_columns("historical_prices")}

    expected_columns = {
        "id",
        "instrument_id",
        "price_date",
        "close_price",
        "currency",
        "source",
        "created_at",
    }

    assert expected_columns.issubset(columns)


def test_instruments_has_exchange_symbol_unique_constraint(engine):
    inspector = inspect(engine)

    constraints = inspector.get_unique_constraints("instruments")

    assert any(constraint["column_names"] == ["exchange", "symbol"] for constraint in constraints)


def test_historical_prices_has_unique_constraint(engine):
    inspector = inspect(engine)

    constraints = inspector.get_unique_constraints("historical_prices")

    assert any(constraint["column_names"] == ["instrument_id", "price_date", "source"] for constraint in constraints)


def test_historical_prices_has_instrument_foreign_key(engine):
    inspector = inspect(engine)

    foreign_keys = inspector.get_foreign_keys("historical_prices")

    assert any(
        fk["constrained_columns"] == ["instrument_id"]
        and fk["referred_table"] == "instruments"
        and fk["referred_columns"] == ["id"]
        for fk in foreign_keys
    )


def test_historical_prices_foreign_key_restricts_deletion(engine):
    inspector = inspect(engine)

    foreign_keys = inspector.get_foreign_keys("historical_prices")

    instrument_fk = next(fk for fk in foreign_keys if fk["constrained_columns"] == ["instrument_id"])

    assert instrument_fk["options"].get("ondelete") == "RESTRICT"


def test_instruments_has_symbol_index(engine):
    inspector = inspect(engine)

    indexes = inspector.get_indexes("instruments")

    assert any(index["column_names"] == ["symbol"] for index in indexes)


def test_historical_prices_has_instrument_date_index(engine):
    inspector = inspect(engine)

    indexes = inspector.get_indexes("historical_prices")

    assert any(index["column_names"] == ["instrument_id", "price_date"] for index in indexes)


def test_instruments_has_currency_check_constraint(engine):
    inspector = inspect(engine)

    constraints = inspector.get_check_constraints("instruments")

    assert any(constraint["name"] == "valid_instrument_quote_currency" for constraint in constraints)


def test_historical_prices_has_price_check_constraint(engine):
    inspector = inspect(engine)

    constraints = inspector.get_check_constraints("historical_prices")

    assert any(constraint["name"] == "valid_historical_price" for constraint in constraints)


def test_historical_prices_has_currency_check_constraint(engine):
    inspector = inspect(engine)

    constraints = inspector.get_check_constraints("historical_prices")

    assert any(constraint["name"] == "valid_historical_price_currency" for constraint in constraints)
