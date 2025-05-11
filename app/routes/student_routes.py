from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from ..models import TutoringSession, db, User, Tutor, Student, Class, Subject, TimeSlot, Review
from ..utils.decorators import student_required
from . import api_bp
from sqlalchemy import func
from sqlalchemy.orm import aliased

@api_bp.route('/student/tutors', methods=['GET'])
@student_required
def find_tutors():
    availability = request.args.get('availability')
    min_rating = request.args.get('min_rating', type=float)
    search_query = request.args.get('query')  # Search term: class name or tutor name
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Start base query from Tutor, join User relationship
    query = db.session.query(Tutor).join(Tutor.user)

    # Create an alias for the Class table to avoid the duplicate alias issue
    class_alias = aliased(Class)

    # Filter by search term (first name, last name, username, or class section)
    if search_query:
        query = query.outerjoin(Tutor.classes).filter(
            (User.username.ilike(f'%{search_query}%')) |
            (User.first_name.ilike(f'%{search_query}%')) |
            (User.last_name.ilike(f'%{search_query}%')) |
            (Class.section.ilike(f'%{search_query}%'))
        )

    # Filter by availability
    if availability:
        now = datetime.utcnow()
        if availability == 'morning':
            start_hour, end_hour = 6, 12
        elif availability == 'afternoon':
            start_hour, end_hour = 12, 18
        elif availability == 'evening':
            start_hour, end_hour = 18, 24
        else:
            start_hour, end_hour = 0, 24

        query = query.join(Tutor.availability).filter(
            TimeSlot.status == 'available',
            TimeSlot.start_time > now,
            func.extract('hour', TimeSlot.start_time).between(start_hour, end_hour)
        )

    # Filter by minimum rating using subquery
    if min_rating is not None:
        rating_subquery = db.session.query(
            Review.tutor_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.tutor_id).subquery()

        query = query.join(rating_subquery, Tutor.id == rating_subquery.c.tutor_id).filter(
            rating_subquery.c.avg_rating >= min_rating
        )

    # Paginate results
    query = query.distinct()
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    tutors = pagination.items

    # Prepare response
    response = []
    for t in tutors:
        avg_rating = db.session.query(func.avg(Review.rating)).filter(
            Review.tutor_id == t.id
        ).scalar() or 0

        upcoming_slots = TimeSlot.query.filter(
            TimeSlot.tutor_id == t.id,
            TimeSlot.status == 'available',
            TimeSlot.start_time > datetime.utcnow()
        ).order_by(TimeSlot.start_time).limit(3).all()

        response.append({
            "id": str(t.user.id),
            "name": f"{t.user.first_name} {t.user.last_name}",
            "hourly_rate": float(t.hourly_rate),
            "bio": t.bio,
            "average_rating": round(float(avg_rating), 2),
            "upcoming_slots": [
                {
                    "id": str(slot.id),
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat() if slot.end_time else None  # Include end_time in the response
                }
                for slot in upcoming_slots
            ]
        })

    return jsonify({
        "tutors": response,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page
    }), 200


@api_bp.route('/student/sessions', methods=['POST'])
@student_required
def book_session():
    print("Reached book_session route")
    user_id = get_jwt_identity()

    # Fetch student profile by user_id
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    data = request.get_json()
    slot_id = data.get('slot_id')

    if not slot_id:
        return jsonify({"error": "Timeslot ID is required"}), 400

    slot = TimeSlot.query.filter_by(id=slot_id, status='available').first()
    if not slot:
        return jsonify({"message": "Timeslot not available"}), 400

    if slot.start_time < datetime.utcnow():
        return jsonify({"error": "Cannot book past timeslots"}), 400

    # Optionally: Check if student is enrolled in class
    # (add logic if needed)

    try:
        # Create TutoringSession record
        tutoring_session = TutoringSession(
            timeslot_id=slot.id,
            student_id=student.user_id, 
            tutor_id=slot.tutor.user_id  # Assuming the tutor is linked to the timeslot
        )

        # Add to the session and commit
        db.session.add(tutoring_session)

        # Update the TimeSlot to 'booked' and link it with the student
        slot.status = 'booked'
        slot.student_id = student.id
        ##slot.class_id = data.get('class_id')  # Optional

        db.session.commit()

        return jsonify({
            "message": "Session booked",
            "session_id": str(tutoring_session.id),
            "start_time": slot.start_time.isoformat()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api_bp.route('/student/sessions', methods=['GET'])
@student_required
def get_booked_sessions_student():
    user_id = get_jwt_identity()

    try:
        # Get the student's TutoringSession entries
        sessions = db.session.query(
            TutoringSession,
            TimeSlot,
            User  # Tutor's User info
        ).join(
            TimeSlot, TutoringSession.timeslot_id == TimeSlot.id
        ).join(
            User, TutoringSession.tutor_id == User.id
        ).filter(
            TutoringSession.student_id == user_id
        ).order_by(TimeSlot.start_time.desc()).all()

        # Build response list
        result = []
        for session, slot, tutor_user in sessions:
            result.append({
                "session_id": str(session.id),
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "status": slot.status,
                "tutor": {
                    "id": str(tutor_user.id),
                    "first_name": tutor_user.first_name,
                    "last_name": tutor_user.last_name,
                }
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    