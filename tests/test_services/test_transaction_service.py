from datetime import date as date_class
from unittest.mock import MagicMock

import pytest

from app.models.database import Database  # Assuming this is the DB class used
from app.services.transaction_service import TransactionService


# Fixture for the mocked database, similar to the one in envelope service tests
@pytest.fixture
def mock_db() -> MagicMock:
    db = MagicMock(spec=Database)
    # Default mock return values for common DB calls in TransactionService
    db.get_envelope_by_id.return_value = {
        "id": 1,
        "name": "Test Envelope",
    }  # Default: envelope exists
    db.insert_transaction.return_value = (
        101  # Default: successful insertion returns ID 101
    )
    # Default: mock fetched transaction
    db.get_transaction_by_id.return_value = {
        "id": 101,
        "envelope_id": 1,
        "amount": 50,
        "description": "Test transaction",
        "date": "2024-01-01",
        "type": "expense",
    }
    return db


# Fixture for TransactionService with mocked db
@pytest.fixture
def transaction_service(mock_db: MagicMock) -> TransactionService:
    return TransactionService(db=mock_db)


# Tests for create_transaction
def test_create_transaction_success(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    envelope_id = 1
    amount = 50.75
    description = "Lunch"
    date = "2024-07-25"
    type = "expense"

    # Ensure the envelope exists for this test
    mock_db.get_envelope_by_id.return_value = {
        "id": envelope_id,
        "name": "Food Envelope",
    }
    # Define what insert_transaction should return
    mock_db.insert_transaction.return_value = 201
    # Define what get_transaction_by_id (called by service.get_transaction) should return
    expected_transaction = {
        "id": 201,
        "envelope_id": envelope_id,
        "amount": amount,
        "description": description,
        "date": date,
        "type": type,
    }
    mock_db.get_transaction_by_id.return_value = expected_transaction

    created_transaction = transaction_service.create_transaction(
        envelope_id, amount, description, date, type
    )

    mock_db.get_envelope_by_id.assert_called_once_with(envelope_id)
    mock_db.insert_transaction.assert_called_once_with(
        envelope_id, amount, description, date_class(2024, 7, 25), type
    )
    mock_db.get_transaction_by_id.assert_called_once_with(
        201
    )  # Ensure get_transaction was called

    assert created_transaction is not None
    assert created_transaction["id"] == 201
    assert created_transaction["amount"] == amount
    assert created_transaction["type"] == "expense"


def test_create_transaction_nonexistent_envelope(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    envelope_id = 99  # Non-existent envelope
    mock_db.get_envelope_by_id.return_value = None  # Simulate envelope not found

    with pytest.raises(ValueError) as excinfo:
        transaction_service.create_transaction(
            envelope_id, 50, "Test", "2024-01-01", "expense"
        )

    assert f"Envelope with ID {envelope_id} does not exist." in str(excinfo.value)
    mock_db.insert_transaction.assert_not_called()


@pytest.mark.parametrize(
    "amount, date, type, expected_message",
    [
        (
            0,
            "2024-01-01",
            "expense",
            "Amount is required and must be a positive number.",
        ),
        (
            -10,
            "2024-01-01",
            "expense",
            "Amount is required and must be a positive number.",
        ),
        (
            "abc",
            "2024-01-01",
            "expense",
            "Amount is required and must be a positive number.",
        ),
        (50, "", "expense", "Date is required and must be a string (YYYY-MM-DD)."),
        (50, None, "expense", "Date is required and must be a string (YYYY-MM-DD)."),
        (50, "2024-01-01", "invalid_type", "Type must be 'income' or 'expense'."),
        (50, "2024-01-01", "", "Type must be 'income' or 'expense'."),
    ],
)
def test_create_transaction_invalid_input(
    transaction_service: TransactionService,
    mock_db: MagicMock,
    amount: float,
    date: str,
    type: str,
    expected_message: str,
) -> None:
    envelope_id = 1
    # Ensure envelope exists for these tests, so other validations are triggered
    mock_db.get_envelope_by_id.return_value = {
        "id": envelope_id,
        "name": "Test Envelope",
    }

    with pytest.raises(ValueError) as excinfo:
        transaction_service.create_transaction(
            envelope_id, amount, "Test desc", date, type
        )

    assert expected_message in str(excinfo.value)
    mock_db.insert_transaction.assert_not_called()


# Tests for get_transaction
def test_get_transaction_success(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    transaction_id = 101
    expected_db_transaction = {
        "id": transaction_id,
        "envelope_id": 1,
        "amount": 75,
        "description": "Dinner",
        "date": "2024-07-26",
        "type": "expense",
    }
    mock_db.get_transaction_by_id.return_value = expected_db_transaction

    transaction = transaction_service.get_transaction(transaction_id)

    mock_db.get_transaction_by_id.assert_called_once_with(transaction_id)
    assert transaction is not None
    assert transaction["id"] == transaction_id
    assert transaction["description"] == "Dinner"


def test_get_transaction_not_found(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    transaction_id = 999  # Non-existent ID
    mock_db.get_transaction_by_id.return_value = None

    with pytest.raises(ValueError) as excinfo:
        transaction_service.get_transaction(transaction_id)

    assert f"Transaction with ID {transaction_id} not found." in str(excinfo.value)
    mock_db.get_transaction_by_id.assert_called_once_with(transaction_id)


# Tests for get_transactions_by_envelope
def test_get_transactions_by_envelope_success(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    envelope_id = 1
    # Simulate envelope exists
    mock_db.get_envelope_by_id.return_value = {
        "id": envelope_id,
        "name": "Test Envelope",
    }
    expected_db_transactions = [
        {
            "id": 101,
            "envelope_id": envelope_id,
            "amount": 50,
            "description": "Gas",
            "date": "2024-01-01",
            "type": "expense",
        },
        {
            "id": 102,
            "envelope_id": envelope_id,
            "amount": 120,
            "description": "Salary",
            "date": "2024-01-02",
            "type": "income",
        },
    ]
    mock_db.get_transactions_for_envelope.return_value = expected_db_transactions

    transactions = transaction_service.get_transactions_by_envelope(envelope_id)

    mock_db.get_envelope_by_id.assert_called_once_with(
        envelope_id
    )  # Service checks if envelope exists
    mock_db.get_transactions_for_envelope.assert_called_once_with(envelope_id)
    assert len(transactions) == 2
    assert transactions[0]["id"] == 101


def test_get_transactions_by_envelope_nonexistent_envelope(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    envelope_id = 99  # Non-existent envelope
    mock_db.get_envelope_by_id.return_value = None  # Simulate envelope not found

    with pytest.raises(ValueError) as excinfo:
        transaction_service.get_transactions_by_envelope(envelope_id)

    assert f"Envelope with ID {envelope_id} does not exist." in str(excinfo.value)
    mock_db.get_transactions_for_envelope.assert_not_called()


def test_get_transactions_by_envelope_empty_result(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    envelope_id = 2
    mock_db.get_envelope_by_id.return_value = {
        "id": envelope_id,
        "name": "Empty Envelope",
    }
    mock_db.get_transactions_for_envelope.return_value = []  # No transactions for this envelope

    transactions = transaction_service.get_transactions_by_envelope(envelope_id)

    mock_db.get_envelope_by_id.assert_called_once_with(envelope_id)
    mock_db.get_transactions_for_envelope.assert_called_once_with(envelope_id)
    assert len(transactions) == 0


# Tests for get_all_transactions
def test_get_all_transactions_success(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    all_db_transactions = [
        {
            "id": 101,
            "envelope_id": 1,
            "amount": 50,
            "description": "Gas",
            "date": "2024-01-01",
            "type": "expense",
        },
        {
            "id": 201,
            "envelope_id": 2,
            "amount": 1200,
            "description": "Salary",
            "date": "2024-01-02",
            "type": "income",
        },
    ]
    mock_db.get_all_transactions.return_value = all_db_transactions

    transactions = transaction_service.get_all_transactions()

    mock_db.get_all_transactions.assert_called_once()
    assert len(transactions) == 2
    assert transactions[1]["id"] == 201


def test_get_all_transactions_empty_result(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    mock_db.get_all_transactions.return_value = []

    transactions = transaction_service.get_all_transactions()

    mock_db.get_all_transactions.assert_called_once()
    assert len(transactions) == 0


# Tests for update_transaction
def test_update_transaction_success(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    transaction_id = 101
    update_data = {
        "envelope_id": 2,  # Changing envelope
        "amount": 75.25,
        "description": "Updated lunch expense",
        "date": "2024-07-27",
        "type": "expense",
    }
    # Mock that the new envelope_id exists
    mock_db.get_envelope_by_id.return_value = {
        "id": update_data["envelope_id"],
        "name": "New Envelope",
    }
    # Mock that the DB update is successful
    mock_db.update_transaction.return_value = True
    # Mock the transaction data that will be returned by get_transaction after update
    updated_transaction_data = {"id": transaction_id, **update_data}
    mock_db.get_transaction_by_id.return_value = updated_transaction_data

    updated_transaction = transaction_service.update_transaction(
        transaction_id, **update_data
    )

    mock_db.get_envelope_by_id.assert_called_once_with(update_data["envelope_id"])
    # Expected data with parsed date
    expected_update_data = {
        "envelope_id": 2,
        "amount": 75.25,
        "description": "Updated lunch expense",
        "date": date_class(2024, 7, 27),
        "type": "expense",
    }
    mock_db.update_transaction.assert_called_once_with(
        transaction_id, **expected_update_data
    )
    mock_db.get_transaction_by_id.assert_called_once_with(
        transaction_id
    )  # From service's get_transaction call

    assert updated_transaction is not None
    assert updated_transaction["amount"] == update_data["amount"]
    assert updated_transaction["envelope_id"] == update_data["envelope_id"]


def test_update_transaction_partial_fields(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    transaction_id = 102
    update_data = {"description": "Just a new description"}

    # Original transaction that get_transaction would return after update
    # (assuming only description changed)
    # In this case, get_envelope_by_id won't be called by the service
    mock_db.update_transaction.return_value = True
    final_transaction_state = {
        "id": transaction_id,
        "envelope_id": 1,
        "amount": 50,
        "description": "Just a new description",
        "date": "2024-01-01",
        "type": "expense",
    }
    mock_db.get_transaction_by_id.return_value = final_transaction_state

    updated_transaction = transaction_service.update_transaction(
        transaction_id, **update_data
    )

    mock_db.get_envelope_by_id.assert_not_called()  # envelope_id not in update_data
    # Construct expected call to update_transaction, ensuring None for unspecified fields
    expected_call_args = {
        "envelope_id": None,
        "amount": None,
        "description": "Just a new description",
        "date": None,
        "type": None,
    }
    mock_db.update_transaction.assert_called_once_with(
        transaction_id, **expected_call_args
    )
    assert updated_transaction["description"] == "Just a new description"


def test_update_transaction_invalid_envelope(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    transaction_id = 103
    invalid_envelope_id = 999
    update_data = {"envelope_id": invalid_envelope_id, "amount": 100.0}

    # Simulate that the target envelope_id for update does not exist
    mock_db.get_envelope_by_id.return_value = None

    with pytest.raises(ValueError) as excinfo:
        transaction_service.update_transaction(transaction_id, **update_data)

    assert f"Envelope with ID {invalid_envelope_id} does not exist." in str(
        excinfo.value
    )
    mock_db.update_transaction.assert_not_called()


@pytest.mark.parametrize(
    "field, value, expected_message_part",
    [
        ("amount", 0, "Amount must be a positive number."),
        ("amount", -20, "Amount must be a positive number."),
        ("amount", "invalid", "Amount must be a positive number."),
        ("date", "", "Date must be a string (YYYY-MM-DD)."),
        ("date", 123, "Date must be a string (YYYY-MM-DD)."),
        ("type", "other", "Type must be 'income' or 'expense'."),
    ],
)
def test_update_transaction_invalid_input_types(
    transaction_service, mock_db, field, value, expected_message_part
):
    transaction_id = 104
    update_args = {field: value}

    # Reset get_envelope_by_id mock if it was set by a previous test, ensure it doesn't interfere
    # if envelope_id is part of the update_args (it's not in these parameterized tests)
    mock_db.get_envelope_by_id.reset_mock()
    # Default behavior for get_envelope_by_id if 'envelope_id' is in update_args
    # (not strictly necessary here as these tests don't update envelope_id, but good practice)
    mock_db.get_envelope_by_id.return_value = {"id": 1, "name": "Default Envelope"}

    with pytest.raises(ValueError) as excinfo:
        transaction_service.update_transaction(transaction_id, **update_args)

    assert expected_message_part in str(excinfo.value)
    mock_db.update_transaction.assert_not_called()


def test_update_transaction_db_failure(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    transaction_id = 105
    update_data = {"amount": 150.0}
    # Simulate DB update failure (e.g. row not found for transaction_id)
    mock_db.update_transaction.return_value = False
    # Ensure get_envelope_by_id is not called if envelope_id is not in update_data
    mock_db.get_envelope_by_id.reset_mock()

    with pytest.raises(ValueError) as excinfo:
        transaction_service.update_transaction(transaction_id, **update_data)

    expected_call_args = {
        "envelope_id": None,
        "amount": update_data.get("amount"),
        "description": None,
        "date": None,
        "type": None,
    }
    expected_message = (
        f"Transaction with ID {transaction_id} not found or no valid fields to update."
    )
    assert expected_message in str(excinfo.value)
    mock_db.update_transaction.assert_called_once_with(
        transaction_id, **expected_call_args
    )
    mock_db.get_transaction_by_id.assert_not_called()  # Service's get_transaction shouldn't be called


# Tests for delete_transaction
def test_delete_transaction_success(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    transaction_id = 101
    # Simulate that the transaction exists before deletion
    mock_db.get_transaction_by_id.return_value = {"id": transaction_id, "amount": 50}
    # Assume db.delete_transaction doesn't return anything or returns a success indicator
    mock_db.delete_transaction.return_value = None

    result = transaction_service.delete_transaction(transaction_id)

    # Service first calls get_transaction_by_id to check existence (implicitly, part of its logic)
    # Then, if it exists, it calls db.delete_transaction
    # The current service code for delete_transaction calls get_transaction_by_id first.
    mock_db.get_transaction_by_id.assert_called_once_with(transaction_id)
    mock_db.delete_transaction.assert_called_once_with(transaction_id)
    assert result == {
        "message": f"Transaction with ID {transaction_id} deleted successfully."
    }


def test_delete_transaction_not_found(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    transaction_id = 999  # Non-existent ID
    # Simulate that the transaction does not exist
    mock_db.get_transaction_by_id.return_value = None

    with pytest.raises(ValueError) as excinfo:
        transaction_service.delete_transaction(transaction_id)

    assert f"Transaction with ID {transaction_id} not found." in str(excinfo.value)
    mock_db.get_transaction_by_id.assert_called_once_with(transaction_id)


def test_delete_transaction_database_error(
    transaction_service: TransactionService, mock_db: MagicMock
) -> None:
    transaction_id = 101
    mock_db.get_transaction_by_id.return_value = {"id": transaction_id, "amount": 50}
    mock_db.delete_transaction.side_effect = Exception("Database error")

    with pytest.raises(Exception) as excinfo:
        transaction_service.delete_transaction(transaction_id)

    assert "Database error" in str(excinfo.value)
    mock_db.get_transaction_by_id.assert_called_once_with(transaction_id)
    mock_db.delete_transaction.assert_called_once_with(transaction_id)
