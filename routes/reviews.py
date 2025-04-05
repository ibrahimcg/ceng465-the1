from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from pymongo import MongoClient
import datetime
from database import get_db

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/<item_id>/rate', methods=['POST'])
@jwt_required()
def rate_item(item_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    db = get_db()
    
    # Validate rating
    if 'rating' not in data:
        return jsonify({"msg": "Rating is required"}), 400
    
    try:
        rating = int(data['rating'])
        if rating < 1 or rating > 10:
            return jsonify({"msg": "Rating must be between 1 and 10"}), 400
    except:
        return jsonify({"msg": "Rating must be a number between 1 and 10"}), 400
    
    try:
        # Find the item
        item = db.items.find_one({"_id": ObjectId(item_id)})
        if not item:
            return jsonify({"msg": "Item not found"}), 404
        
        # Find the user
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        # Check if user has already rated this item
        existing_review = None
        for review in item.get('reviews', []):
            if review.get('user_id') == user_id:
                existing_review = review
                break
        
        if existing_review:
            # Update existing review's rating
            db.items.update_one(
                {"_id": ObjectId(item_id), "reviews.user_id": user_id},
                {"$set": {"reviews.$.rating": rating}}
            )
        else:
            # Add new review with rating
            review = {
                "user_id": user_id,
                "username": user['username'],
                "rating": rating,
                "date": datetime.datetime.now()
            }
            
            db.items.update_one(
                {"_id": ObjectId(item_id)},
                {"$push": {"reviews": review}}
            )
            
            # Add to user's reviews if not already there
            user_has_review = False
            for r in user.get('reviews', []):
                if r.get('item_id') == item_id:
                    user_has_review = True
                    break
            
            if not user_has_review:
                user_review = {
                    "item_id": item_id,
                    "item_name": item['name'],
                    "rating": rating,
                    "date": datetime.datetime.now()
                }
                
                db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$push": {"reviews": user_review}}
                )
        
        # Recalculate average rating
        item = db.items.find_one({"_id": ObjectId(item_id)})
        if item and 'reviews' in item and len(item['reviews']) > 0:
            ratings = [r.get('rating', 0) for r in item['reviews'] if 'rating' in r]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                
                db.items.update_one(
                    {"_id": ObjectId(item_id)},
                    {
                        "$set": {
                            "rating": round(avg_rating, 1),
                            "number_of_reviewers": len(ratings)
                        }
                    }
                )
        
        return jsonify({"msg": "Item rated successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error: {str(e)}"}), 400

@reviews_bp.route('/<item_id>/review', methods=['POST'])
@jwt_required()
def review_item(item_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    db = get_db()
    
    # Validate review
    if 'content' not in data or not data['content'].strip():
        return jsonify({"msg": "Review content is required"}), 400
    
    try:
        # Find the item
        item = db.items.find_one({"_id": ObjectId(item_id)})
        if not item:
            return jsonify({"msg": "Item not found"}), 404
        
        # Find the user
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        # Check if user has already reviewed this item
        existing_review = None
        for review in item.get('reviews', []):
            if review.get('user_id') == user_id:
                existing_review = review
                break
        
        if existing_review:
            # Update existing review
            db.items.update_one(
                {"_id": ObjectId(item_id), "reviews.user_id": user_id},
                {"$set": {
                    "reviews.$.content": data['content'],
                    "reviews.$.updated_at": datetime.datetime.now()
                }}
            )
        else:
            # Create new review
            review = {
                "user_id": user_id,
                "username": user['username'],
                "content": data['content'],
                "date": datetime.datetime.now()
            }
            
            db.items.update_one(
                {"_id": ObjectId(item_id)},
                {"$push": {"reviews": review}}
            )
        
        # Update user's reviews
        user_has_review = False
        for i, r in enumerate(user.get('reviews', [])):
            if r.get('item_id') == item_id:
                user_has_review = True
                # Update user's review
                db.users.update_one(
                    {"_id": ObjectId(user_id), "reviews.item_id": item_id},
                    {"$set": {
                        "reviews.$.content": data['content'],
                        "reviews.$.updated_at": datetime.datetime.now()
                    }}
                )
                break
        
        if not user_has_review:
            user_review = {
                "item_id": item_id,
                "item_name": item['name'],
                "content": data['content'],
                "date": datetime.datetime.now()
            }
            
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {"reviews": user_review}}
            )
        
        return jsonify({"msg": "Review added successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error: {str(e)}"}), 400