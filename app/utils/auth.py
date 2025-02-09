# Author: SANJAY KR
from functools import wraps
from flask import request, jsonify, current_app
from ..controllers.auth_controller import verify_token
import logging

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        current_app.logger.info(f"Received Authorization header: {token}")
        
        if not token or not token.startswith('Bearer '):
            current_app.logger.error("Missing or invalid Authorization header format")
            return jsonify({"error": "Missing or invalid token format"}), 401
        
        try:
            token_value = token.split(' ')[1]
            current_app.logger.info("Attempting to verify token")
            username = verify_token(token_value)
            
            if not username:
                current_app.logger.error("Token verification failed")
                return jsonify({"error": "Invalid token"}), 401
                
            current_app.logger.info(f"Token verified successfully for user: {username}")
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error during token verification: {str(e)}")
            return jsonify({"error": "Token verification failed"}), 401
            
    return decorated_function
