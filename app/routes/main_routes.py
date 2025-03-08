from flask import Blueprint

# Create a Blueprint for main routes
main_routes = Blueprint('main_routes', __name__)

@main_routes.route('/')
def home():
    return "Home"