import uuid
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Numeric, UniqueConstraint, func

### User Model ###
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Changed from user_id to id
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    date_joined = db.Column(db.Date, default=db.func.current_date())

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    # Relationships
    student_profile = db.relationship('Student', back_populates='user', uselist=False, cascade='all, delete')
    tutor_profile = db.relationship('Tutor', back_populates='user', uselist=False, cascade='all, delete')

### Subject Model ###
class Subject(db.Model):
    __tablename__ = "subjects"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True)
    
    __table_args__ = (
        UniqueConstraint('name', name='uq_subject_name'),
        UniqueConstraint('code', name='uq_subject_code'),
    )

### Class Model ###
class Class(db.Model):
    __tablename__ = "classes"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = db.Column(UUID(as_uuid=True), db.ForeignKey('subjects.id'), nullable=False)
    section = db.Column(db.String(10))
    
    subject = db.relationship('Subject', backref='classes')
    tutors = db.relationship('Tutor', secondary='tutor_class_association', back_populates='classes')

### Tutor Model ###
class Tutor(db.Model):
    __tablename__ = "tutors"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), unique=True, nullable=False)
    hourly_rate = db.Column(Numeric(10, 2), nullable=False)
    bio = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', back_populates='tutor_profile')
    classes = db.relationship('Class', secondary='tutor_class_association', back_populates='tutors')
    availability = db.relationship('TimeSlot', back_populates='tutor', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='tutor')

    def calculate_average_rating(self):
        avg_rating = db.session.query(
            func.avg(Review.rating)
        ).filter(Review.tutor_id == self.id).scalar()
        return round(float(avg_rating or 0), 2)

    def get_rating_distribution(self):
        distribution = db.session.query(
            Review.rating,
            func.count(Review.id)
        ).filter(Review.tutor_id == self.id)\
         .group_by(Review.rating)\
         .order_by(Review.rating)\
         .all()
        return {str(rating): count for rating, count in distribution}

    def to_dict(self, include_reviews=False):
        data = {
            "id": str(self.id),
            "hourly_rate": float(self.hourly_rate),
            "bio": self.bio,
            "average_rating": self.calculate_average_rating(),
            "total_reviews": len(self.reviews)
        }
        if include_reviews:
            data["reviews"] = [r.to_dict() for r in self.reviews]
            data["rating_distribution"] = self.get_rating_distribution()
        return data

# Junction table for Tutor <-> Class
tutor_class_association = db.Table(
    'tutor_class_association',
    db.Column('tutor_id', UUID(as_uuid=True), db.ForeignKey('tutors.id'), primary_key=True),
    db.Column('class_id', UUID(as_uuid=True), db.ForeignKey('classes.id'), primary_key=True)
)

### TimeSlot Model ###
class TimeSlot(db.Model):
    __tablename__ = "time_slots"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tutor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tutors.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='available')
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'))
    
    tutor = db.relationship('Tutor', back_populates='availability')
    student = db.relationship('Student', backref='booked_sessions')

### Student Model ###
class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), unique=True, nullable=False)
    major = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    
    # Relationships
    user = db.relationship('User', back_populates='student_profile')
    reviews = db.relationship('Review', back_populates='student')

### Review Model ###
class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tutor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tutors.id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    timeslot_id = db.Column(UUID(as_uuid=True), db.ForeignKey('time_slots.id'), unique=True, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating'),
    )

    tutor = db.relationship('Tutor', back_populates='reviews')
    student = db.relationship('Student', back_populates='reviews')
    timeslot = db.relationship('TimeSlot', backref='review')

    def to_dict(self):
        return {
            "id": str(self.id),
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
            "student": {
                "name": f"{self.student.user.first_name} {self.student.user.last_name}"
            }
        }
    
class TutoringSession(db.Model):
    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    timeslot_id = db.Column(db.UUID, db.ForeignKey('time_slots.id'), nullable=False)
    student_id = db.Column(db.UUID, db.ForeignKey('user.id'), nullable=False)
    tutor_id = db.Column(db.UUID, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)