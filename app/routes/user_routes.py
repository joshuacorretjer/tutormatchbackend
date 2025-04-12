from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, Student, Tutor
from . import api_bp  # Import the Blueprint from the parent package


@api_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "user_id": str(user.user_id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "account_type": user.account_type,
        "date_joined": user.date_joined.isoformat()
    }), 200


@api_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "account_type": user.account_type,
        "date_joined": user.date_joined.isoformat()
    }), 200

# Updates user's profile
@api_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()

    required_fields = ['username', 'email', 'first_name', 'last_name']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required user fields"}), 400

    # Update base user fields
    user.username = data['username']
    user.email = data['email']
    user.first_name = data['first_name']
    user.last_name = data['last_name']

    if 'password' in data:
        user.set_password(data['password'])

    # Student-specific
    if user.account_type == 'student':
        if 'major' not in data or 'year' not in data:
            return jsonify({"message": "Missing major or year for student"}), 400

        student = user.students[0] if user.students else None
        if not student:
            student = Student(user_id=user.user_id)
            db.session.add(student)

        student.major = data['major']
        student.year = data['year']

    # Tutor-specific
    elif user.account_type == 'tutor':
        if 'hourly_rate' not in data:
            return jsonify({"message": "Missing hourly_rate for tutor"}), 400

        tutor = user.tutors[0] if user.tutors else None
        if not tutor:
            tutor = Tutor(user_id=user.user_id)
            db.session.add(tutor)

        tutor.available_hours = data.get('available_hours', '')
        tutor.hourly_rate = data['hourly_rate']

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"}), 200


# Gets a specific account's account type
@api_bp.route('/users/<uuid:user_id>/account-type', methods=['GET'])
@jwt_required()
def get_account_type(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "user_id": str(user.user_id),
        "account_type": user.account_type
    }), 200

# Gets all accounts' account types
@api_bp.route('/users/account-type', methods=['GET'])
@jwt_required()
def get_all_account_types():
    users = User.query.all()
    user_list = [{
        "user_id": str(user.user_id),
        "username": user.username,
        "account_type": user.account_type
    } for user in users]

    return jsonify(user_list), 200