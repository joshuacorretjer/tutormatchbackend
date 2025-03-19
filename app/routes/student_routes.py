from flask import request, jsonify
from flask_jwt_extended import jwt_required
from ..models import db, Student, Tutor, Class, ClassSubject, TutorSubject, TutorClass
from sqlalchemy.exc import SQLAlchemyError
from . import api_bp  # Import the Blueprint

# Helper function to serialize tutor data
def serialize_tutor(tutor):
    return {
        "tutor_id": str(tutor.tutor_id),
        "name": tutor.user.first_name + " " + tutor.user.last_name,
        "available_hours": tutor.available_hours,
        "hourly_rate": str(tutor.hourly_rate)
    }

# Retrieves all students
@api_bp.route('/students', methods=['GET'])
@jwt_required()
def get_all_students():
    students = Student.query.all()
    students_list = [{"student_id": str(student.student_id), "name": student.user.first_name + " " + student.user.last_name, "major": student.major, "year": student.year} for student in students]
    return jsonify(students_list), 200

# Retrieves a specific student's details
@api_bp.route('/students/<uuid:student_id>', methods=['GET'])
@jwt_required()
def get_student_details(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    student_details = {
        "student_id": str(student.student_id),
        "name": student.user.first_name + " " + student.user.last_name,
        "major": student.major,
        "year": student.year,
        "classes": [{"class_id": str(enrollment.class_ref.class_id), "class_name": enrollment.class_ref.class_name} for enrollment in student.classes],
        "tutoring_sessions": [{"session_id": str(session.session_id), "date": str(session.date), "time": str(session.time), "status": session.status} for session in student.sessions]
    }
    return jsonify(student_details), 200

# Updates a specific student's details
@api_bp.route('/students/<uuid:student_id>', methods=['PUT'])
@jwt_required()
def update_student_details(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    # Gets data from the request body
    data = request.json
    if 'major' in data:
        student.major = data['major']
    if 'year' in data:
        student.year = data['year']
    
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": f"An error occurred while updating the student: {str(e)}"}), 500

    return jsonify({
        "message": "Student details updated successfully",
        "student_id": str(student.student_id),
        "major": student.major,
        "year": student.year
    }), 200

# Retrieves all tutors
@api_bp.route('/students/search/tutors', methods=['GET'])
@jwt_required()
def search_all_tutors():
    tutors_query = Tutor.query
    
    # Filter by available hours if provided
    available_hours = request.args.get('available_hours')
    if available_hours:
        tutors_query = tutors_query.filter(Tutor.available_hours >= int(available_hours))
    
    # Filter by hourly_rate if provided
    hourly_rate = request.args.get('hourly_rate')
    if hourly_rate:
        tutors_query = tutors_query.filter(Tutor.hourly_rate <= float(hourly_rate))
    
    tutors = tutors_query.all()
    
    if not tutors:
        return jsonify({"message": "No tutors found"}), 404

    tutor_list = [serialize_tutor(tutor) for tutor in tutors]
    
    return jsonify(tutor_list), 200

# Searches for tutors by subject
@api_bp.route('/students/search/tutors/subject', methods=['GET'])
@jwt_required()
def search_tutors_by_subject():
    subject_name = request.args.get('subject_name')
    if not subject_name:
        return jsonify({"message": "Subject name is required"}), 400

    subject = ClassSubject.query.filter_by(subject_name=subject_name).first()
    if not subject:
        return jsonify({"message": "Subject not found"}), 404

    tutors = Tutor.query.join(TutorSubject).filter(TutorSubject.subject_id == subject.subject_id).all()
    
    if not tutors:
        return jsonify({"message": "No tutors found for this subject"}), 404

    tutor_list = [serialize_tutor(tutor) for tutor in tutors]
    
    return jsonify(tutor_list), 200

# Searches for tutors by class
@api_bp.route('/students/search/tutors/class', methods=['GET'])
@jwt_required()
def search_tutors_by_class():
    class_name = request.args.get('class_name')
    if not class_name:
        return jsonify({"message": "Class name is required"}), 400

    class_obj = Class.query.filter_by(class_name=class_name).first()
    if not class_obj:
        return jsonify({"message": "Class not found"}), 404

    tutors = Tutor.query.join(TutorClass).filter(TutorClass.class_id == class_obj.class_id).all()

    if not tutors:
        return jsonify({"message": "No tutors found for this class"}), 404

    tutor_list = [serialize_tutor(tutor) for tutor in tutors]
    
    return jsonify(tutor_list), 200