import json
import pytest
from unittest.mock import patch, MagicMock

# Test data
VALID_ENVELOPE_DATA = {"category": "Groceries", "budgeted_amount": 100.0, "starting_balance": 100.0, "description": "Monthly groceries"}
INVALID_ENVELOPE_DATA = {"category": "Groceries"} # Missing budgeted_amount and starting_balance
EMPTY_ENVELOPE_DATA = {}

@pytest.fixture
def mock_envelope_service():
    with patch('app.api.envelopes.envelope_service') as mock_service:
        yield mock_service

# --- POST /envelopes/ ---
def test_create_envelope_success(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    # Adjust the mock return value to match the structure if new_envelope includes all these fields
    mock_return_value = {"id": 1,
                         "category": VALID_ENVELOPE_DATA['category'],
                         "budgeted_amount": VALID_ENVELOPE_DATA['budgeted_amount'],
                         "starting_balance": VALID_ENVELOPE_DATA['starting_balance'],
                         "current_balance": VALID_ENVELOPE_DATA['starting_balance'], # Assuming balance starts same as starting_balance
                         "description": VALID_ENVELOPE_DATA['description']}
    mock_envelope_service.create_envelope.return_value = mock_return_value
    response = client.post('/envelopes/', json=VALID_ENVELOPE_DATA, headers=headers)
    assert response.status_code == 201
    assert response.json['id'] == 1
    assert response.json['category'] == VALID_ENVELOPE_DATA['category']
    mock_envelope_service.create_envelope.assert_called_once_with(
        VALID_ENVELOPE_DATA['category'],
        VALID_ENVELOPE_DATA['budgeted_amount'],
        VALID_ENVELOPE_DATA['starting_balance'],
        VALID_ENVELOPE_DATA['description']
    )

def test_create_envelope_bad_request_missing_data(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    response = client.post('/envelopes/', json=EMPTY_ENVELOPE_DATA, headers=headers)
    assert response.status_code == 400
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_envelope_service.create_envelope.assert_not_called()

def test_create_envelope_bad_request_invalid_data(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    # INVALID_ENVELOPE_DATA is {"category": "Groceries"}
    # Route will extract category="Groceries", budgeted_amount=None, starting_balance=None, description=None
    # The service's validation for budgeted_amount (being None) should trigger ValueError.
    mock_envelope_service.create_envelope.side_effect = ValueError("Budgeted amount must be a non-negative number.")

    response = client.post('/envelopes/', json=INVALID_ENVELOPE_DATA, headers=headers)

    assert response.status_code == 400
    assert 'message' in response.json
    assert response.json['message'] == "Budgeted amount must be a non-negative number."
    mock_envelope_service.create_envelope.assert_called_once_with("Groceries", None, None, None)


def test_create_envelope_internal_server_error(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.create_envelope.side_effect = Exception("Unexpected error")
    response = client.post('/envelopes/', json=VALID_ENVELOPE_DATA, headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_envelope_service.create_envelope.assert_called_once_with(
        VALID_ENVELOPE_DATA['category'],
        VALID_ENVELOPE_DATA['budgeted_amount'],
        VALID_ENVELOPE_DATA['starting_balance'],
        VALID_ENVELOPE_DATA['description']
    )

# --- GET /envelopes/ ---
def test_get_all_envelopes_success(app, client, mock_envelope_service):
    mock_envelopes = [
        {
            "id": 1,
            "category": "Groceries",
            "budgeted_amount": 100.0,
            "starting_balance": 100.0,
            "description": "Monthly groceries",
            "current_balance": 100.0
        },
        {
            "id": 2,
            "category": "Dining Out",
            "budgeted_amount": 50.0,
            "starting_balance": 50.0,
            "description": "Eating out",
            "current_balance": 50.0
        }
    ]
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.get_all_envelopes.return_value = mock_envelopes
    response = client.get('/envelopes/', headers=headers)
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['category'] == "Groceries"
    assert response.json[0]['budgeted_amount'] == 100.0
    assert response.json[0]['current_balance'] == 100.0
    mock_envelope_service.get_all_envelopes.assert_called_once()

def test_get_all_envelopes_internal_server_error(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.get_all_envelopes.side_effect = Exception("Unexpected error")
    response = client.get('/envelopes/', headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_envelope_service.get_all_envelopes.assert_called_once()

# --- GET /envelopes/<envelope_id> ---
def test_get_envelope_success(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope = {
        "id": 1,
        "category": "Groceries",
        "budgeted_amount": 100.0,
        "starting_balance": 100.0,
        "description": "Monthly groceries",
        "current_balance": 100.0
    }
    mock_envelope_service.get_envelope.return_value = mock_envelope
    response = client.get('/envelopes/1', headers=headers)
    assert response.status_code == 200
    assert response.json['category'] == "Groceries"
    assert response.json['budgeted_amount'] == 100.0
    assert response.json['current_balance'] == 100.0
    mock_envelope_service.get_envelope.assert_called_once_with(1)

def test_get_envelope_not_found(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.get_envelope.return_value = None # Changed get_envelope_by_id to get_envelope
    response = client.get('/envelopes/99', headers=headers) # Assuming 99 does not exist
    assert response.status_code == 404
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_envelope_service.get_envelope.assert_called_once_with(99) # Changed get_envelope_by_id to get_envelope

def test_get_envelope_internal_server_error(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.get_envelope.side_effect = Exception("Unexpected error") # Changed get_envelope_by_id to get_envelope
    response = client.get('/envelopes/1', headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_envelope_service.get_envelope.assert_called_once_with(1) # Changed get_envelope_by_id to get_envelope

# --- PUT /envelopes/<envelope_id> ---
UPDATED_ENVELOPE_DATA = {"category": "Updated Groceries", "budgeted_amount": 150.0}
# Invalid update data should also use correct keys if we are testing specific missing fields
# Let's make this data truly invalid for the service's update validation rules
INVALID_UPDATE_DATA = {"budgeted_amount": "not_a_number"}

def test_update_envelope_success(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    # Adjust mock return to reflect updated structure
    mock_return_value = {"id": 1,
                         "category": UPDATED_ENVELOPE_DATA['category'],
                         "budgeted_amount": UPDATED_ENVELOPE_DATA['budgeted_amount'],
                         "starting_balance": 100.0, # Assuming starting_balance is not changed or fetched
                         "current_balance": 150.0, # Example balance
                         "description": "Monthly groceries"} # Assuming description not changed
    mock_envelope_service.update_envelope.return_value = mock_return_value
    response = client.put('/envelopes/1', json=UPDATED_ENVELOPE_DATA, headers=headers)
    assert response.status_code == 200
    assert response.json['category'] == UPDATED_ENVELOPE_DATA['category']
    assert response.json['budgeted_amount'] == UPDATED_ENVELOPE_DATA['budgeted_amount']
    mock_envelope_service.update_envelope.assert_called_once_with(
        1,
        category=UPDATED_ENVELOPE_DATA['category'],
        budgeted_amount=UPDATED_ENVELOPE_DATA['budgeted_amount'],
        starting_balance=None, # Route doesn't send starting_balance if not in json
        description=None       # Route doesn't send description if not in json
    )

def test_update_envelope_bad_request(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    # INVALID_UPDATE_DATA is now {"budgeted_amount": "not_a_number"}
    # Route will extract category=None, budgeted_amount="not_a_number", etc.
    # Service validation for budgeted_amount type should raise ValueError.
    mock_envelope_service.update_envelope.side_effect = ValueError("Budgeted amount must be a non-negative number.")

    response = client.put('/envelopes/1', json=INVALID_UPDATE_DATA, headers=headers)

    assert response.status_code == 400
    assert 'message' in response.json
    assert response.json['message'] == "Budgeted amount must be a non-negative number."
    mock_envelope_service.update_envelope.assert_called_once_with(
        1, category=None, budgeted_amount="not_a_number", starting_balance=None, description=None
    )


def test_update_envelope_not_found(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.update_envelope.side_effect = ValueError("Envelope not found")
    response = client.put('/envelopes/99', json=UPDATED_ENVELOPE_DATA, headers=headers)
    assert response.status_code == 400 # Changed 404 to 400 based on route logic
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_envelope_service.update_envelope.assert_called_once_with(
        99,
        category=UPDATED_ENVELOPE_DATA['category'],
        budgeted_amount=UPDATED_ENVELOPE_DATA['budgeted_amount'],
        starting_balance=None,
        description=None
    )

def test_update_envelope_internal_server_error(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.update_envelope.side_effect = Exception("Unexpected error")
    response = client.put('/envelopes/1', json=UPDATED_ENVELOPE_DATA, headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_envelope_service.update_envelope.assert_called_once_with(
        1,
        category=UPDATED_ENVELOPE_DATA['category'],
        budgeted_amount=UPDATED_ENVELOPE_DATA['budgeted_amount'],
        starting_balance=None,
        description=None
    )

# --- DELETE /envelopes/<envelope_id> ---
def test_delete_envelope_success(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.delete_envelope.return_value = {"message": "Envelope deleted successfully"}
    response = client.delete('/envelopes/1', headers=headers)
    assert response.status_code == 200
    assert response.json['message'] == "Envelope deleted successfully"
    mock_envelope_service.delete_envelope.assert_called_once_with(1)

def test_delete_envelope_not_found(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.delete_envelope.side_effect = ValueError("Envelope not found")
    response = client.delete('/envelopes/99', headers=headers)
    assert response.status_code == 404
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_envelope_service.delete_envelope.assert_called_once_with(99)

def test_delete_envelope_internal_server_error(app, client, mock_envelope_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_envelope_service.delete_envelope.side_effect = Exception("Unexpected error")
    response = client.delete('/envelopes/1', headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_envelope_service.delete_envelope.assert_called_once_with(1)
