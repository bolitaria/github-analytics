"""
Módulo para autenticación y seguridad
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, g
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    def __init__(self):
        self.secret_key = os.getenv(
            "JWT_SECRET_KEY", "your-default-secret-key-change-in-production"
        )
        self.token_expiry = int(os.getenv("TOKEN_EXPIRY_HOURS", 24))

    def generate_token(self, user_id: str, username: str, roles: list = None) -> str:
        """Generar token JWT"""
        if roles is None:
            roles = ["user"]

        payload = {
            "user_id": user_id,
            "username": username,
            "roles": roles,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiry),
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verificar y decodificar token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Token inválido")
            return None

    def hash_password(self, password: str) -> str:
        """Hashear contraseña"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return salt.hex() + key.hex()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verificar contraseña"""
        salt = bytes.fromhex(hashed[:64])
        key = bytes.fromhex(hashed[64:])
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return new_key == key


# Instancia global del security manager
security_manager = SecurityManager()


def token_required(f):
    """Decorator para requerir token JWT"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Obtener token del header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token es requerido"}), 401

        # Verificar token
        payload = security_manager.verify_token(token)
        if not payload:
            return jsonify({"error": "Token inválido o expirado"}), 401

        # Agregar usuario al contexto global
        g.user = payload
        return f(*args, **kwargs)

    return decorated


def roles_required(required_roles: list):
    """Decorator para requerir roles específicos"""

    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            user_roles = g.user.get("roles", [])

            # Verificar si el usuario tiene al menos uno de los roles requeridos
            if not any(role in user_roles for role in required_roles):
                return jsonify({"error": "Permisos insuficientes"}), 403

            return f(*args, **kwargs)

        return decorated

    return decorator
