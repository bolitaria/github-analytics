# src/auth/middleware.py
from functools import wraps
from flask import request, jsonify, g
from .utils import verify_token


def jwt_required(f):
    """Decorador para proteger rutas con JWT"""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token missing or invalid"}), 401

        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Guardar información del usuario en el contexto de la petición
        g.current_user = payload.get("sub")
        g.user_role = payload.get("role", "user")
        return f(*args, **kwargs)

    return decorated


def get_current_user():
    """Obtiene el usuario actual desde el contexto de Flask (g)"""
    return getattr(g, "current_user", None)
