from uuid import UUID
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from ..models import db, Tutor, TutorSubject, ClassSubject, Class, TutorClass  # Import relevant models
from . import api_bp  # Import the Blueprint

# Helper function to validate UUID
def is_valid_uuid(value):
    try:
        UUID(value)
        return True
    except ValueError:
        return False

# Get all tutors
@api_bp.route('/tutors', methods=['GET'])
@jwt_required()
def get_all_tutors():
    tutors = Tutor.query.all()
    tutors_list = [{"tutor_id": str(tutor.tutor_id), "name": tutor.user.first_name + " " + tutor.user.last_name, "hourly_rate": str(tutor.hourly_rate)} for tutor in tutors]
    return jsonify(tutors_list), 200

# Get a specific tutor's details
@api_bp.route('/tutors/<uuid:tutor_id>', methods=['GET'])
@jwt_required()
def get_tutor_details(tutor_id):
    if not is_valid_uuid(tutor_id):
        return jsonify({"message": "Invalid tutor ID format"}), 400

    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({"message": "Tutor not found"}), 404

    tutor_details = {
        "tutor_id": str(tutor.tutor_id),
        "name": tutor.user.first_name + " " + tutor.user.last_name,
        "available_hours": tutor.available_hours,
        "hourly_rate": str(tutor.hourly_rate),
        "subjects": [{"subject_id": str(subject.subject_id), "subject_name": subject.subject_name} for subject in tutor.subjects]
    }
    return jsonify(tutor_details), 200

# Assign a tutor to a subject
@api_bp.route('/tutors/<uuid:tutor_id>/subjects', methods=['POST'])
@jwt_required()
def assign_tutor_to_subject(tutor_id):
    if not is_valid_uuid(tutor_id):
        return jsonify({"message": "Invalid tutor ID format"}), 400
    
    data = request.json
    subject_id = data.get('subject_id')
    
    if not subject_id or not is_valid_uuid(subject_id):
        return jsonify({"message": "Invalid or missing subject ID"}), 400

    tutor = Tutor.query.get(tutor_id)
    subject = ClassSubject.query.get(subject_id)

    if not tutor:
        return jsonify({"message": "Tutor not found"}), 404
    if not subject:
        return jsonify({"message": "Subject not found"}), 404

    # Check if the tutor is already associated with the subject
    existing_assignment = TutorSubject.query.filter_by(tutor_id=tutor_id, subject_id=subject_id).first()
    if existing_assignment:
        return jsonify({"message": "Tutor is already assigned to this subject"}), 400

    # Create the subject assignment
    tutor_subject = TutorSubject(tutor_id=tutor_id, subject_id=subject_id)
    db.session.add(tutor_subject)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Tutor assigned to subject", "tutor_id": str(tutor.tutor_id), "subject_id": str(subject.subject_id)}), 201

# Remove a tutor from a subject
@api_bp.route('/tutors/<uuid:tutor_id>/subjects/<uuid:subject_id>', methods=['DELETE'])
@jwt_required()
def remove_tutor_from_subject(tutor_id, subject_id):
    if not is_valid_uuid(tutor_id) or not is_valid_uuid(subject_id):
        return jsonify({"message": "Invalid ID format"}), 400

    tutor_subject = TutorSubject.query.filter_by(tutor_id=tutor_id, subject_id=subject_id).first()
    if not tutor_subject:
        return jsonify({"message": "Assignment not found"}), 404

    db.session.delete(tutor_subject)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Tutor removed from subject"}), 200

# Get all classes for a specific tutor
@api_bp.route('/tutors/<uuid:tutor_id>/classes', methods=['GET'])
@jwt_required()
def get_tutor_classes(tutor_id):
    if not is_valid_uuid(tutor_id):
        return jsonify({"message": "Invalid tutor ID format"}), 400

    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({"message": "Tutor not found"}), 404

    tutor_classes = TutorClass.query.filter_by(tutor_id=tutor_id).all()
    classes = [{"class_id": str(tutor_class.class_id), "class_name": tutor_class.class_ref.class_name} for tutor_class in tutor_classes]

    return jsonify(classes), 200

# Assign a tutor to a class
@api_bp.route('/tutors/<uuid:tutor_id>/classes', methods=['POST'])
@jwt_required()
def assign_tutor_to_class(tutor_id):
    if not is_valid_uuid(tutor_id):
        return jsonify({"message": "Invalid tutor ID format"}), 400
    
    data = request.json
    class_id = data.get('class_id')
    
    if not class_id or not is_valid_uuid(class_id):
        return jsonify({"message": "Invalid or missing class ID"}), 400

    tutor = Tutor.query.get(tutor_id)
    class_obj = Class.query.get(class_id)

    if not tutor:
        return jsonify({"message": "Tutor not found"}), 404
    if not class_obj:
        return jsonify({"message": "Class not found"}), 404

    # Check if the tutor is already assigned to the class
    existing_assignment = TutorClass.query.filter_by(tutor_id=tutor_id, class_id=class_id).first()
    if existing_assignment:
        return jsonify({"message": "Tutor is already assigned to this class"}), 400

    # Create the class assignment
    tutor_class = TutorClass(tutor_id=tutor_id, class_id=class_id)
    db.session.add(tutor_class)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Tutor assigned to class", "tutor_id": str(tutor.tutor_id), "class_id": str(class_obj.class_id)}), 201

# Remove a tutor from a class
@api_bp.route('/tutors/<uuid:tutor_id>/classes/<uuid:class_id>', methods=['DELETE'])
@jwt_required()
def remove_tutor_from_class(tutor_id, class_id):
    if not is_valid_uuid(tutor_id) or not is_valid_uuid(class_id):
        return jsonify({"message": "Invalid ID format"}), 400

    tutor_class = TutorClass.query.filter_by(tutor_id=tutor_id, class_id=class_id).first()
    if not tutor_class:
        return jsonify({"message": "Assignment not found"}), 404

    db.session.delete(tutor_class)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Tutor removed from class"}), 200

# Update tutor details (e.g., availability, hourly rate)
@api_bp.route('/tutors/<uuid:tutor_id>', methods=['PUT'])
@jwt_required()
def update_tutor_details(tutor_id):
    if not is_valid_uuid(tutor_id):
        return jsonify({"message": "Invalid tutor ID format"}), 400

    data = request.json
    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({"message": "Tutor not found"}), 404

    # Update tutor information
    tutor.available_hours = data.get('available_hours', tutor.available_hours)
    tutor.hourly_rate = data.get('hourly_rate', tutor.hourly_rate)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

    return jsonify({"message": "Tutor updated", "tutor_id": str(tutor.tutor_id)}), 200
