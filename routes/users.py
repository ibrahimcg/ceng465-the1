from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId
from pymongo import MongoClient
import datetime
from database import get_db


users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    user_id = get_jwt_identity()

    db = get_db()
    
    # Check if user is admin
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get('is_admin', False):
        return jsonify({"msg": "Admin access required"}), 403
    
    users = list(db.users.find({}, {'password': 0}))  # Exclude passwords
    
    # Convert ObjectId to string for JSON serialization
    for user in users:
        user['_id'] = str(user['_id'])
    
    return jsonify(users), 200

@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()

    db = get_db()
    
    # Check if admin or self
    current_user = db.users.find_one({"_id": ObjectId(current_user_id)})
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    
    if str(current_user['_id']) != user_id and not current_user.get('is_admin', False):
        return jsonify({"msg": "Access denied"}), 403
    
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)}, {'password': 0})  # Exclude password
        
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        user['_id'] = str(user['_id'])
        
        return jsonify(user), 200
    except:
        return jsonify({"msg": "Invalid user ID"}), 400

@users_bp.route('', methods=['POST'])
@jwt_required()
def add_user():
    user_id = get_jwt_identity()

    db = get_db()
    
    # Check if admin
    current_user = db.users.find_one({"_id": ObjectId(user_id)})
    if not current_user or not current_user.get('is_admin', False):
        return jsonify({"msg": "Admin access required"}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Username and password are required"}), 400
    
    # Check if username exists
    if db.users.find_one({'username': data['username']}):
        return jsonify({"msg": "Username already exists"}), 400
    
    # Create new user
    new_user = {
        'username': data['username'],
        'password': generate_password_hash(data['password']),
        'is_admin': data.get('is_admin', False),
        'reviews': [],
        'average_rating': 0,
        'created_at': datetime.datetime.now()
    }
    
    result = db.users.insert_one(new_user)
    
    return jsonify({
        "msg": "User created successfully",
        "user_id": str(result.inserted_id)
    }), 201

@users_bp.route('/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()

    db = get_db()   
    
    # Check if admin
    current_user = db.users.find_one({"_id": ObjectId(current_user_id)})
    if not current_user or not current_user.get('is_admin', False):
        return jsonify({"msg": "Admin access required"}), 403
    
    try:
        # Find user first
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        # Update items that were reviewed by this user
        if 'reviews' in user:
            for review in user['reviews']:
                if 'item_id' in review:
                    # Remove the review from the item
                    db.items.update_one(
                        {"_id": ObjectId(review['item_id'])},
                        {"$pull": {"reviews": {"user_id": user_id}}}
                    )
                    
                    # Recalculate average rating
                    item = db.items.find_one({"_id": ObjectId(review['item_id'])})
                    if item and 'reviews' in item and len(item['reviews']) > 0:
                        ratings = [r.get('rating', 0) for r in item['reviews']]
                        avg_rating = sum(ratings) / len(ratings)
                        
                        db.items.update_one(
                            {"_id": ObjectId(review['item_id'])},
                            {
                                "$set": {
                                    "rating": avg_rating,
                                    "number_of_reviewers": len(ratings)
                                }
                            }
                        )
                    else:
                        # No reviews left, reset rating
                        db.items.update_one(
                            {"_id": ObjectId(review['item_id'])},
                            {
                                "$set": {
                                    "rating": 0,
                                    "number_of_reviewers": 0
                                }
                            }
                        )
        
        # Delete the user
        db.users.delete_one({"_id": ObjectId(user_id)})
        
        return jsonify({"msg": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error: {str(e)}"}), 400