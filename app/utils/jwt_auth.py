from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, request, jsonify, g

from app.models import User


def issue_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "role": user.role.value,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=current_app.config["JWT_ACCESS_TOKEN_EXPIRES_MINUTES"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def jwt_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing bearer token"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        user = User.query.get(payload["sub"])
        if not user or not user.is_active_account:
            return jsonify({"error": "Account not found or inactive"}), 401
        g.current_api_user = user
        return view_func(*args, **kwargs)

    return wrapped
