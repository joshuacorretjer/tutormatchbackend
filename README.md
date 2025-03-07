# TutorMatch Backend

Welcome to the **TutorMatch Backend** repository! This is the backend component of the TutorMatch application, built using **Flask**, a lightweight Python web framework. This README provides instructions on how to set up, run, and contribute to the project.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Setup Instructions](#setup-instructions)
5. [Running the Application](#running-the-application)
6. [Project Structure](#project-structure)
7. [API Documentation](#api-documentation)
8. [Contributing](#contributing)
9. [License](#license)

---

## Project Overview

TutorMatch is a platform that connects students with tutors for personalized learning. This repository contains the backend logic, including API endpoints, database models, and business logic.

---

## Features

- **User Authentication**: Register, login, and manage user accounts.
- **Tutor Matching**: Match students with tutors based on subjects and availability.
- **Database Integration**: Uses **SQLAlchemy** for database management.
- **RESTful API**: Provides endpoints for frontend integration.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**
- **Pip** (Python package manager)
- **Git** (for version control)
- **PostgreSQL** (or any other database supported by SQLAlchemy)

---

## Setup Instructions

### 1. Clone the Repository

Clone this repository to your local machine:

```
git clone https://github.com/GabrielFigueroaMora/tutormatch_backend.git
cd tutormatch_backend
```

### 2. Set Up a Virtual Environment

1. Create and activate a virtual environment:

```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependecies

Install the required Python packages:

```
pip install -r requirements.txt
```

### 4. Set Up the Database

1. Create a PostgreSQL database (e.g., tutormatch).
2. Update the database configuration in config.py:

```
class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/tutormatch'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

3. Run migrations to create the database schema:

```
flask db upgrade
```

### 5. Running the Application

To run the Flask application, use the following command:

```
python run.py
```

### 6. Project Structure

Here’s an overview of the project structure:

```
tutormatch_backend/
│
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── models.py            # Database models
│   ├── routes.py            # API routes
│   ├── extensions.py        # Flask extensions (e.g., SQLAlchemy)
│   └── (other modules)
│
├── migrations/              # Database migration scripts
├── config.py                # Configuration settings
├── requirements.txt         # Project dependencies
├── run.py                   # Entry point for the application
└── README.md                # Project documentation
```

### 7. API Documentation

The following API endpoints are available:

Authentication
POST /register: Register a new user.
POST /login: Log in and receive an access token.

Tutors
GET /tutors: Get a list of all tutors.
POST /tutors: Add a new tutor.

Students
GET /students: Get a list of all students.
POST /students: Add a new student.

### 8. Contributing

Here’s how you can contribute:

1. Fork the repository.

2. Create a new branch for your feature or bugfix:

```
git checkout -b feature/your-feature-name
```

3. Commit your changes:

```
git commit -m "Add your feature"
```

4. Push to the branch:

```
git push origin feature/your-feature-name
```

5. Open a pull request.

### 9. License
This project is licensed under the MIT License.
