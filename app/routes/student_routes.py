from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from ..models import db, User, Tutor, Student, Class, Subject, TimeSlot, Review
from ..utils.decorators import tutor_required, student_required, role_required
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