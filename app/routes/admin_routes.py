from uuid import UUID
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..models import db, Subject, Class, User, Student, Tutor, TimeSlot
from ..utils.decorators import admin_required
from . import api_bp

# --- Helper Functions ---
def validate_uuid(uuid_str):
    try:
        return UUID(uuid_str)
    except ValueError:
        return None

def get_profile_data(user):
    """Extracts role-specific profile data"""
    if user.role == 'student' and user.student_profile:
        return {"major": user.student_profile.major, "year": user.student_profile.year}
    elif user.role == 'tutor' and user.tutor_profile:
        return {
            "hourly_rate": float(user.tutor_profile.hourly_rate),
            "bio": user.tutor_profile.bio,
            "classes": [str(c.id) for c in user.tutor_profile.classes]
        }
    return None

# --- User Management ---
@api_bp.route('/admin/users', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json()
    
    # Validate required fields
    required = ['email', 'password', 'first_name', 'last_name', 'role']
    if missing := [f for f in required if f not in data]:
        return jsonify({"message": f"Missing fields: {', '.join(missing)}"}), 400

    # Check email uniqueness
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already exists"}), 400

    # Create user
    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=data['role']
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()  # Get user ID before commit

    # Create profile
    if user.role == 'student':
        profile = Student(
            user_id=user.id,
            major=data.get('major', 'Undeclared'),
            year=data.get('year', 1)
        )
    elif user.role == 'tutor':
        profile = Tutor(
            user_id=user.id,
            hourly_rate=data.get('hourly_rate', 0.0),
            bio=data.get('bio', '')
        )
        if 'classes' in data:  # Assign classes if provided
            profile.classes = Class.query.filter(Class.id.in_(data['classes'])).all()
    
    if user.role in ('student', 'tutor'):
        db.session.add(profile)

    db.session.commit()
    return jsonify({
        "message": "User created",
        "user_id": str(user.id),
        "role": user.role
    }), 201

@api_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.options(
        db.joinedload(User.student_profile),
        db.joinedload(User.tutor_profile)
    ).all()
    
    return jsonify([{
        "id": str(u.id),
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "role": u.role,
        "profile": get_profile_data(u)
    } for u in users]), 200

@api_bp.route('/admin/users/<uuid:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.json
    if 'email' in data and data['email'] != user.email:
        if User.query.filter(User.email == data['email']).first():
            return jsonify({"message": "Email already in use"}), 400
        user.email = data['email']

    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    
    # Handle role changes
    if 'role' in data and data['role'] != user.role:
        # Delete old profile
        if user.role == 'student' and user.student_profile:
            db.session.delete(user.student_profile)
        elif user.role == 'tutor' and user.tutor_profile:
            db.session.delete(user.tutor_profile)
        
        # Create new profile
        user.role = data['role']
        if user.role == 'student':
            user.student_profile = Student(
                major=data.get('major', 'Undeclared'),
                year=data.get('year', 1)
            )
        elif user.role == 'tutor':
            user.tutor_profile = Tutor(
                hourly_rate=data.get('hourly_rate', 0.0),
                bio=data.get('bio', '')
            )

    # Update profile data
    if user.role == 'student' and user.student_profile:
        user.student_profile.major = data.get('major', user.student_profile.major)
        user.student_profile.year = data.get('year', user.student_profile.year)
    elif user.role == 'tutor' and user.tutor_profile:
        user.tutor_profile.hourly_rate = data.get('hourly_rate', user.tutor_profile.hourly_rate)
        user.tutor_profile.bio = data.get('bio', user.tutor_profile.bio)
        if 'classes' in data:
            user.tutor_profile.classes = Class.query.filter(Class.id.in_(data['classes'])).all()

    db.session.commit()
    return jsonify({"message": "User updated"}), 200

# --- Subject/Class Management ---
@api_bp.route('/admin/subjects', methods=['POST'])
@admin_required
def create_subject():
    if not (name := request.json.get('name')):
        return jsonify({"message": "Subject name required"}), 400
    
    subject = Subject(name=name)
    db.session.add(subject)
    db.session.commit()
    return jsonify({
        "id": str(subject.id),
        "name": subject.name
    }), 201

@api_bp.route('/admin/classes', methods=['POST'])
@admin_required
def create_class():
    data = request.json
    ##if not all(k in data for k in ['subject_id', 'name', 'code']):
    ##    return jsonify({"message": "Missing required fields"}), 400
    
    if not all(k in data for k in ['subject_id', 'section']):
        return jsonify({"message": "Missing required fields"}), 400
    
    if not (subject := Subject.query.get(data['subject_id'])):
        return jsonify({"message": "Subject not found"}), 404

    ##class_ = Class(
    ##    name=data['name'],
    ##    code=data['code'],
    ##    subject_id=subject.id
    ##)
    class_ = Class(
        section=data['section'],
        subject_id=subject.id
    )
    db.session.add(class_)
    db.session.commit()
    ##return jsonify({
    ##    "id": str(class_.id),
    ##    "name": class_.name,
    ##    "code": class_.code,
    ##    "subject_id": str(subject.id)
    ##}), 201
    return jsonify({
        "id": str(class_.id),
        "section": class_.section,
        "subject_id": str(subject.id)
    }), 201