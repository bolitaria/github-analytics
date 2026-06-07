"""
Rutas de autenticación para la API
"""

from flask import Blueprint, g, jsonify, request

from src.auth.security import security_manager, token_required

auth_bp = Blueprint("auth", __name__)

# Usuarios demo (en producción usar una base de datos)
DEMO_USERS = {
    "admin": {
        "user_id": "1",
        "username": "admin",
        "password_hash": security_manager.hash_password("admin123"),
        "roles": ["admin", "user"],
    },
    "viewer": {
        "user_id": "2",
        "username": "viewer",
        "password_hash": security_manager.hash_password("viewer123"),
        "roles": ["user"],
    },
}


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """Endpoint de login"""
    data = request.get_json()

    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username y password son requeridos"}), 400

    username = data["username"]
    password = data["password"]

    # Verificar usuario
    user = DEMO_USERS.get(username)
    if not user or not security_manager.verify_password(
        password, user["password_hash"]
    ):
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Generar token
    token = security_manager.generate_token(
        user_id=user["user_id"], username=user["username"], roles=user["roles"]
    )

    return jsonify(
        {
            "token": token,
            "user": {
                "user_id": user["user_id"],
                "username": user["username"],
                "roles": user["roles"],
            },
        }
    )


@auth_bp.route("/api/auth/me", methods=["GET"])
@token_required
def get_current_user():
    """Obtener información del usuario actual"""
    return jsonify(
        {
            "user_id": g.user["user_id"],
            "username": g.user["username"],
            "roles": g.user["roles"],
        }
    )


@auth_bp.route("/api/auth/refresh", methods=["POST"])
@token_required
def refresh_token():
    """Refrescar token"""
    new_token = security_manager.generate_token(
        user_id=g.user["user_id"], username=g.user["username"], roles=g.user["roles"]
    )

    return jsonify({"token": new_token})
