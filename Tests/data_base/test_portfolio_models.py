import uuid

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.models import Account, Portfolio


def create_portfolio(
    db_session,
    *,
    owner_id=None,
    name="Test Portfolio",
    base_currency="PLN",
):
    portfolio = Portfolio(
        owner_id=owner_id or uuid.uuid4(),
        name=name,
        base_currency=base_currency,
    )

    db_session.add(portfolio)
    db_session.flush()

    return portfolio


def test_create_portfolio(db_session):
    portfolio = create_portfolio(db_session)

    assert portfolio.id is not None, "Portfiolio ID doesn't exist"
    assert portfolio.name == "Test Portfolio", "Incorrect Portfolio name"
    assert portfolio.base_currency == "PLN", "Incorrect base currency"


def test_create_account(db_session):
    portfolio = create_portfolio(db_session)

    account = Account(
        portfolio_id=portfolio.id,
        name="Main Brokerage",
        account_type="BROKERAGE",
        default_currency="PLN",
    )

    db_session.add(account)
    db_session.flush()

    assert account.id is not None, "account ID doesn't exist"
    assert account.portfolio_id == portfolio.id, "account ID doen't match portfolio ID"


def test_portfolio_can_have_multiple_accounts(db_session):
    portfolio = create_portfolio(db_session)

    accounts = [
        Account(
            portfolio_id=portfolio.id,
            name="Brokerage",
            account_type="BROKERAGE",
            default_currency="PLN",
        ),
        Account(
            portfolio_id=portfolio.id,
            name="Savings",
            account_type="SAVINGS",
            default_currency="EUR",
        ),
    ]

    db_session.add_all(accounts)
    db_session.flush()

    assert len(portfolio.accounts) == 2, "Incorrect portfolio number"


@pytest.mark.parametrize(
    "currency",
    ["PLN", "EUR", "GBP", "USD"],
)
def test_portfolio_accepts_supported_currencies(
    db_session,
    currency,
):
    portfolio = create_portfolio(
        db_session,
        base_currency=currency,
    )

    assert portfolio.base_currency == currency, "Incorrect currency in created Portfolio"


def test_portfolio_rejects_unsupported_currency(db_session):
    with pytest.raises(expected_exception=IntegrityError), db_session.begin_nested():
        create_portfolio(
            db_session,
            base_currency="CHF",
        )


@pytest.mark.parametrize(
    "account_type",
    ["BROKERAGE", "SAVINGS", "CASH"],
)
def test_account_accepts_supported_types(
    db_session,
    account_type,
):
    portfolio = create_portfolio(db_session)

    account = Account(
        portfolio_id=portfolio.id,
        name="Test Account",
        account_type=account_type,
        default_currency="PLN",
    )

    db_session.add(account)
    db_session.flush()

    assert account.account_type == account_type


def test_account_rejects_unsupported_type(db_session):
    portfolio = create_portfolio(db_session)

    with pytest.raises(expected_exception=IntegrityError), db_session.begin_nested():  # noqa: PT012
        db_session.add(
            Account(
                portfolio_id=portfolio.id,
                name="Invalid Account",
                account_type="CRYPTO",
                default_currency="PLN",
            )
        )
        db_session.flush()


def test_account_rejects_unsupported_currency(db_session):
    portfolio = create_portfolio(db_session)

    with pytest.raises(IntegrityError), db_session.begin_nested():  # noqa: PT012
        db_session.add(
            Account(
                portfolio_id=portfolio.id,
                name="Invalid Account",
                account_type="BROKERAGE",
                default_currency="CHF",
            )
        )
        db_session.flush()


def test_account_requires_existing_portfolio(db_session):
    account = Account(
        portfolio_id=uuid.uuid4(),
        name="Orphan Account",
        account_type="BROKERAGE",
        default_currency="PLN",
    )

    with pytest.raises(IntegrityError), db_session.begin_nested():  # noqa: PT012
        db_session.add(account)
        db_session.flush()


def test_portfolio_cannot_be_deleted_while_accounts_exist(
    db_session,
):
    portfolio = create_portfolio(db_session)

    account = Account(
        portfolio_id=portfolio.id,
        name="Main Brokerage",
        account_type="BROKERAGE",
        default_currency="PLN",
    )

    db_session.add(account)
    db_session.flush()

    with pytest.raises(IntegrityError), db_session.begin_nested():  # noqa: PT012
        db_session.execute(delete(Portfolio).where(Portfolio.id == portfolio.id))
        db_session.flush()
