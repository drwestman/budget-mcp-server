from unittest.mock import MagicMock

import pytest

from app.models.database import (
    Database,
)  # Assuming Database is the class used by the service
from app.services.envelope_service import EnvelopeService


# Fixture for the mocked database
@pytest.fixture
def mock_db() -> MagicMock:
    db = MagicMock(spec=Database)  # Use spec for more accurate mocking
    # Setup common mock return values if needed for multiple tests
    db.get_envelope_by_category.return_value = None  # Default: category does not exist
    db.insert_envelope.return_value = 1  # Default: successful insertion returns ID 1
    db.get_envelope_by_id.return_value = {
        "id": 1,
        "category": "Test",
        "budgeted_amount": 100,
        "starting_balance": 50,
        "description": "Test desc",
        "current_balance": 50,
    }  # Default: mock fetched envelope
    db.get_envelope_current_balance.return_value = 50  # Default mock current balance
    return db


# Fixture for EnvelopeService with mocked db
@pytest.fixture
def envelope_service(mock_db: MagicMock) -> EnvelopeService:
    return EnvelopeService(db=mock_db)


# Tests for create_envelope
def test_create_envelope_success(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    category = "Groceries"
    budgeted_amount = 200.0
    starting_balance = 50.0
    description = "Monthly groceries budget"

    # Ensure get_envelope_by_category is correctly configured for this test case if needed
    mock_db.get_envelope_by_category.return_value = None
    # Define what insert_envelope should return specifically for this call
    mock_db.insert_envelope.return_value = 123
    # Define what get_envelope_by_id (called by service.get_envelope) should return after creation
    expected_envelope = {
        "id": 123,
        "category": category,
        "budgeted_amount": budgeted_amount,
        "starting_balance": starting_balance,
        "description": description,
        "current_balance": 50.0,
    }
    mock_db.get_envelope_by_id.return_value = expected_envelope
    mock_db.get_envelope_current_balance.return_value = (
        50.0  # Assuming this is called by get_envelope
    )

    created_envelope = envelope_service.create_envelope(
        category, budgeted_amount, starting_balance, description
    )

    mock_db.get_envelope_by_category.assert_called_once_with(category)
    mock_db.insert_envelope.assert_called_once_with(
        category, budgeted_amount, starting_balance, description
    )
    mock_db.get_envelope_by_id.assert_called_once_with(
        123
    )  # Ensure get_envelope was called with the new ID
    assert created_envelope is not None
    assert created_envelope["id"] == 123
    assert created_envelope["category"] == category
    assert created_envelope["budgeted_amount"] == budgeted_amount


def test_create_envelope_duplicate_category(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    category = "Utilities"
    budgeted_amount = 150.0
    starting_balance = 0.0
    description = "Monthly utilities"

    # Simulate that this category already exists
    mock_db.get_envelope_by_category.return_value = {"id": 1, "category": category}

    with pytest.raises(ValueError) as excinfo:
        envelope_service.create_envelope(
            category, budgeted_amount, starting_balance, description
        )

    assert f"Envelope with category '{category}' already exists." in str(excinfo.value)
    mock_db.insert_envelope.assert_not_called()


@pytest.mark.parametrize(
    "category, budgeted_amount, starting_balance, expected_message",
    [
        ("", 100, 50, "Category is required and must be a non-empty string."),
        ("  ", 100, 50, "Category is required and must be a non-empty string."),
        (None, 100, 50, "Category is required and must be a non-empty string."),
        ("Valid", -10, 50, "Budgeted amount must be a non-negative number."),
        ("Valid", "abc", 50, "Budgeted amount must be a non-negative number."),
        ("Valid", 100, "abc", "Starting balance must be a number."),
    ],
)
def test_create_envelope_invalid_input(
    envelope_service,
    mock_db,
    category,
    budgeted_amount,
    starting_balance,
    expected_message,
):
    with pytest.raises(ValueError) as excinfo:
        envelope_service.create_envelope(
            category, budgeted_amount, starting_balance, "Test description"
        )
    assert expected_message in str(excinfo.value)
    mock_db.insert_envelope.assert_not_called()


# Tests for get_envelope
def test_get_envelope_success(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    envelope_id = 1
    expected_db_envelope = {
        "id": envelope_id,
        "category": "Food",
        "budgeted_amount": 150,
        "starting_balance": 20,
        "description": "Food stuff",
    }
    expected_balance = 75.50

    mock_db.get_envelope_by_id.return_value = expected_db_envelope
    mock_db.get_envelope_current_balance.return_value = expected_balance

    envelope = envelope_service.get_envelope(envelope_id)

    mock_db.get_envelope_by_id.assert_called_once_with(envelope_id)
    mock_db.get_envelope_current_balance.assert_called_once_with(envelope_id)
    assert envelope is not None
    assert envelope["id"] == envelope_id
    assert envelope["category"] == "Food"
    assert envelope["current_balance"] == expected_balance


def test_get_envelope_not_found(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    envelope_id = 99  # Non-existent ID
    mock_db.get_envelope_by_id.return_value = None

    with pytest.raises(ValueError) as excinfo:
        envelope_service.get_envelope(envelope_id)

    assert f"Envelope with ID {envelope_id} not found." in str(excinfo.value)

    mock_db.get_envelope_by_id.assert_called_once_with(envelope_id)
    mock_db.get_envelope_current_balance.assert_not_called()  # Should not be called if envelope not found


# Tests for get_all_envelopes
def test_get_all_envelopes_success(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    db_envelopes = [
        {
            "id": 1,
            "category": "Rent",
            "budgeted_amount": 1000,
            "starting_balance": 1000,
            "description": "",
        },
        {
            "id": 2,
            "category": "Gas",
            "budgeted_amount": 100,
            "starting_balance": 50,
            "description": "",
        },
    ]
    balances = {1: 950, 2: 30}  # Balances keyed by envelope ID

    mock_db.get_all_envelopes.return_value = db_envelopes
    # Configure side_effect for get_envelope_current_balance
    mock_db.get_envelope_current_balance.side_effect = lambda id_val: balances.get(
        id_val, 0
    )

    envelopes = envelope_service.get_all_envelopes()

    mock_db.get_all_envelopes.assert_called_once()
    assert mock_db.get_envelope_current_balance.call_count == len(db_envelopes)
    mock_db.get_envelope_current_balance.assert_any_call(1)
    mock_db.get_envelope_current_balance.assert_any_call(2)

    assert len(envelopes) == 2
    assert envelopes[0]["id"] == 1
    assert envelopes[0]["category"] == "Rent"
    assert envelopes[0]["current_balance"] == 950
    assert envelopes[1]["id"] == 2
    assert envelopes[1]["category"] == "Gas"
    assert envelopes[1]["current_balance"] == 30


def test_get_all_envelopes_empty_result(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    mock_db.get_all_envelopes.return_value = []

    envelopes = envelope_service.get_all_envelopes()

    mock_db.get_all_envelopes.assert_called_once()
    mock_db.get_envelope_current_balance.assert_not_called()
    assert len(envelopes) == 0


# Tests for update_envelope
def test_update_envelope_success(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    envelope_id = 1
    update_data = {
        "category": "Updated Groceries",
        "budgeted_amount": 250.0,
        "starting_balance": 75.0,
        "description": "Updated monthly groceries budget",
    }
    # Mock that the new category is not taken by another envelope
    mock_db.get_envelope_by_category.return_value = None
    # Mock that the update in DB is successful
    mock_db.update_envelope.return_value = True
    # Mock the envelope that will be returned by get_envelope after update
    updated_envelope_data = {
        "id": envelope_id,
        "category": update_data["category"],
        "budgeted_amount": update_data["budgeted_amount"],
        "starting_balance": update_data["starting_balance"],
        "description": update_data["description"],
        "current_balance": 75.0,  # Example, actual balance depends on transactions
    }
    mock_db.get_envelope_by_id.return_value = updated_envelope_data
    mock_db.get_envelope_current_balance.return_value = updated_envelope_data[
        "current_balance"
    ]

    updated_envelope = envelope_service.update_envelope(envelope_id, **update_data)

    mock_db.get_envelope_by_category.assert_called_once_with(update_data["category"])
    mock_db.update_envelope.assert_called_once_with(envelope_id, **update_data)
    # get_envelope calls get_envelope_by_id and get_envelope_current_balance
    mock_db.get_envelope_by_id.assert_called_once_with(envelope_id)
    mock_db.get_envelope_current_balance.assert_called_once_with(envelope_id)

    assert updated_envelope is not None
    assert updated_envelope["category"] == update_data["category"]
    assert updated_envelope["budgeted_amount"] == update_data["budgeted_amount"]


def test_update_envelope_partial_fields(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    envelope_id = 1
    update_data = {"budgeted_amount": 300.0}

    # Original envelope data that get_envelope would return after update
    # (assuming only budgeted_amount changed)
    # In this case, get_envelope_by_category won't be called by the service
    mock_db.update_envelope.return_value = True
    final_envelope_state = {
        "id": envelope_id,
        "category": "Groceries",
        "budgeted_amount": 300.0,
        "starting_balance": 50.0,
        "description": "Test desc",
        "current_balance": 50.0,
    }
    mock_db.get_envelope_by_id.return_value = final_envelope_state
    mock_db.get_envelope_current_balance.return_value = final_envelope_state[
        "current_balance"
    ]

    updated_envelope = envelope_service.update_envelope(envelope_id, **update_data)

    mock_db.get_envelope_by_category.assert_not_called()  # Category not in update_data
    mock_db.update_envelope.assert_called_once_with(
        envelope_id,
        category=None,
        budgeted_amount=300.0,
        starting_balance=None,
        description=None,
    )
    assert updated_envelope["budgeted_amount"] == 300.0


def test_update_envelope_category_already_exists_for_another_envelope(
    envelope_service, mock_db
):
    envelope_id = 1
    new_category = "Existing Category"
    # Simulate that 'Existing Category' is used by envelope ID 2
    mock_db.get_envelope_by_category.return_value = {"id": 2, "category": new_category}

    with pytest.raises(ValueError) as excinfo:
        envelope_service.update_envelope(envelope_id, category=new_category)

    assert f"Envelope with category '{new_category}' already exists." in str(
        excinfo.value
    )
    mock_db.update_envelope.assert_not_called()


def test_update_envelope_category_already_exists_for_same_envelope_no_change(
    envelope_service, mock_db
):
    envelope_id = 1
    current_category = "My Category"
    # Simulate that 'My Category' is used by the same envelope ID 1
    # This means the category is not actually changing, so it should be allowed.
    # The service's get_envelope_by_category will be called.
    # Then, update_envelope in the DB will be called.
    # Then, the service's get_envelope will be called.

    mock_db.get_envelope_by_category.return_value = {
        "id": envelope_id,
        "category": current_category,
    }
    mock_db.update_envelope.return_value = True  # DB update is successful

    # Expected state after "update" (no actual change in category)
    expected_envelope_after_update = {
        "id": envelope_id,
        "category": current_category,
        "budgeted_amount": 100,
        "starting_balance": 50,
        "description": "Test desc",
        "current_balance": 50,
    }
    mock_db.get_envelope_by_id.return_value = expected_envelope_after_update
    mock_db.get_envelope_current_balance.return_value = 50

    updated_envelope = envelope_service.update_envelope(
        envelope_id, category=current_category, budgeted_amount=100
    )

    mock_db.get_envelope_by_category.assert_called_once_with(current_category)
    mock_db.update_envelope.assert_called_once_with(
        envelope_id,
        category=current_category,
        budgeted_amount=100,
        starting_balance=None,
        description=None,
    )
    assert updated_envelope["category"] == current_category


@pytest.mark.parametrize(
    "field, value, expected_message_part",
    [
        ("category", "", "Category must be a non-empty string."),
        ("category", "  ", "Category must be a non-empty string."),
        ("budgeted_amount", -100, "Budgeted amount must be a non-negative number."),
        (
            "budgeted_amount",
            "invalid",
            "Budgeted amount must be a non-negative number.",
        ),
        ("starting_balance", "invalid", "Starting balance must be a number."),
    ],
)
def test_update_envelope_invalid_input_types(
    envelope_service, mock_db, field, value, expected_message_part
):
    envelope_id = 1
    update_args = {field: value}

    # Reset relevant mocks for this parameterized test if they might interfere
    mock_db.get_envelope_by_category.reset_mock()

    if field == "category":
        # If category is being tested for emptiness, ensure get_envelope_by_category is not an issue
        mock_db.get_envelope_by_category.return_value = None

    with pytest.raises(ValueError) as excinfo:
        envelope_service.update_envelope(envelope_id, **update_args)

    assert expected_message_part in str(excinfo.value)
    mock_db.update_envelope.assert_not_called()


def test_update_envelope_db_failure(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    envelope_id = 1
    update_data = {"budgeted_amount": 150.0}
    mock_db.update_envelope.return_value = (
        False  # Simulate DB update failure (e.g. row not found)
    )

    with pytest.raises(ValueError) as excinfo:
        envelope_service.update_envelope(envelope_id, **update_data)

    assert (
        f"Envelope with ID {envelope_id} not found or no valid fields to update."
        in str(excinfo.value)
    )
    mock_db.update_envelope.assert_called_once_with(
        envelope_id,
        category=None,
        budgeted_amount=150.0,
        starting_balance=None,
        description=None,
    )
    # get_envelope should not be called if update_envelope itself indicated failure
    mock_db.get_envelope_by_id.assert_not_called()


# Tests for delete_envelope
def test_delete_envelope_success(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    envelope_id = 1
    # Simulate that the envelope exists before deletion
    mock_db.get_envelope_by_id.return_value = {
        "id": envelope_id,
        "category": "ToDelete",
    }
    # Assume db.delete_envelope doesn't return anything or returns a success indicator like number of rows deleted
    mock_db.delete_envelope.return_value = None

    result = envelope_service.delete_envelope(envelope_id)

    mock_db.get_envelope_by_id.assert_called_once_with(
        envelope_id
    )  # Service checks existence first
    mock_db.delete_envelope.assert_called_once_with(envelope_id)
    assert result == {
        "message": f"Envelope with ID {envelope_id} deleted successfully."
    }


def test_delete_envelope_not_found(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    envelope_id = 99  # Non-existent ID
    # Simulate that the envelope does not exist
    mock_db.get_envelope_by_id.return_value = None

    with pytest.raises(ValueError) as excinfo:
        envelope_service.delete_envelope(envelope_id)

    assert f"Envelope with ID {envelope_id} not found." in str(excinfo.value)
    mock_db.get_envelope_by_id.assert_called_once_with(envelope_id)


def test_delete_envelope_database_error(
    envelope_service: EnvelopeService, mock_db: MagicMock
) -> None:
    envelope_id = 1
    mock_db.get_envelope_by_id.return_value = {
        "id": envelope_id,
        "category": "ToDelete",
    }
    mock_db.delete_envelope.side_effect = Exception("Database error")

    with pytest.raises(Exception) as excinfo:
        envelope_service.delete_envelope(envelope_id)

    assert "Database error" in str(excinfo.value)
    mock_db.get_envelope_by_id.assert_called_once_with(envelope_id)
    mock_db.delete_envelope.assert_called_once_with(envelope_id)
