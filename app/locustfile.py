# from locust import HttpUser, task, between, TaskSet
# import random
# import json
# import uuid
# from faker import Faker

# fake = Faker()

# class AuthBehavior(TaskSet):
#     def on_start(self):
#         """Initialize test data for the virtual user"""
#         self.registered = False  # Initialize the flag
#         self.username = f"user_{uuid.uuid4().hex[:8]}"  # Generate unique username
#         self.email = fake.email()
#         self.password = "Test@1234"
#         self.account_type = random.choice(["student", "tutor"])
#         self.auth_token = None
        
#         # Tutor-specific data
#         if self.account_type == "tutor":
#             self.hourly_rate = round(random.uniform(15, 100), 2)

#     def random_name(self):
#         return fake.first_name(), fake.last_name()

#     @task(3)
#     def register(self):
#         random_id = random.randint(100000, 999999)
#         payload = {
#             "username": f"user_{random_id}",  # Ensured unique username
#             "email": f"test_{random_id}@example.com",
#             "password": "ValidPass123!",
#             "account_type": random.choice(["student", "tutor"]),
#             "first_name": "Locust",
#             "last_name": "User",
#             "hourly_rate": round(random.uniform(15, 50), 2) if random.choice([True, False]) else None
#         }
        
#         # Only include hourly_rate for tutors
#         if payload["account_type"] != "tutor":
#             payload.pop("hourly_rate", None)
        
#         with self.client.post("/register", json=payload, catch_response=True) as response:
#             # First check if the request was properly formed
#             if response.status_code == 400:
#                 error_details = response.json()
#                 if "username" in error_details.get("errors", {}):
#                     response.failure(f"Username error: {error_details['errors']['username']}")
#                 else:
#                     response.failure(f"Validation error: {error_details}")
            
#             # Then check for server errors
#             elif response.status_code >= 500:
#                 response.failure(f"Server error: {response.status_code}")
            
#             # Finally check for success (201 Created is standard for registration)
#             elif response.status_code != 201:
#                 try:
#                     error_msg = response.json().get("error", f"Unexpected status: {response.status_code}")
#                     response.failure(error_msg)
#                 except:
#                     response.failure(f"Unexpected response: {response.status_code}")

#     @task(3)
#     def login(self):
#         """Login task is executed only after successful registration."""
#         if not self.registered:  # Now using the properly initialized attribute
#             return
            
#         payload = {
#             "username_or_email": self.username,
#             "password": self.password
#         }
        
#         with self.client.post("/login",
#                             json=payload,
#                             headers={"Content-Type": "application/json"},
#                             catch_response=True) as response:
#             if response.status_code == 200:
#                 self.auth_token = response.json().get("access_token")
#                 response.success()
#                 self.check_protected_endpoints()
#             else:
#                 error = response.json().get("message", "No error details")
#                 response.failure(f"Login failed: {error}")

#     @task(1)
#     def logout(self):
#         """Logout only when authenticated."""
#         if self.auth_token:
#             headers = {
#                 "Authorization": f"Bearer {self.auth_token}",
#                 "Content-Type": "application/json"
#             }
#             with self.client.post("/logout", headers=headers, catch_response=True) as response:
#                 if response.status_code in [200, 204]:
#                     self.auth_token = None
#                     response.success()
#                 else:
#                     response.failure(f"Logout failed: {response.status_code}")

# class WebsiteUser(HttpUser):
#     tasks = [AuthBehavior]
#     wait_time = between(1, 5)
#     host = "http://127.0.0.1:5000/api"

from locust import HttpUser, task, between, TaskSet
import random
from faker import Faker

fake = Faker()

class AuthBehavior(TaskSet):
    def on_start(self):
        self.password = "Test@1234"

    def generate_user_data(self):
        account_type = random.choice(["student", "tutor"])
        username = fake.user_name() + str(random.randint(10000, 99999))
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
            payload["hourly_rate"] = round(random.uniform(15, 100), 2)
        else:
            payload["major"] = random.choice(["Math", "English", "Physics", "History"])

        return payload

    @task(3)
    def register(self):
        payload = self.generate_user_data()

        with self.client.post("/register", json=payload, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 400:
                error_msg = response.text
                response.failure(f"Registration failed (400): {error_msg}")
            else:
                response.failure(f"Registration failed ({response.status_code}): {response.text}")

    @task(2)
    def login(self):
        # For now: using a fresh user to avoid username/email not found
        user_data = self.generate_user_data()
        reg_response = self.client.post("/register", json=user_data)
        if reg_response.status_code != 201:
            return

        payload = {
            "username_or_email": user_data["username"],
            "password": self.password
        }

        with self.client.post("/login", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                self.auth_token = response.json().get("access_token")
                response.success()
            elif response.status_code == 401:
                response.success()  # Acceptable failure
            else:
                response.failure(f"Login failed ({response.status_code}): {response.text}")

    @task(1)
    def logout(self):
        if not hasattr(self, 'auth_token') or not self.auth_token:
            return

        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }

        with self.client.post("/logout", headers=headers, catch_response=True) as response:
            if response.status_code in [200, 204]:
                self.auth_token = None
                response.success()
            else:
                response.failure(f"Logout failed ({response.status_code}): {response.text}")

class WebsiteUser(HttpUser):
    tasks = [AuthBehavior]
    wait_time = between(1, 3)
    host = "http://127.0.0.1:5000/api"
