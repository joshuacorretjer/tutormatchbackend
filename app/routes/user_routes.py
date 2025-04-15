from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity, 
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import Class, User, Student, Tutor, Subject
from ..extensions import db, jwt
from ..utils.decorators import tutor_required, student_required, account_type_required
import uuid

api_bp = Blueprint('api', __name__)

# Token blacklist (consider using Redis in production)
blacklist = set()

# ======================
# Authentication Routes
# ======================

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Validate required fields
    required_fields = {
        'all': ['username', 'email', 'first_name', 'last_name', 'account_type', 'password'],
        'student': ['major', 'year'],
        'tutor': ['hourly_rate']
    }

    missing_fields = [f for f in required_fields['all'] if f not in data]
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    # Check existing users
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 409

    # Validate role-specific fields
    if data['account_type'] == 'student':
        missing = [f for f in required_fields['student'] if f not in data]
    elif data['account_type'] == 'tutor':
        missing = [f for f in required_fields['tutor'] if f not in data]
    else:
        return jsonify({"error": "Invalid account type"}), 400

    if missing:
        return jsonify({"error": f"Missing fields for {data['account_type']}: {', '.join(missing)}"}), 400

    try:
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

        # Create profile
        if user.account_type == 'student':
            profile = Student(
                user_id=user.id,
                major=data['major'],
                year=int(data['year']))
        else:
            profile = Tutor(
                user_id=user.id,
                hourly_rate=float(data['hourly_rate']),
                bio=data.get('bio', '')
            )
        db.session.add(profile)
        db.session.commit()

        return jsonify({
            "message": "User registered successfully",
            "user_id": str(user.id),
            "account_type": user.account_type
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username_or_email = data.get('username_or_email')  # Match JSON key exactly
    password = data.get('password')

    if not username_or_email or not password:
        return jsonify({"message": "Username / email and password are required"}), 400

    user = User.query.filter(
        (User.username == username_or_email) | 
        (User.email == username_or_email)
    ).first()

    if user and user.check_password(password):
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"account_type": user.account_type}
        )
        return jsonify(access_token=access_token), 200

    return jsonify({"message": "Invalid credentials"}), 401

@api_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']  # Get the JWT ID
    blacklist.add(jti)      # Add the JWT ID to the blacklist
    return jsonify({"message": "Successfully logged out"}), 200
# ======================
# Shared Routes
# ======================

@api_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    profile_data = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "account_type": user.account_type,
        "date_joined": user.date_joined.isoformat()
    }
    
    if user.account_type == 'student' and user.student_profile:
        profile_data.update({
            "major": user.student_profile.major,
            "year": user.student_profile.year
        })
    elif user.account_type == 'tutor' and user.tutor_profile:
        profile_data.update({
            "hourly_rate": float(user.tutor_profile.hourly_rate),
            "bio": user.tutor_profile.bio,
            "average_rating": user.tutor_profile.calculate_average_rating()
        })
    
    return jsonify(profile_data), 200

@api_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # Update base user fields
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({"error": "Email already in use"}), 409
            user.email = data['email']

        for field in ['first_name', 'last_name']:
            if field in data:
                setattr(user, field, data[field])

        if 'password' in data:
            user.set_password(data['password'])

        # Update profile-specific fields
        if user.account_type == 'student':
            for field in ['major', 'year']:
                if field in data:
                    setattr(user.student_profile, field, data[field])
        else:
            if 'hourly_rate' in data:
                user.tutor_profile.hourly_rate = float(data['hourly_rate'])
            if 'bio' in data:
                user.tutor_profile.bio = data['bio']

        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@api_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_classes():
    classes = Class.query.options(db.joinedload(Class.subject)).all()
    
    return jsonify([{
        "id": str(c.id),
        "subject": {
            "id": str(c.subject.id),
            "name": c.subject.name,
            "code": c.subject.code
        },
        "section": c.section,
        "tutor_count": len(c.tutors)
    } for c in classes]), 200

# JWT

# Token revocation check
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']  # Get the JWT ID
    print("Checking if token is revoked:", jti)  # Debugging
    return jti in blacklist   # Check if the JWT ID is in the blacklist

# Checks JWT claims
@api_bp.route('/debug-token', methods=['GET'])
@jwt_required()
def debug_token():
    claims = get_jwt()  # Get JWT claims
    return jsonify(claims), 200