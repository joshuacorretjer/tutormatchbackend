from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from ..models import db, User, Tutor, Student, Class, Subject, TimeSlot, Review
from ..utils.decorators import tutor_required, admin_required
from . import api_bp


# --- Tutor Routes ---
@api_bp.route('/tutor/availability', methods=['POST']) # Time wasted debuggin esta vaina -> 14.5 hours
@tutor_required
def create_availability():
    # Get the logged-in user's ID
    user_id = get_jwt_identity()
    
    # Find the tutor profile linked to this user
    tutor = Tutor.query.filter_by(user_id=user_id).first()
    
    if not tutor:
        return jsonify({"error": "Tutor profile not found"}), 404

    data = request.get_json()
    
    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"Invalid time format: {str(e)}"}), 400

    if start_time >= end_time:
        return jsonify({"error": "End time must be after start time"}), 400

    # Use the tutor's ID (not user ID) when creating availability
    slot = TimeSlot(
        tutor_id=tutor.id,  # Use tutor.id instead of user_id
        start_time=start_time,
        end_time=end_time,
        status='available'
    )
    
    db.session.add(slot)
    db.session.commit()
    
    return jsonify({
        "id": str(slot.id),
        "tutor_id": str(tutor.id),
        "start_time": slot.start_time.isoformat(),
        "end_time": slot.end_time.isoformat(),
        "status": slot.status
    }), 201

@api_bp.route('/tutor/availability', methods=['GET'])
@tutor_required
def get_tutor_availability():
    user_id = get_jwt_identity()

    tutor = Tutor.query.filter_by(user_id=user_id).first()
    if not tutor:
        return jsonify({"error": "Tutor profile not found"}), 404

    slots = TimeSlot.query.filter_by(tutor_id=tutor.id).order_by(TimeSlot.start_time).all()

    return jsonify([{
        "id": str(s.id),
        "start_time": s.start_time.isoformat(),
        "end_time": s.end_time.isoformat(),
        "status": s.status,
        "student": {
            "name": f"{s.student.user.first_name} {s.student.user.last_name}",
            "major": s.student.major
        } if s.student else None
    } for s in slots]), 200

@api_bp.route('/tutor/availability/<slot_id>', methods=['DELETE'])
@tutor_required
def delete_availability(slot_id):
    user_id = get_jwt_identity()

    # Get the tutor profile
    tutor = Tutor.query.filter_by(user_id=user_id).first()
    if not tutor:
        return jsonify({"error": "Tutor profile not found"}), 404

    # Ensure the slot belongs to the logged-in tutor
    slot = TimeSlot.query.filter_by(id=slot_id, tutor_id=tutor.id).first()
    if not slot:
        return jsonify({"error": "Slot not found or not authorized to delete"}), 404

    db.session.delete(slot)
    db.session.commit()

    return jsonify({"message": "Slot deleted"}), 200

@api_bp.route('/tutor/sessions', methods=['GET'])
@tutor_required
def get_tutor_sessions():
    user_id = get_jwt_identity()

    tutor = Tutor.query.filter_by(user_id=user_id).first()
    if not tutor:
        return jsonify({"error": "Tutor profile not found"}), 404

    query = TimeSlot.query.filter_by(tutor_id=tutor.id)

    status_filter = request.args.get('status', 'upcoming')

    if status_filter == 'upcoming':
        query = query.filter(TimeSlot.start_time > datetime.utcnow())
    elif status_filter == 'completed':
        query = query.filter(TimeSlot.end_time < datetime.utcnow())

    sessions = query.order_by(TimeSlot.start_time).all()

    return jsonify([{
        "id": str(s.id),
        "start_time": s.start_time.isoformat(),
        "end_time": s.end_time.isoformat(),
        "status": s.status,
        "student": {
            "name": f"{s.student.user.first_name} {s.student.user.last_name}",
            "major": s.student.major
        } if s.student else None,
        # Class info removed since TimeSlot has no class_ref
    } for s in sessions]), 200


@api_bp.route('/<uuid:tutor_id>', methods=['GET'])
def get_tutor_profile(tutor_id):
    tutor = Tutor.query.get_or_404(tutor_id)
    
    include_reviews = request.args.get('reviews', 'false').lower() == 'true'
    
    return jsonify(tutor.to_dict(include_reviews=include_reviews)), 200

@api_bp.route('/tutor/<uuid:tutor_id>/classes', methods=['POST'])
@tutor_required
def associate_tutor_with_classes(tutor_id):
    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({"message": "Tutor not found"}), 404

    data = request.get_json()
    class_ids = data.get("class_ids", [])

    if not class_ids:
        return jsonify({"message": "No class IDs provided"}), 400

    try:
        for class_id in class_ids:
            class_instance = Class.query.get(class_id)
            if class_instance and class_instance not in tutor.classes:
                tutor.classes.append(class_instance)

        db.session.commit()
        return jsonify({"message": "Tutor successfully associated with classes"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
