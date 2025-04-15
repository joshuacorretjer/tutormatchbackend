from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from ..models import TutoringSession, db, User, Tutor, Student, Class, Subject, TimeSlot, Review
from ..utils.decorators import student_required
from . import api_bp

@api_bp.route('/students/tutors', methods=['GET'])
@student_required
def find_tutors():
    # Get query parameters
    subject_name = request.args.get('subject')
    class_id = request.args.get('class')
    
    # Base query
    query = Tutor.query.join(User)
    
    # Apply filters
    if subject_name:
        query = query.join(Tutor.classes).join(Class).join(Subject)\
                   .filter(Subject.name.ilike(f"%{subject_name}%"))
    
    if class_id:
        query = query.join(Tutor.classes).filter(Class.id == class_id)
    
    tutors = query.distinct().all()
    
    return jsonify([{
        "id": str(t.user.id),
        "name": f"{t.user.first_name} {t.user.last_name}",
        "hourly_rate": float(t.hourly_rate),
        "bio": t.bio,
        "average_rating": db.session.query(
            db.func.avg(Review.rating)
        ).filter(Review.tutor_id == t.id).scalar() or 0,
        "upcoming_slots": [
            s.start_time.isoformat() for s in 
            TimeSlot.query.filter(
                TimeSlot.tutor_id == t.id,
                TimeSlot.status == 'available',
                TimeSlot.start_time > datetime.utcnow()
            ).limit(3).all()
        ]
    } for t in tutors]), 200

@api_bp.route('/students/sessions', methods=['POST'])
@student_required
def book_session():
    student_id = get_jwt_identity()
    data = request.get_json()
    
    slot = TimeSlot.query.filter_by(
        id=data['slot_id'],
        status='available'
    ).first()
    
    if not slot:
        return jsonify({"message": "Timeslot not available"}), 400
    
    # Verify student is enrolled in the class?
    # Add your custom logic here
    
    slot.status = 'booked'
    slot.student_id = student_id
    slot.class_id = data['class_id']
    
    db.session.commit()
    
    return jsonify({
        "message": "Session booked",
        "session_id": str(slot.id),
        "start_time": slot.start_time.isoformat()
    }), 201

@api_bp.route('/students/sessions/book', methods=['POST'], endpoint='book_tutoring_session')  # Unique name
@student_required
def book_session():
    # Get current student ID from auth token
    student_id = get_jwt_identity()

    data = request.get_json()
    timeslot_id = data.get('timeslot_id')  

    if not timeslot_id:
        return jsonify({"error": "Timeslot ID is required"}), 400

    # Rest of your code remains the same...
    timeslot = TimeSlot.query.get(timeslot_id)
    if not timeslot:
        return jsonify({"error": "Timeslot not found"}), 404

    if timeslot.status != 'available':
        return jsonify({"error": "Timeslot is not available"}), 400

    if timeslot.start_time < datetime.utcnow():
        return jsonify({"error": "Cannot book past timeslots"}), 400

    try:
        timeslot.status = 'booked'
        timeslot.student_id = student_id

        session = TutoringSession(
            timeslot_id=timeslot.id,
            student_id=student_id,
            tutor_id=timeslot.tutor_id
        )
        db.session.add(session)
        db.session.commit()

        return jsonify({
            "message": "Session booked successfully",
            "session_id": str(session.id),
            "timeslot_id": str(timeslot.id),
            "tutor_id": str(timeslot.tutor_id),
            "start_time": timeslot.start_time.isoformat(),
            "end_time": timeslot.end_time.isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500