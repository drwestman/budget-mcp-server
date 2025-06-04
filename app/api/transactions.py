from flask import Blueprint, request, jsonify, current_app

transactions_bp = Blueprint('transactions', __name__)

# This will be set by the app factory
transaction_service = None


def init_transaction_service(service):
    """Initialize the transaction service for this blueprint."""
    global transaction_service
    transaction_service = service


@transactions_bp.route('/', methods=['POST'])
def create_transaction_route():
    """Endpoint to create a new transaction."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON."}), 400

    envelope_id = data.get('envelope_id')
    amount = data.get('amount')
    description = data.get('description')
    date = data.get('date')
    type = data.get('type') # 'income' or 'expense'

    try:
        new_transaction = transaction_service.create_transaction(envelope_id, amount, description, date, type)
        return jsonify(new_transaction), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500


@transactions_bp.route('/', methods=['GET'])
def get_all_transactions_route():
    """Endpoint to get all transactions, or transactions for a specific envelope."""
    envelope_id = request.args.get('envelope_id', type=int)
    try:
        if envelope_id:
            transactions = transaction_service.get_transactions_by_envelope(envelope_id)
        else:
            transactions = transaction_service.get_all_transactions()
        return jsonify(transactions), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500


@transactions_bp.route('/<int:transaction_id>', methods=['GET'])
def get_transaction_route(transaction_id):
    """Endpoint to get a single transaction by ID."""
    try:
        transaction = transaction_service.get_transaction(transaction_id)
        if not transaction:
            return jsonify({"message": "Transaction not found."}), 404
        return jsonify(transaction), 200
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500


@transactions_bp.route('/<int:transaction_id>', methods=['PUT'])
def update_transaction_route(transaction_id):
    """Endpoint to update an existing transaction."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON."}), 400

    try:
        updated_transaction = transaction_service.update_transaction(
            transaction_id,
            envelope_id=data.get('envelope_id'),
            amount=data.get('amount'),
            description=data.get('description'),
            date=data.get('date'),
            type=data.get('type')
        )
        return jsonify(updated_transaction), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500


@transactions_bp.route('/<int:transaction_id>', methods=['DELETE'])
def delete_transaction_route(transaction_id):
    """Endpoint to delete a transaction."""
    try:
        transaction_service.delete_transaction(transaction_id)
        # If service call is successful, return a success message
        return jsonify({"message": "Transaction deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500