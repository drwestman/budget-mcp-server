import os
from datetime import date

import pytest

from app.models.database import Database


@pytest.fixture
def db():
    db_path = "test_temp_db.duckdb"
    # Ensure the database file does not exist before creating a new one
    if os.path.exists(db_path):
        os.remove(db_path)

    database = Database(db_path=db_path)
    yield database
    database.close()
    # Clean up the database file after tests are done
    if os.path.exists(db_path):
        os.remove(db_path)


def test_insert_and_get_envelope(db):
    # Test inserting a new envelope and retrieving it by ID
    env_id = db.insert_envelope("Groceries", 500.00, 100.00, "Monthly grocery budget")
    assert env_id is not None
    envelope = db.get_envelope_by_id(env_id)
    assert envelope is not None
    assert envelope["category"] == "Groceries"
    assert envelope["budgeted_amount"] == 500.00
    assert envelope["starting_balance"] == 100.00
    assert envelope["description"] == "Monthly grocery budget"


def test_get_envelope_by_category(db):
    # Test retrieving an envelope by its category
    db.insert_envelope("Utilities", 200.00, 50.00, "Electricity, Water, Internet")
    envelope = db.get_envelope_by_category("Utilities")
    assert envelope is not None
    assert envelope["category"] == "Utilities"


def test_get_all_envelopes(db):
    # Test retrieving all envelopes
    db.insert_envelope("Dining Out", 150.00, 0.00, "Eating at restaurants")
    db.insert_envelope("Transport", 100.00, 20.00, "Public transport and fuel")
    envelopes = db.get_all_envelopes()
    assert len(envelopes) == 2
    categories = [env["category"] for env in envelopes]
    assert "Dining Out" in categories
    assert "Transport" in categories


def test_update_envelope(db):
    # Test updating an existing envelope's details
    env_id = db.insert_envelope(
        "Shopping", 300.00, 50.00, "Clothing and other shopping"
    )
    updated = db.update_envelope(
        env_id,
        category="Online Shopping",
        budgeted_amount=350.00,
        description="Online purchases",
    )
    assert updated is True
    envelope = db.get_envelope_by_id(env_id)
    assert envelope["category"] == "Online Shopping"
    assert envelope["budgeted_amount"] == 350.00
    assert envelope["description"] == "Online purchases"


def test_delete_envelope(db):
    # Test deleting an envelope
    env_id = db.insert_envelope(
        "Entertainment", 100.00, 10.00, "Movies, concerts, etc."
    )
    deleted = db.delete_envelope(env_id)
    assert deleted is True
    envelope = db.get_envelope_by_id(env_id)
    assert envelope is None


def test_insert_duplicate_envelope_category_raises_value_error(db):
    # Test that inserting an envelope with a duplicate category name raises a ValueError
    db.insert_envelope("Health", 100.00, 0.00, "Gym, supplements")
    with pytest.raises(ValueError) as excinfo:
        db.insert_envelope("Health", 150.00, 10.00, "Duplicate category")
    assert "already exists" in str(excinfo.value)


def test_insert_and_get_transaction(db):
    # Test inserting a new transaction and retrieving it by ID
    env_id = db.insert_envelope("General", 100.00, 0.00, "General expenses")
    trans_id = db.insert_transaction(
        env_id, 25.50, "Lunch", date(2023, 1, 15), "expense"
    )
    assert trans_id is not None
    transaction = db.get_transaction_by_id(trans_id)
    assert transaction is not None
    assert transaction["envelope_id"] == env_id
    assert transaction["amount"] == 25.50
    assert transaction["description"] == "Lunch"
    assert transaction["date"] == "2023-01-15"
    assert transaction["type"] == "expense"


def test_get_transactions_for_envelope(db):
    # Test retrieving all transactions for a specific envelope
    env_id1 = db.insert_envelope("Gifts", 100.00, 0.00, "Birthday gifts")
    env_id2 = db.insert_envelope("Holiday", 500.00, 100.00, "Vacation fund")
    db.insert_transaction(
        env_id1, 50.00, "Friend's Birthday", date(2023, 2, 10), "expense"
    )
    db.insert_transaction(
        env_id2, 200.00, "Flight tickets", date(2023, 2, 15), "expense"
    )
    db.insert_transaction(
        env_id1, 30.00, "Office gift exchange", date(2023, 2, 20), "expense"
    )

    transactions = db.get_transactions_for_envelope(env_id1)
    assert len(transactions) == 2
    descriptions = [t["description"] for t in transactions]
    assert "Friend's Birthday" in descriptions
    assert "Office gift exchange" in descriptions

    transactions_env2 = db.get_transactions_for_envelope(env_id2)
    assert len(transactions_env2) == 1
    assert transactions_env2[0]["description"] == "Flight tickets"


