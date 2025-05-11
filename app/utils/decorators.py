from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
from app.models import User

def account_type_required(*required_account_types):
    """
    Checks if user's account_type matches any of the required types.
    Optimized to reduce database queries and improve error messages.
    
    Args:
        *required_account_types: Variable list of allowed account types
        
    Usage:
        @account_type_required('tutor')
        @account_type_required('tutor', 'admin')
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            
            # If you're including account_type in JWT claims (recommended)
            jwt_data = get_jwt()
            print("JWT Data:", jwt_data)
            if 'account_type' in jwt_data:
                if jwt_data['account_type'] in required_account_types:
                    return fn(*args, **kwargs)
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_types": required_account_types,
                    "your_type": jwt_data['account_type']
                }), 403
            
            # Fallback to database query if account_type not in JWT
            user = User.query.get(current_user)
            if not user:
                return jsonify({"error": "User not found"}), 404
                
            if user.account_type not in required_account_types:
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_types": required_account_types,
                    "your_type": user.account_type
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Specific decorators
tutor_required = account_type_required('tutor')
student_required = account_type_required('student')
admin_required = account_type_required('admin')