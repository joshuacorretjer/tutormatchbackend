from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from ..models import User
from ..extensions import db, login_manager, jwt
from . import api_bp  # Import the Blueprint from the parent package

# Token blacklist for logout
blacklist = set()


@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate required fields
    required_fields = ['username', 'email', 'first_name',
                       'last_name', 'account_type', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Username already exists"}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already exists"}), 400

    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        account_type=data['account_type']
    )
    user.set_password(data['password'])  # Hash the password
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "user_id": str(user.user_id)}), 201


@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username_or_email = data.get('username_or_email')
    password = data.get('password')

    if not username_or_email or not password:
        return jsonify({"message": "Username/email and password are required"}), 400

    # Find user by username or email
    user = User.query.filter(
        (User.username == username_or_email) | (
            User.email == username_or_email)
    ).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.user_id))
        return jsonify(access_token=access_token), 200

    return jsonify({"message": "Invalid credentials"}), 401


@api_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']  # Get the JWT ID
    blacklist.add(jti)      # Add the JWT ID to the blacklist
    return jsonify({"message": "Successfully logged out"}), 200

# Token revocation check
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']  # Get the JWT ID
    print("Checking if token is revoked:", jti)  # Debugging
    return jti in blacklist   # Check if the JWT ID is in the blacklist