def test_get_all_transactions(db):
    # Test retrieving all transactions from the database
    env_id1 = db.insert_envelope("Food", 300.00, 50.00, "Groceries and dining")
    env_id2 = db.insert_envelope("Travel", 400.00, 0.00, "Commuting and trips")
    db.insert_transaction(
        env_id1, 45.00, "Weekly groceries", date(2023, 3, 1), "expense"
    )
    db.insert_transaction(env_id2, 120.00, "Train ticket", date(2023, 3, 5), "expense")
    db.insert_transaction(env_id1, 15.00, "Coffee", date(2023, 3, 3), "expense")

    transactions = db.get_all_transactions()
    # Transactions are ordered by date DESC
    assert len(transactions) == 3
    assert transactions[0]["description"] == "Train ticket"
    assert transactions[1]["description"] == "Coffee"
    assert transactions[2]["description"] == "Weekly groceries"


def test_update_transaction(db):
    # Test updating an existing transaction's details
    env_id = db.insert_envelope("Bills", 500.00, 100.00, "Monthly bills")
    trans_id = db.insert_transaction(
        env_id, 75.00, "Electricity Bill", date(2023, 4, 5), "expense"
    )

    env_id_new = db.insert_envelope("Utilities", 200.00, 0.00, "New Utilities")
    updated = db.update_transaction(
        trans_id,
        envelope_id=env_id_new,
        amount=80.00,
        description="Updated Electricity Bill",
        date=date(2023, 4, 6),
        type="expense",
    )
    assert updated is True
    transaction = db.get_transaction_by_id(trans_id)
    assert transaction["envelope_id"] == env_id_new
    assert transaction["amount"] == 80.00
    assert transaction["description"] == "Updated Electricity Bill"
    assert (
        transaction["date"] == "2023-04-06"
    )  # Dates are stored and retrieved as ISO format strings


def test_delete_transaction(db):
    # Test deleting a transaction
    env_id = db.insert_envelope("Subscriptions", 50.00, 5.00, "Streaming services")
    trans_id = db.insert_transaction(
        env_id, 10.00, "Music Subscription", date(2023, 5, 1), "expense"
    )
    deleted = db.delete_transaction(trans_id)
    assert deleted is True
    transaction = db.get_transaction_by_id(trans_id)
    assert transaction is None


def test_insert_transaction_invalid_envelope_id_raises_value_error(db):
    # Test that inserting a transaction with a non-existent envelope_id raises a ValueError
    non_existent_env_id = 999
    with pytest.raises(ValueError) as excinfo:
        db.insert_transaction(
            non_existent_env_id, 50.00, "Test Transaction", date(2023, 1, 1), "expense"
        )
    assert f"Envelope with ID {non_existent_env_id} does not exist" in str(
        excinfo.value
    )


def test_get_envelope_current_balance_no_transactions(db):
    # Test balance calculation when there are no transactions
    env_id = db.insert_envelope("Savings", 1000.00, 500.00, "Emergency fund")
    balance = db.get_envelope_current_balance(env_id)
    assert balance == 500.00  # Should be the starting balance


def test_get_envelope_current_balance_with_expenses(db):
    # Test balance calculation with only expense transactions
    env_id = db.insert_envelope("Fun Money", 200.00, 100.00, "Discretionary spending")
    db.insert_transaction(env_id, 20.00, "Movie ticket", date(2023, 6, 1), "expense")
    db.insert_transaction(
        env_id, 30.00, "Dinner with friends", date(2023, 6, 5), "expense"
    )
    balance = db.get_envelope_current_balance(env_id)
    assert balance == 50.00  # 100 - 20 - 30


def test_get_envelope_current_balance_with_income(db):
    # Test balance calculation with only income transactions
    env_id = db.insert_envelope("Side Hustle", 0.00, 0.00, "Freelance income")
    db.insert_transaction(
        env_id, 150.00, "Web design project", date(2023, 6, 10), "income"
    )
    db.insert_transaction(
        env_id, 200.00, "Tutoring session", date(2023, 6, 12), "income"
    )
    balance = db.get_envelope_current_balance(env_id)
    assert balance == 350.00  # 0 + 150 + 200


def test_get_envelope_current_balance_mixed_transactions(db):
    # Test balance calculation with a mix of income and expense transactions
    env_id = db.insert_envelope("Checking Account", 0.00, 1000.00, "Main checking")
    db.insert_transaction(
        env_id, 500.00, "Salary deposit", date(2023, 7, 1), "income"
    )  # Balance = 1500
    db.insert_transaction(
        env_id, 100.00, "Groceries", date(2023, 7, 2), "expense"
    )  # Balance = 1400
    db.insert_transaction(
        env_id, 50.00, "Refund for returned item", date(2023, 7, 3), "income"
    )  # Balance = 1450
    db.insert_transaction(
        env_id, 200.00, "Rent payment", date(2023, 7, 5), "expense"
    )  # Balance = 1250
    balance = db.get_envelope_current_balance(env_id)
    assert balance == 1250.00


def test_get_envelope_current_balance_non_existent_envelope(db):
    # Test balance calculation for a non-existent envelope ID
    balance = db.get_envelope_current_balance(999)  # Assuming 999 is not a valid ID
    assert balance is None
