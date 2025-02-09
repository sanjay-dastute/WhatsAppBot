# Author: SANJAY KR
from flask import Blueprint, request, jsonify, render_template, make_response, redirect, url_for
from ..controllers.auth_controller import authenticate_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("admin/login.html")
        
    data = request.get_json() if request.is_json else request.form
    if not data:
        return jsonify({"error": "Missing request data"}), 400
        
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    token_data = authenticate_user(username, password)
    if not token_data:
        return jsonify({"error": "Invalid credentials"}), 401
    
    if request.is_json:
        return jsonify(token_data)
    else:
        # For form submissions, set token in localStorage and redirect
        response = make_response("""
            <script>
                localStorage.setItem('token', '{}');
                window.location.href = '/api/v1/admin/dashboard';
            </script>
        """.format(token_data['access_token']))
        response.headers['Content-Type'] = 'text/html'
        return response
