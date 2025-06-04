from functools import wraps
from flask import request, jsonify


def require_api_key(api_key):
    """
    Decorator factory to enforce API key authentication for routes.
    Args:
        api_key (str): The expected API key value
    """
    def decorator(view_function):
        @wraps(view_function)
        def decorated_function(*args, **kwargs):
            if request.headers.get('X-API-Key') and request.headers.get('X-API-Key') == api_key:
                return view_function(*args, **kwargs)
            else:
                return jsonify({"message": "Unauthorized: Invalid or missing API Key."}), 401
        return decorated_function
    return decorator