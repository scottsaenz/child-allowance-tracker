from functools import wraps
from flask import request, abort
import os

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_token = request.headers.get('Authorization')
        if not auth_token or auth_token != os.getenv('AUTH_TOKEN'):
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated

def log_request(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        print(f"Request made to {request.path} with method {request.method}")
        return f(*args, **kwargs)
    return decorated