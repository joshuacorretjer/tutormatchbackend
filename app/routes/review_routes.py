from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from ..models import db, User, Tutor, Student, Class, Subject, TimeSlot, Review
from ..utils.decorators import tutor_required, student_required, role_required
from . import api_bp

@api_bp.route('/students/sessions/<uuid:session_id>/reviews', methods=['POST'])
@student_required
def create_review(session_id):
    student_id = get_jwt_identity()
    data = request.get_json()
    
    # Verify session exists and belongs to this student
    session = TimeSlot.query.filter_by(
        id=session_id,
        student_id=student_id,
        status='completed'
    ).first()
    
    if not session:
        return jsonify({"message": "Invalid session for review"}), 400
    
    # Check if review already exists
    if Review.query.filter_by(timeslot_id=session_id).first():
        return jsonify({"message": "Review already submitted"}), 400
    
    review = Review(
        tutor_id=session.tutor_id,
        student_id=student_id,
        timeslot_id=session_id,
        rating=data['rating'],
        comment=data.get('comment', '')
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        "message": "Review submitted",
        "review_id": str(review.id)
    }), 201