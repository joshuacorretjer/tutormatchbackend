from uuid import UUID
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from ..models import db, ClassSubject, Class, User, Student, Tutor, TutorSubject, TutorClass
from ..utils.decorators import admin_required  # Import the decorator
from . import api_bp  # Import the Blueprint

# Helper function to validate UUID
def is_valid_uuid(value):
    try:
        UUID(value)
        return True
    except ValueError:
        return False

# Creates a user
@api_bp.route('/admin/users', methods=['POST'])
@admin_required
def create_user():
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

    # Add user to the appropriate table based on account type
    if user.account_type == "student":
        student_data = data.get("student_data", {})  # Get optional student details
        major = student_data.get("major", "Undeclared")
        year = student_data.get("year", 1)
        student = Student(user_id=user.user_id, major=major, year=year)
        db.session.add(student)
    elif user.account_type == "tutor":
        tutor_data = data.get("tutor_data", {})  # Get optional tutor details
        available_hours = tutor_data.get("available_hours", "")
        hourly_rate = tutor_data.get("hourly_rate", 0.00)
        tutor = Tutor(user_id=user.user_id, available_hours=available_hours, hourly_rate=hourly_rate)
        db.session.add(tutor)

    db.session.commit()

    return jsonify({"message": "User registered successfully", "user_id": str(user.user_id)}), 201

# Gets the list of all users
@api_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    user_list = []

    for user in users:
        user_data = {
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "account_type": user.account_type,
            "date_joined": user.date_joined.isoformat()
        }

        if user.account_type == "student":
            student = Student.query.filter_by(user_id=user.user_id).first()
            if student:
                user_data["student_data"] = {
                    "major": student.major,
                    "year": student.year
                }

        elif user.account_type == "tutor":
            tutor = Tutor.query.filter_by(user_id=user.user_id).first()
            if tutor:
                # Get subjects associated with the tutor
                subjects = (
                    db.session.query(ClassSubject)
                    .join(TutorSubject)
                    .filter(TutorSubject.tutor_id == tutor.tutor_id)
                    .all()
                )
                subject_list = [{"subject_id": str(subject.subject_id), "subject_name": subject.subject_name} for subject in subjects]

                # Get classes associated with the tutor
                classes = (
                    db.session.query(Class)
                    .join(TutorClass)
                    .filter(TutorClass.tutor_id == tutor.tutor_id)
                    .all()
                )
                class_list = [{"class_id": str(class_instance.class_id), "class_name": class_instance.class_name, "class_code": class_instance.class_code} for class_instance in classes]

                user_data["tutor_data"] = {
                    "available_hours": tutor.available_hours,
                    "hourly_rate": float(tutor.hourly_rate),
                    "subjects": subject_list,
                    "classes": class_list
                }

        user_list.append(user_data)

    return jsonify(user_list), 200

# Gets a specific user
@api_bp.route('/admin/users/<uuid:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    user_data = {
        "user_id": str(user.user_id),
        "username": user.username,
        "email": user.email,
        "account_type": user.account_type,
        "date_joined": user.date_joined.isoformat()
    }

    if user.account_type == "student":
        student = user.students[0] if user.students else None
        if student:
            user_data["student_data"] = {
                "major": student.major,
                "year": student.year
            }

    elif user.account_type == "tutor":
        tutor = user.tutors[0] if user.tutors else None
        if tutor:
            # Get subjects associated with the tutor
            subjects = (
                db.session.query(ClassSubject)
                .join(TutorSubject)
                .filter(TutorSubject.tutor_id == tutor.tutor_id)
                .all()
            )
            subject_list = [{"subject_id": str(subject.subject_id), "subject_name": subject.subject_name} for subject in subjects]

            # Get classes associated with the tutor
            classes = (
                db.session.query(Class)
                .join(TutorClass)
                .filter(TutorClass.tutor_id == tutor.tutor_id)
                .all()
            )
            class_list = [{"class_id": str(class_instance.class_id), "class_name": class_instance.class_name, "class_code": class_instance.class_code} for class_instance in classes]

            user_data["tutor_data"] = {
                "available_hours": tutor.available_hours,
                "hourly_rate": float(tutor.hourly_rate),
                "subjects": subject_list,
                "classes": class_list
            }

    return jsonify(user_data), 200

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

    # Update Student data
    if user.account_type == "student":
        student = user.students[0] if user.students else None
        if student:
            student.major = data.get("student_data", {}).get("major", student.major)
            student.year = data.get("student_data", {}).get("year", student.year)

    # Update Tutor data
    elif user.account_type == "tutor":
        tutor = user.tutors[0] if user.tutors else None
        if tutor:
            tutor.available_hours = data.get("tutor_data", {}).get("available_hours", tutor.available_hours)
            tutor.hourly_rate = data.get("tutor_data", {}).get("hourly_rate", tutor.hourly_rate)

    db.session.commit()
    return jsonify({"message": "User updated successfully"}), 200

