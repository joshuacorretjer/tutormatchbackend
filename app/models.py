from datetime import datetime
import uuid
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID  # For PostgreSQL
from sqlalchemy import Numeric

### User Model ###

class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Store hashed passwords
    date_joined = db.Column(db.Date, default=db.func.current_date())

### Class Subject Model ###

class ClassSubject(db.Model):
    __tablename__ = "class_subject"

    subject_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_name = db.Column(db.String(100), nullable=False)

### Class Model ###

class Class(db.Model):
    __tablename__ = "class"

    class_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = db.Column(UUID(as_uuid=True), db.ForeignKey('class_subject.subject_id'), nullable=False)
    class_name = db.Column(db.String(100), nullable=False)
    class_code = db.Column(db.String(50), nullable=False)

    subject = db.relationship('ClassSubject', backref='classes')

### Student Model ###

class Student(db.Model):
    __tablename__ = "student"

    student_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.user_id'), nullable=False)
    major = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref='students')

### Tutor Model ###

class Tutor(db.Model):
    __tablename__ = "tutor"

    tutor_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.user_id'), nullable=False)
    available_hours = db.Column(db.Text, nullable=True)
    hourly_rate = db.Column(Numeric(10, 2), nullable=False)

    user = db.relationship('User', backref='tutors')

### Tutor Subject Model ###

class TutorSubject(db.Model):
    __tablename__ = "tutor_subject"

    tutor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tutor.tutor_id'), primary_key=True)
    subject_id = db.Column(UUID(as_uuid=True), db.ForeignKey('class_subject.subject_id'), primary_key=True)

    tutor = db.relationship('Tutor', backref='subjects')
    subject = db.relationship('ClassSubject', backref='tutors')

### Tutoring Session Model ###

class TutoringSession(db.Model):
    __tablename__ = "tutoring_session"

    session_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tutor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tutor.tutor_id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('student.student_id'), nullable=False)
    class_id = db.Column(UUID(as_uuid=True), db.ForeignKey('class.class_id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # Use a string to represent the status
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    duration = db.Column(Numeric(10, 2), nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)

    tutor = db.relationship('Tutor', backref='sessions')
    student = db.relationship('Student', backref='sessions')
    class_ref = db.relationship('Class', backref='sessions')

### Review Model ###

class Review(db.Model):
    __tablename__ = "review"

    review_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tutoring_session.session_id'), nullable=False)
    review_title = db.Column(db.String(200), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.String(1000), nullable=True)
    date = db.Column(db.Date, nullable=False)

    session = db.relationship('TutoringSession', backref='reviews')

### Direct Message Model ###

class DirectMessage(db.Model):
    __tablename__ = "direct_message"

    message_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.user_id'), nullable=False)
    receiver_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.user_id'), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=db.func.now(), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # Use a string to represent the message status

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
