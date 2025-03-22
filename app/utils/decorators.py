from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt

def admin_required(fn):
    @wraps(fn)  # Preserves the original function's metadata
    @jwt_required()  # Ensures the user is authenticated
    def wrapper(*args, **kwargs):
        claims = get_jwt()  # Get the JWT claims
        if claims.get("account_type") != "admin":  # Check if the user is an admin
            return jsonify({"message": "Admins only!"}), 403  # Forbidden
        return fn(*args, **kwargs)  # Allow access if the user is an admin
    return wrapper
