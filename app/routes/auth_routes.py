from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from ..models import Class, User, Student, Tutor
from ..extensions import db, jwt
from werkzeug.security import generate_password_hash
from . import api_bp  # Import the Blueprint from the parent package
import uuid


# Token blacklist (consider using Redis in production)
blacklist = set()

@api_bp.route('/register', methods=['POST'])
def register():

    data = request.get_json()
    if data is None:
        return jsonify({"message": "Invalid JSON"}), 400
    

    # Validate required fields
    required_fields = ['username', 'email', 'first_name', 'last_name', 'account_type', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    # Check existing users
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Username exists"}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email exists"}), 400

    # Create user
    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        account_type=data['account_type']
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush() 
    
    try:
        # Create profile
        if user.account_type == 'student':
            if 'major' not in data or 'year' not in data:
                raise ValueError("Missing student fields")
                
            student = Student(
                user_id=user.id,
                major=data['major'],
                year=int(data['year'])  # for student
            )
            db.session.add(student)

        elif user.account_type == 'tutor':
            if 'hourly_rate' not in data:
                raise ValueError("Missing hourly_rate")
                
            tutor = Tutor(
                user_id=user.id,
                hourly_rate=float(data['hourly_rate']),  # for tutor
                available_hours=data.get('available_hours', '')
            )
            db.session.add(tutor)

        db.session.commit()
        return jsonify({
            "message": "User registered successfully",
            "user_id": str(user.id)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400
    
@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials"}), 401

    # Include role in JWT claims
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}  
    )
    return jsonify(access_token=access_token), 200

@api_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    blacklist.add(jti)
    return jsonify({"message": "Logged out"}), 200

# --- JWT Handlers ---
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in blacklist

@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user.id)  # Ensures identity is UUID string

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.get(uuid.UUID(identity))

