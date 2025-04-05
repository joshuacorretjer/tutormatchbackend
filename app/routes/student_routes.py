from flask import request, jsonify
from flask_jwt_extended import jwt_required
from ..models import db, Student, Tutor, Class, ClassSubject, TutorSubject, TutorClass
from . import api_bp  # Import the Blueprint

# Helper function to serialize tutor data
def serialize_tutor(tutor):
    return {
        "tutor_id": str(tutor.tutor_id),
        "name": tutor.user.first_name + " " + tutor.user.last_name,
        "available_hours": tutor.available_hours,
        "hourly_rate": str(tutor.hourly_rate)
    }

# Gets all students
@api_bp.route('/students', methods=['GET'])
@jwt_required()
def get_all_students():
    students = Student.query.all()
    students_list = [{"student_id": str(student.student_id), "name": student.user.first_name + " " + student.user.last_name, "major": student.major, "year": student.year} for student in students]
    return jsonify(students_list), 200

# Gets a specific student's details
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

# Search tutors by subject
@api_bp.route('/students/search/tutors/subject/<uuid:subject_id>', methods=['GET'])
@jwt_required()
def search_tutors_by_subject(subject_id):
    tutors = (
        db.session.query(Tutor)
        .join(TutorSubject)
        .filter(TutorSubject.subject_id == subject_id)
        .all()
    )

    if not tutors:
        return jsonify({"message": "No tutors found for this subject"}), 404

    tutor_list = [
        {
            "tutor_id": str(tutor.tutor_id),
            "name": f"{tutor.user.first_name} {tutor.user.last_name}",
            "email": tutor.user.email,
            "available_hours": tutor.available_hours,
            "hourly_rate": float(tutor.hourly_rate),
        }
        for tutor in tutors
    ]

    return jsonify({"tutors": tutor_list}), 200


# Search tutors by class
@api_bp.route('/students/search/tutors/class/<uuid:class_id>', methods=['GET'])
@jwt_required()
def search_tutors_by_class(class_id):
    tutors = (
        db.session.query(Tutor)
        .join(TutorClass)
        .filter(TutorClass.class_id == class_id)
        .all()
    )

    if not tutors:
        return jsonify({"message": "No tutors found for this class"}), 404

    tutor_list = [
        {
            "tutor_id": str(tutor.tutor_id),
            "name": f"{tutor.user.first_name} {tutor.user.last_name}",
            "email": tutor.user.email,
            "available_hours": tutor.available_hours,
            "hourly_rate": float(tutor.hourly_rate),
        }
        for tutor in tutors
    ]

    return jsonify({"tutors": tutor_list}), 200