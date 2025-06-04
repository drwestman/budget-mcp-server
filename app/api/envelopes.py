from flask import Blueprint, request, jsonify, current_app

envelopes_bp = Blueprint('envelopes', __name__)

# This will be set by the app factory
envelope_service = None


def init_envelope_service(service):
    """Initialize the envelope service for this blueprint."""
    global envelope_service
    envelope_service = service


@envelopes_bp.route('/', methods=['POST'])
def create_envelope_route():
    """Endpoint to create a new envelope."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON."}), 400

    category = data.get('category')
    budgeted_amount = data.get('budgeted_amount')
    starting_balance = data.get('starting_balance')
    description = data.get('description')

    try:
        new_envelope = envelope_service.create_envelope(category, budgeted_amount, starting_balance, description)
        return jsonify(new_envelope), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500


@envelopes_bp.route('/', methods=['GET'])
def get_all_envelopes_route():
    """Endpoint to get all envelopes."""
    try:
        envelopes = envelope_service.get_all_envelopes()
        return jsonify(envelopes), 200
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500


@envelopes_bp.route('/<int:envelope_id>', methods=['GET'])
def get_envelope_route(envelope_id):
    """Endpoint to get a single envelope by ID."""
    try:
        envelope = envelope_service.get_envelope(envelope_id)
        if not envelope:
            return jsonify({"message": "Envelope not found."}), 404
        return jsonify(envelope), 200
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500


@envelopes_bp.route('/<int:envelope_id>', methods=['PUT'])
def update_envelope_route(envelope_id):
    """Endpoint to update an existing envelope."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON."}), 400

    try:
        updated_envelope = envelope_service.update_envelope(
            envelope_id,
            category=data.get('category'),
            budgeted_amount=data.get('budgeted_amount'),
            starting_balance=data.get('starting_balance'),
            description=data.get('description')
        )
        return jsonify(updated_envelope), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500


@envelopes_bp.route('/<int:envelope_id>', methods=['DELETE'])
def delete_envelope_route(envelope_id):
    """Endpoint to delete an envelope."""
    try:
        result = envelope_service.delete_envelope(envelope_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Internal server error in {request.endpoint}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500