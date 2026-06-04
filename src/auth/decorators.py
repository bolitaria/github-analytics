from functools import wraps

from flask import jsonify, request

from src.auth.utils import decode_token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return jsonify({"error": "Token missing or invalid"}), 401
        token = token.split(" ")[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        # Payload debe contener "username" y "role"
        return f(payload, *args, **kwargs)

    return decorated
