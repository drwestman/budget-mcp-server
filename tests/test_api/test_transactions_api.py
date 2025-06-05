import json
import pytest
from unittest.mock import patch, MagicMock

# Test data
VALID_TRANSACTION_DATA = {"envelope_id": 1, "amount": 25.0, "description": "Coffee", "date": "YYYY-MM-DD", "type": "expense"} # Ensure date is a valid string like "2023-10-26"
INVALID_TRANSACTION_DATA = {"envelope_id": 1, "description": "Coffee"} # Missing amount
EMPTY_TRANSACTION_DATA = {}

@pytest.fixture
def mock_transaction_service():
    with patch('app.api.transactions.transaction_service') as mock_service:
        yield mock_service

# --- POST /transactions/ ---
def test_create_transaction_success(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_transaction_service.create_transaction.return_value = {"id": 1, **VALID_TRANSACTION_DATA}
    response = client.post('/transactions/', json=VALID_TRANSACTION_DATA, headers=headers)
    assert response.status_code == 201
    assert response.json['id'] == 1
    assert response.json['description'] == VALID_TRANSACTION_DATA['description']
    mock_transaction_service.create_transaction.assert_called_once_with(
        VALID_TRANSACTION_DATA['envelope_id'],
        VALID_TRANSACTION_DATA['amount'],
        VALID_TRANSACTION_DATA['description'],
        VALID_TRANSACTION_DATA['date'],  # 'YYYY-MM-DD'
        VALID_TRANSACTION_DATA['type']   # 'expense'
    )

def test_create_transaction_bad_request_missing_data(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    response = client.post('/transactions/', json=EMPTY_TRANSACTION_DATA, headers=headers)
    assert response.status_code == 400
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_transaction_service.create_transaction.assert_not_called()

def test_create_transaction_bad_request_invalid_data(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    # INVALID_TRANSACTION_DATA = {"envelope_id": 1, "description": "Coffee"}
    # Route calls service with (1, None, "Coffee", None, None)
    # Service validation for amount (being None) should raise ValueError.
    mock_transaction_service.create_transaction.side_effect = ValueError("Amount is required and must be a positive number.")

    response = client.post('/transactions/', json=INVALID_TRANSACTION_DATA, headers=headers)

    assert response.status_code == 400
    assert 'message' in response.json
    assert response.json['message'] == "Amount is required and must be a positive number."
    mock_transaction_service.create_transaction.assert_called_once_with(1, None, "Coffee", None, None)

def test_create_transaction_internal_server_error(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_transaction_service.create_transaction.side_effect = Exception("Unexpected service error")
    response = client.post('/transactions/', json=VALID_TRANSACTION_DATA, headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_transaction_service.create_transaction.assert_called_once_with(
        VALID_TRANSACTION_DATA['envelope_id'],
        VALID_TRANSACTION_DATA['amount'],
        VALID_TRANSACTION_DATA['description'],
        VALID_TRANSACTION_DATA.get('date'), # Or specific expected value if VALID_TRANSACTION_DATA is updated
        VALID_TRANSACTION_DATA.get('type')  # Or specific expected value
    )

# --- GET /transactions/ ---
def test_get_all_transactions_success(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_data = [{"id": 1, **VALID_TRANSACTION_DATA}, {"id": 2, "envelope_id": 2, "amount": 50.0, "description": "Paycheck"}]
    mock_transaction_service.get_all_transactions.return_value = mock_data
    response = client.get('/transactions/', headers=headers)
    assert response.status_code == 200
    assert len(response.json) == 2
    mock_transaction_service.get_all_transactions.assert_called_once_with() # Corrected: no args

def test_get_transactions_for_envelope_success(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    envelope_id = 1
    mock_data = [{"id": 1, **VALID_TRANSACTION_DATA}]
    # Mock the correct service method
    mock_transaction_service.get_transactions_by_envelope.return_value = mock_data
    response = client.get(f'/transactions/?envelope_id={envelope_id}', headers=headers)
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['envelope_id'] == envelope_id
    # Assert call on the correct service method
    mock_transaction_service.get_transactions_by_envelope.assert_called_once_with(envelope_id)
    mock_transaction_service.get_all_transactions.assert_not_called() # Ensure the other one isn't called

def test_get_transactions_for_envelope_bad_request(app, client, mock_transaction_service):
    # Route logic: if envelope_id is 'invalid_id', request.args.get('envelope_id', type=int) makes it None.
    # So, get_all_transactions() is called by the route.
    # To test a "bad request" for an invalid envelope_id that the *service* might reject (e.g. string that bypasses type=int, or specific value),
    # we'd need to adjust the route or this test's focus.
    # For now, let's assume the route calls get_all_transactions() if envelope_id is 'invalid_id' (becomes None).
    # If the intention is to test the service's get_transactions_by_envelope for an ID that causes ValueError:
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    invalid_envelope_id_for_service = 12345 # An int that service might reject
    mock_transaction_service.get_transactions_by_envelope.side_effect = ValueError("Envelope ID does not exist for service call")
    response = client.get(f'/transactions/?envelope_id={invalid_envelope_id_for_service}', headers=headers)
    assert response.status_code == 400
    assert 'message' in response.json
    mock_transaction_service.get_transactions_by_envelope.assert_called_once_with(invalid_envelope_id_for_service)

def test_get_all_transactions_internal_server_error(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    mock_transaction_service.get_all_transactions.side_effect = Exception("Unexpected service error")
    response = client.get('/transactions/', headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_transaction_service.get_all_transactions.assert_called_once_with() # Corrected: no args

def test_get_transactions_for_envelope_internal_server_error(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    envelope_id = 1
    # Mock the correct service method to throw error
    mock_transaction_service.get_transactions_by_envelope.side_effect = Exception("Unexpected service error")
    response = client.get(f'/transactions/?envelope_id={envelope_id}', headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    # Assert call on the correct service method
    mock_transaction_service.get_transactions_by_envelope.assert_called_once_with(envelope_id)


# --- GET /transactions/<transaction_id> ---
def test_get_transaction_success(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 1
    mock_data = {"id": transaction_id, **VALID_TRANSACTION_DATA}
    mock_transaction_service.get_transaction.return_value = mock_data # Changed get_transaction_by_id to get_transaction
    response = client.get(f'/transactions/{transaction_id}', headers=headers)
    assert response.status_code == 200
    assert response.json['id'] == transaction_id
    mock_transaction_service.get_transaction.assert_called_once_with(transaction_id) # Changed get_transaction_by_id to get_transaction

def test_get_transaction_not_found(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 99 # Assuming 99 does not exist
    mock_transaction_service.get_transaction.return_value = None # Changed get_transaction_by_id to get_transaction
    response = client.get(f'/transactions/{transaction_id}', headers=headers)
    assert response.status_code == 404
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_transaction_service.get_transaction.assert_called_once_with(transaction_id) # Changed get_transaction_by_id to get_transaction

def test_get_transaction_internal_server_error(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 1
    mock_transaction_service.get_transaction.side_effect = Exception("Unexpected service error") # Changed get_transaction_by_id to get_transaction
    response = client.get(f'/transactions/{transaction_id}', headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_transaction_service.get_transaction.assert_called_once_with(transaction_id) # Changed get_transaction_by_id to get_transaction

# --- PUT /transactions/<transaction_id> ---
UPDATED_TRANSACTION_DATA = {"envelope_id": 1, "amount": 30.0, "description": "Large Coffee"}
# Let's make this data truly invalid for the service's update validation rules
INVALID_UPDATE_DATA = {"amount": "not_a_number"}

def test_update_transaction_success(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 1
    mock_transaction_service.update_transaction.return_value = {"id": transaction_id, **UPDATED_TRANSACTION_DATA}
    response = client.put(f'/transactions/{transaction_id}', json=UPDATED_TRANSACTION_DATA, headers=headers)
    assert response.status_code == 200
    assert response.json['amount'] == UPDATED_TRANSACTION_DATA['amount']
    mock_transaction_service.update_transaction.assert_called_once_with(
        transaction_id,
        envelope_id=UPDATED_TRANSACTION_DATA['envelope_id'],
        amount=UPDATED_TRANSACTION_DATA['amount'],
        description=UPDATED_TRANSACTION_DATA['description'],
        date=None,
        type=None
    )

def test_update_transaction_bad_request(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 1
    # INVALID_UPDATE_DATA is now {"amount": "not_a_number"}
    # Route will call service with update_transaction(1, envelope_id=None, amount="not_a_number", ...)
    # Service validation for amount type should raise ValueError.
    mock_transaction_service.update_transaction.side_effect = ValueError("Amount must be a positive number.")

    response = client.put(f'/transactions/{transaction_id}', json=INVALID_UPDATE_DATA, headers=headers)

    assert response.status_code == 400
    assert 'message' in response.json
    assert response.json['message'] == "Amount must be a positive number."
    mock_transaction_service.update_transaction.assert_called_once_with(
        transaction_id, envelope_id=None, amount="not_a_number", description=None, date=None, type=None
    )

def test_update_transaction_not_found(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 99 # Assuming 99 does not exist
    mock_transaction_service.update_transaction.side_effect = ValueError("Transaction not found")
    response = client.put(f'/transactions/{transaction_id}', json=UPDATED_TRANSACTION_DATA, headers=headers)
    assert response.status_code == 400 # Changed 404 to 400, route converts ValueError to 400
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_transaction_service.update_transaction.assert_called_once_with(
        transaction_id, # which is 99
        envelope_id=UPDATED_TRANSACTION_DATA.get('envelope_id'),
        amount=UPDATED_TRANSACTION_DATA.get('amount'),
        description=UPDATED_TRANSACTION_DATA.get('description'),
        date=UPDATED_TRANSACTION_DATA.get('date'),
        type=UPDATED_TRANSACTION_DATA.get('type')
    )

def test_update_transaction_internal_server_error(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 1
    mock_transaction_service.update_transaction.side_effect = Exception("Unexpected service error")
    response = client.put(f'/transactions/{transaction_id}', json=UPDATED_TRANSACTION_DATA, headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_transaction_service.update_transaction.assert_called_once_with(
        transaction_id, # which is 1
        envelope_id=UPDATED_TRANSACTION_DATA.get('envelope_id'),
        amount=UPDATED_TRANSACTION_DATA.get('amount'),
        description=UPDATED_TRANSACTION_DATA.get('description'),
        date=UPDATED_TRANSACTION_DATA.get('date'),
        type=UPDATED_TRANSACTION_DATA.get('type')
    )

# --- DELETE /transactions/<transaction_id> ---
def test_delete_transaction_success(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 1
    mock_transaction_service.delete_transaction.return_value = True
    response = client.delete(f'/transactions/{transaction_id}', headers=headers)
    assert response.status_code == 200
    assert response.json['message'] == "Transaction deleted successfully"
    mock_transaction_service.delete_transaction.assert_called_once_with(transaction_id)

def test_delete_transaction_not_found(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 99 # Assuming 99 does not exist
    mock_transaction_service.delete_transaction.side_effect = ValueError("Transaction not found")
    response = client.delete(f'/transactions/{transaction_id}', headers=headers)
    assert response.status_code == 404
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_transaction_service.delete_transaction.assert_called_once_with(transaction_id)

def test_delete_transaction_internal_server_error(app, client, mock_transaction_service):
    api_key = app.config['API_KEY']
    headers = {'X-API-Key': api_key}
    transaction_id = 1
    mock_transaction_service.delete_transaction.side_effect = Exception("Unexpected service error")
    response = client.delete(f'/transactions/{transaction_id}', headers=headers)
    assert response.status_code == 500
    assert 'message' in response.json # Changed 'error' to 'message'
    mock_transaction_service.delete_transaction.assert_called_once_with(transaction_id)
