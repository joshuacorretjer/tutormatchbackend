from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User  # Import your User model

def account_type_required(*required_account_types):
    """
    Checks if user's account_type matches any of the required types.
    Replaces the role_required decorator to work with your account_type field.
    Usage: @account_type_required('tutor') or @account_type_required('tutor', 'admin')
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            # Get the user ID from JWT
            user_id = get_jwt_identity()
            
            # Fetch the user from database
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({"error": "User not found"}), 404
                
            if user.account_type not in required_account_types:
                return jsonify({
                    "error": f"Requires one of these account types: {', '.join(required_account_types)}"
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Specific decorators for your account types
tutor_required = account_type_required('tutor')
student_required = account_type_required('student')
staff_required = account_type_required('tutor', 'admin')  # For tutor+admin access