# Deletes a user
@api_bp.route('/admin/users/<uuid:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Delete from Student or Tutor table if applicable
    if user.account_type == "student":
        student = Student.query.filter_by(user_id=user.user_id).first()
        if student:
            db.session.delete(student)

    elif user.account_type == "tutor":
        tutor = Tutor.query.filter_by(user_id=user.user_id).first()
        if tutor:
            db.session.delete(tutor)

    # Finally, delete the user
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"}), 200

# Assigns role to users
@api_bp.route('/admin/users/<uuid:user_id>/role', methods=['PUT'])
@admin_required
def assign_role(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.json
    new_role = data.get('account_type')
    if new_role not in ['student', 'tutor', 'admin']:
        return jsonify({"message": "Invalid role"}), 400

    # If the role is changing, update related tables
    if user.account_type != new_role:
        if new_role == "student":
            # Remove existing tutor record if applicable
            Tutor.query.filter_by(user_id=user.user_id).delete()
            # Create a student record if it doesn't exist
            if not Student.query.filter_by(user_id=user.user_id).first():
                student = Student(user_id=user.user_id, major="", year=1)
                db.session.add(student)

        elif new_role == "tutor":
            # Remove existing student record if applicable
            Student.query.filter_by(user_id=user.user_id).delete()
            # Create a tutor record if it doesn't exist
            if not Tutor.query.filter_by(user_id=user.user_id).first():
                tutor = Tutor(user_id=user.user_id, available_hours="", hourly_rate=0)
                db.session.add(tutor)

        elif new_role == "admin":
            # Remove student/tutor records if user is becoming an admin
            Student.query.filter_by(user_id=user.user_id).delete()
            Tutor.query.filter_by(user_id=user.user_id).delete()

    user.account_type = new_role
    db.session.commit()
    
    return jsonify({"message": "User role updated successfully"}), 200

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

# Gets all the subjects available
@api_bp.route('/admin/subjects', methods=['GET'])
@admin_required
def get_all_subjects():
    subjects = ClassSubject.query.all()
    subject_list = [
        {
            "subject_id": str(subject.subject_id),
            "subject_name": subject.subject_name
        } for subject in subjects
    ]
    return jsonify(subject_list), 200

# Gets a specific subject
@api_bp.route('/admin/subjects/<uuid:subject_id>', methods=['GET'])
@admin_required
def get_subject(subject_id):
    if not is_valid_uuid(subject_id):
        return jsonify({"message": "Invalid subject ID format"}), 400

    subject = ClassSubject.query.get(subject_id)
    if not subject:
        return jsonify({"message": "Subject not found"}), 404

    return jsonify({
        "subject_id": str(subject.subject_id),
        "subject_name": subject.subject_name
    }), 200

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

# Gets all the classes available
@api_bp.route('/admin/classes', methods=['GET'])
@admin_required
def get_all_classes():
    classes = Class.query.all()
    class_list = [
        {
            "class_id": str(class_ref.class_id),
            "class_name": class_ref.class_name,
            "class_code": class_ref.class_code,
            "subject_id": str(class_ref.subject_id)
        } for class_ref in classes
    ]
    return jsonify(class_list), 200

# Gets a specific class
@api_bp.route('/admin/classes/<uuid:class_id>', methods=['GET'])
@admin_required
def get_class(class_id):
    if not is_valid_uuid(class_id):
        return jsonify({"message": "Invalid class ID format"}), 400

    class_ref = Class.query.get(class_id)
    if not class_ref:
        return jsonify({"message": "Class not found"}), 404

    return jsonify({
        "class_id": str(class_ref.class_id),
        "class_name": class_ref.class_name,
        "class_code": class_ref.class_code,
        "subject_id": str(class_ref.subject_id)
    }), 200

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

