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

# Associates tutor with subjects
@api_bp.route('/tutors/<uuid:tutor_id>/subjects', methods=['POST'])
@jwt_required()
def associate_tutor_with_subjects(tutor_id):
    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({"message": "Tutor not found"}), 404

    data = request.json
    subject_ids = data.get("subject_ids", [])

    if not subject_ids:
        return jsonify({"message": "No subjects provided"}), 400

    for subject_id in subject_ids:
        subject = ClassSubject.query.get(subject_id)
        if subject:
            tutor_subject = TutorSubject(tutor_id=tutor_id, subject_id=subject_id)
            db.session.add(tutor_subject)

    db.session.commit()
    return jsonify({"message": "Tutor associated with subjects successfully"}), 200


# Associates tutor with classes
@api_bp.route('/tutors/<uuid:tutor_id>/classes', methods=['POST'])
@jwt_required()
def associate_tutor_with_classes(tutor_id):
    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({"message": "Tutor not found"}), 404

    data = request.json
    class_ids = data.get("class_ids", [])

    if not class_ids:
        return jsonify({"message": "No classes provided"}), 400

    for class_id in class_ids:
        class_instance = Class.query.get(class_id)
        if class_instance:
            tutor_class = TutorClass(tutor_id=tutor_id, class_id=class_id)
            db.session.add(tutor_class)

    db.session.commit()
    return jsonify({"message": "Tutor associated with classes successfully"}), 200

# Get all tutors
@api_bp.route('/tutors', methods=['GET'])
@jwt_required()
def get_tutors():
    tutors = Tutor.query.all()
    if not tutors:
        return jsonify({"message": "No tutors found"}), 404

    tutor_list = []
    for tutor in tutors:
        # Get all subjects associated with the tutor
        subjects = (
            db.session.query(ClassSubject)
            .join(TutorSubject)
            .filter(TutorSubject.tutor_id == tutor.tutor_id)
            .all()
        )
        subject_list = [{"subject_id": str(subject.subject_id), "subject_name": subject.subject_name} for subject in subjects]

        # Get all classes associated with the tutor
        classes = (
            db.session.query(Class)
            .join(TutorClass)
            .filter(TutorClass.tutor_id == tutor.tutor_id)
            .all()
        )
        class_list = [{"class_id": str(class_instance.class_id), "class_name": class_instance.class_name, "class_code": class_instance.class_code} for class_instance in classes]

        tutor_list.append({
            "tutor_id": str(tutor.tutor_id),
            "name": f"{tutor.user.first_name} {tutor.user.last_name}",
            "email": tutor.user.email,
            "available_hours": tutor.available_hours,
            "hourly_rate": float(tutor.hourly_rate),
            "subjects": subject_list,
            "classes": class_list
        })

    return jsonify({"tutors": tutor_list}), 200

# Get a specific tutor's details
@api_bp.route('/tutors/<uuid:tutor_id>', methods=['GET'])
@jwt_required()
def get_tutor_details(tutor_id):
    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({"message": "Tutor not found"}), 404

    # Get all subjects associated with the tutor
    subjects = (
        db.session.query(ClassSubject)
        .join(TutorSubject)
        .filter(TutorSubject.tutor_id == tutor_id)
        .all()
    )
    subject_list = [{"subject_id": str(subject.subject_id), "subject_name": subject.subject_name} for subject in subjects]

    # Get all classes associated with the tutor
    classes = (
        db.session.query(Class)
        .join(TutorClass)
        .filter(TutorClass.tutor_id == tutor_id)
        .all()
    )
    class_list = [{"class_id": str(class_instance.class_id), "class_name": class_instance.class_name, "class_code": class_instance.class_code} for class_instance in classes]

    tutor_data = {
        "tutor_id": str(tutor.tutor_id),
        "name": f"{tutor.user.first_name} {tutor.user.last_name}",
        "email": tutor.user.email,
        "available_hours": tutor.available_hours,
        "hourly_rate": float(tutor.hourly_rate),
        "subjects": subject_list,
        "classes": class_list
    }

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

# Removes a tutor from a subject
@api_bp.route('/tutors/<uuid:tutor_id>/subjects/<uuid:subject_id>', methods=['DELETE'])
@jwt_required()
def remove_tutor_from_subject(tutor_id, subject_id):
    tutor_subject = TutorSubject.query.filter_by(tutor_id=tutor_id, subject_id=subject_id).first()
    if not tutor_subject:
        return jsonify({"message": "Tutor is not associated with this subject"}), 404

    db.session.delete(tutor_subject)
    db.session.commit()

    return jsonify({"message": "Tutor removed from subject successfully"}), 200

# Removes a tutor from a class
@api_bp.route('/tutors/<uuid:tutor_id>/classes/<uuid:class_id>', methods=['DELETE'])
@jwt_required()
def remove_tutor_from_class(tutor_id, class_id):
    tutor_class = TutorClass.query.filter_by(tutor_id=tutor_id, class_id=class_id).first()
    if not tutor_class:
        return jsonify({"message": "Tutor is not associated with this class"}), 404

    db.session.delete(tutor_class)
    db.session.commit()

    return jsonify({"message": "Tutor removed from class successfully"}), 200
