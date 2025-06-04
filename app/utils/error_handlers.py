from flask import jsonify


def register_error_handlers(app):
    """Register global error handlers for the Flask app."""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            "message": "Bad Request: The server cannot process the request due to a client error (e.g., malformed request syntax, invalid request message framing, or deceptive request routing).", 
            "status_code": 400
        }), 400

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "message": "Not Found: The requested resource could not be found on the server.", 
            "status_code": 404
        }), 404

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return jsonify({
            "message": "Method Not Allowed: The method specified in the Request-Line is not allowed for the resource identified by the Request-URI.", 
            "status_code": 405
        }), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "message": "Internal Server Error: The server encountered an unexpected condition that prevented it from fulfilling the request.", 
            "status_code": 500
        }), 500