from uuid import UUID
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from ..models import db, ClassSubject, Class, User
from ..utils.decorators import admin_required  # Import the decorator
from . import api_bp  # Import the Blueprint

# Helper function to validate UUID
def is_valid_uuid(value):
    try:
        UUID(value)
        return True
    except ValueError:
        return False

# Gets the list of all users
@api_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    user_list = [{
        "user_id": str(user.user_id),
        "username": user.username,
        "email": user.email,
        "account_type": user.account_type,
        "date_joined": user.date_joined.isoformat()
    } for user in users]
    return jsonify(user_list), 200

# Creates a user
@api_bp.route('/admin/users', methods=['POST'])
@admin_required
def create_user():
    data = request.json
    new_user = User(
        username=data['username'],
        email=data['email'],
        account_type=data.get('account_type', 'student')
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

# Updates a user
@api_bp.route('/admin/users/<uuid:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.account_type = data.get('account_type', user.account_type)

    db.session.commit()
    return jsonify({"message": "User updated successfully"}), 200

# Deletes a user
@api_bp.route('/admin/users/<uuid:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200

# Adds a subject
@api_bp.route('/admin/subjects', methods=['POST'])
@admin_required
def add_subject():
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({"message": "Missing subject name"}), 400

    new_subject = ClassSubject(subject_name=name)
    db.session.add(new_subject)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Subject added", "subject_id": str(new_subject.subject_id), "subject_name": new_subject.subject_name}), 201

# Updates a subject
@api_bp.route('/admin/subjects/<uuid:subject_id>', methods=['PUT'])
@admin_required
def update_subject(subject_id):
    if not is_valid_uuid(subject_id):
        return jsonify({"message": "Invalid subject ID format"}), 400

    data = request.json
    subject = ClassSubject.query.get(subject_id)
    if not subject:
        return jsonify({"message": "Subject not found"}), 404

    name = data.get('name')
    if name:
        subject.subject_name = name

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Subject updated", "subject_id": str(subject.subject_id), "subject_name": subject.subject_name})

# Deletes a subject
@api_bp.route('/admin/subjects/<uuid:subject_id>', methods=['DELETE'])
@admin_required
def delete_subject(subject_id):
    if not is_valid_uuid(subject_id):
        return jsonify({"message": "Invalid subject ID format"}), 400

    subject = ClassSubject.query.get(subject_id)
    if not subject:
        return jsonify({"message": "Subject not found"}), 404

    db.session.delete(subject)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Subject deleted"}), 200

# Adds a class under a subject
@api_bp.route('/admin/classes', methods=['POST'])
@admin_required
def add_class():
    data = request.json
    subject_id = data.get('subject_id')
    class_name = data.get('name')
    class_code = data.get('class_code')
    
    if not subject_id or not is_valid_uuid(subject_id):
        return jsonify({"message": "Invalid or missing subject ID"}), 400
    if not class_name:
        return jsonify({"message": "Missing class name"}), 400
    if not class_code:
        return jsonify({"message": "Missing class code"}), 400

    subject = ClassSubject.query.get(subject_id)
    if not subject:
        return jsonify({"message": "Subject not found"}), 404

    new_class = Class(class_name=class_name, subject_id=subject_id, class_code=class_code)
    db.session.add(new_class)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Class added", "class_id": str(new_class.class_id), "class_name": new_class.class_name}), 201

# Updates a class
@api_bp.route('/admin/classes/<uuid:class_id>', methods=['PUT'])
@admin_required
def update_class(class_id):
    if not is_valid_uuid(class_id):
        return jsonify({"message": "Invalid class ID format"}), 400

    data = request.json
    class_ref = Class.query.get(class_id)
    if not class_ref:
        return jsonify({"message": "Class not found"}), 404

    class_name = data.get('name')
    class_code = data.get('class_code')

    if class_name:
        class_ref.class_name = class_name
    if class_code:
        class_ref.class_code = class_code

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Class updated", "class_id": str(class_ref.class_id), "class_name": class_ref.class_name})

# Deletes a class
@api_bp.route('/admin/classes/<uuid:class_id>', methods=['DELETE'])
@admin_required
def delete_class(class_id):
    if not is_valid_uuid(class_id):
        return jsonify({"message": "Invalid class ID format"}), 400

    class_ref = Class.query.get(class_id)
    if not class_ref:
        return jsonify({"message": "Class not found"}), 404

    db.session.delete(class_ref)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Class deleted"}), 200

