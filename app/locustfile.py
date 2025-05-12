from locust import HttpUser, task, between
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker()

class BookingBehavior:
    password = "Test@1234"

    def generate_user_data(self, account_type):
        username = fake.user_name() + str(random.randint(1000, 9999))
        email = fake.email()
        first_name = fake.first_name()
        last_name = fake.last_name()

        payload = {
            "username": username,
            "email": email,
            "password": self.password,
            "account_type": account_type,
            "first_name": first_name,
            "last_name": last_name
        }

        if account_type == "tutor":
            payload["hourly_rate"] = round(random.uniform(15, 50), 2)
        else:
            payload["major"] = random.choice(["Math", "Physics", "Biology"])

        return payload

    def register_user(self, client, user_data):
        return client.post("/register", json=user_data)

    def login_user(self, client, username):
        return client.post("/login", json={
            "username_or_email": username,
            "password": self.password
        })

    def logout_user(self, client, token):
        return client.post("/logout", headers={"Authorization": f"Bearer {token}"})

    def create_availability(self, client, token):
        start = datetime.utcnow() + timedelta(minutes=10)
        end = start + timedelta(hours=1)

        resp = client.post("/tutor/availability", json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat()
        }, headers={"Authorization": f"Bearer {token}"})

        if resp.status_code == 201:
            return resp.json()["id"]
        return None

    def book_session(self, client, token, slot_id):
        return client.post("/student/sessions", json={"slot_id": slot_id}, headers={"Authorization": f"Bearer {token}"})


class FullBookingFlow(HttpUser):
    wait_time = between(1, 3)
    host = "http://127.0.0.1:5000/api"
    behavior = BookingBehavior()

    @task
    def tutor_student_booking_flow(self):
        # Tutor flow
        tutor_data = self.behavior.generate_user_data("tutor")
        print("Registering tutor:", tutor_data)
        reg_response = self.behavior.register_user(self.client, tutor_data)
        print("Tutor registration response:", reg_response.status_code, reg_response.text)
        assert reg_response.status_code == 201, "Tutor registration failed"

        login_response = self.behavior.login_user(self.client, tutor_data["username"])
        assert login_response.status_code == 200, "Tutor login failed"
        tutor_token = login_response.json()["access_token"]

        slot_id = self.behavior.create_availability(self.client, tutor_token)
        assert slot_id, "Slot creation failed"

        self.behavior.logout_user(self.client, tutor_token)

        # Student flow
        student_data = self.behavior.generate_user_data("student")
        print("Registering student:", student_data)
        reg_response = self.behavior.register_user(self.client, student_data)
        print("Student registration response:", reg_response.status_code, reg_response.text)
        assert reg_response.status_code == 201, "Student registration failed"

        login_response = self.behavior.login_user(self.client, student_data["username"])
        assert login_response.status_code == 200, "Student login failed"
        student_token = login_response.json()["access_token"]

        book_response = self.behavior.book_session(self.client, student_token, slot_id)
        assert book_response.status_code == 201, f"Booking failed: {book_response.text}"

        self.behavior.logout_user(self.client, student_token)


# This class delegates to FullBookingFlow's task
class WebsiteUser(FullBookingFlow):
    tasks = [FullBookingFlow.tutor_student_booking_flow]

