from sqlalchemy import inspect


def test_portfolio_and_account_tables_exist(engine):
    inspector = inspect(engine)

    tables = inspector.get_table_names()

    assert "portfolios" in tables, "missing `portfolios` table"
    assert "accounts" in tables, "missing `accounts` table"


def test_portfolios_table_has_expected_columns(engine):
    inspector = inspect(engine)

    columns = {column["name"] for column in inspector.get_columns("portfolios")}

    expected_columns = {
        "id",
        "owner_id",
        "name",
        "base_currency",
        "created_at",
        "updated_at",
    }

    assert expected_columns.issubset(columns), "Incorrect columns in `portfolios` table"


def test_accounts_table_has_expected_columns(engine):
    inspector = inspect(engine)

    columns = {column["name"] for column in inspector.get_columns("accounts")}

    expected_columns = {
        "id",
        "portfolio_id",
        "name",
        "account_type",
        "default_currency",
        "created_at",
        "updated_at",
    }

    assert expected_columns.issubset(columns), "Incorrect columns in `accounts` table"


def test_accounts_has_portfolio_foreign_key(engine):
    inspector = inspect(engine)

    foreign_keys = inspector.get_foreign_keys("accounts")

    assert any(
        fk["constrained_columns"] == ["portfolio_id"] and fk["referred_table"] == "portfolios" for fk in foreign_keys
    ), "Incorrect `portfolios` table `foreign_key` in `accounts` table"


def test_portfolios_has_owner_id_index(engine):
    inspector = inspect(engine)

    indexes = inspector.get_indexes("portfolios")

    assert any(index["column_names"] == ["owner_id"] for index in indexes), "Incorrect owner ID in `portfolios` table"
