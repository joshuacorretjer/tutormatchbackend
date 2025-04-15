from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from ..models import Class, Student, Subject, Tutor, db, User
from ..utils.decorators import tutor_required, student_required, role_required
from . import api_bp


@api_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    profile_data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role
    }
    
    if user.role == 'student' and user.student_profile:
        profile_data.update({
            "major": user.student_profile.major,
            "year": user.student_profile.year
        })
    elif user.role == 'tutor' and user.tutor_profile:
        profile_data.update({
            "hourly_rate": float(user.tutor_profile.hourly_rate),
            "bio": user.tutor_profile.bio
        })
    
    return jsonify(profile_data), 200


@api_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()

    # Update base fields
    if 'email' in data:
        if User.query.filter(User.email == data['email'], User.id != user.id).first():
            return jsonify({"message": "Email already in use"}), 400
        user.email = data['email']

    if 'first_name' in data:
        user.first_name = data['first_name']
    
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    if 'password' in data:
        user.set_password(data['password'])

    # Update role-specific profile
    if user.role == 'student':
        if not user.student_profile:
            user.student_profile = Student(user_id=user.id)
        
        if 'major' in data:
            user.student_profile.major = data['major']
        if 'year' in data:
            user.student_profile.year = data['year']

    elif user.role == 'tutor':
        if not user.tutor_profile:
            user.tutor_profile = Tutor(user_id=user.id)
        
        if 'hourly_rate' in data:
            user.tutor_profile.hourly_rate = data['hourly_rate']
        if 'bio' in data:
            user.tutor_profile.bio = data.get('bio', '')

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200

@api_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_classes():
    # Shared endpoint for both roles
    classes = Class.query.join(Subject).all()
    
    return jsonify([{
        "id": str(c.id),
        "name": c.name,
        "code": c.code,
        "subject": c.subject.name
    } for c in classes]), 200