from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import datetime
from database import get_db
import os

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Get database connection
    db = get_db()

    # Check if username exists
    if db.users.find_one({'username': data.get('username')}):
        return jsonify({"msg": "Username already exists"}), 400
    
    # Create new user
    user = {
        'username': data.get('username'),
        'password': generate_password_hash(data.get('password')),
        'is_admin': False,
        'reviews': [],
        'average_rating': 0,
        'created_at': datetime.datetime.now()
    }
    
    result = db.users.insert_one(user)
    
    # Create access token
    access_token = create_access_token(identity=str(result.inserted_id))
    
    return jsonify({
        "msg": "User registered successfully",
        "user_id": str(result.inserted_id),
        "access_token": access_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    db = get_db()
    
    user = db.users.find_one({'username': data.get('username')})
    
    if not user or not check_password_hash(user['password'], data.get('password')):
        return jsonify({"msg": "Invalid username or password"}), 401
    
    access_token = create_access_token(identity=str(user['_id']))
    
    return jsonify({
        "msg": "Login successful",
        "user_id": str(user['_id']),
        "is_admin": user.get('is_admin', False),
        "access_token": access_token
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()

    db = get_db()
    
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Remove password before sending
    user.pop('password', None)
    user['_id'] = str(user['_id'])
    
    return jsonify(user), 200