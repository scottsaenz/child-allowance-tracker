from flask import Blueprint, request, jsonify
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Dummy user data for demonstration purposes
AUTHORIZED_USERS = {
    "user1": "password1",
    "user2": "password2"
}

def check_auth(username, password):
    return AUTHORIZED_USERS.get(username) == password

def authenticate():
    return jsonify({"message": "Authentication required"}), 401

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    return jsonify({"message": "Login successful"}), 200

@auth_bp.route('/restricted', methods=['GET'])
@requires_auth
def restricted_area():
    return jsonify({"message": "Welcome to the restricted area!"}), 200