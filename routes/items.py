from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from pymongo import MongoClient
import datetime
from database import get_db

items_bp = Blueprint('items', __name__)

@items_bp.route('', methods=['GET'])
def get_items():
    category = request.args.get('category')

    db = get_db()
    
    query = {}
    if category:
        query['category'] = category
    
    items = list(db.items.find(query))
    
    # Convert ObjectId to string for JSON serialization
    for item in items:
        item['_id'] = str(item['_id'])
    
    return jsonify(items), 200

@items_bp.route('/<item_id>', methods=['GET'])
def get_item(item_id):
    try:

        db = get_db()
        item = db.items.find_one({"_id": ObjectId(item_id)})
        
        if not item:
            return jsonify({"msg": "Item not found"}), 404
        
        item['_id'] = str(item['_id'])
        
        return jsonify(item), 200
    except:
        return jsonify({"msg": "Invalid item ID"}), 400

@items_bp.route('', methods=['POST'])
@jwt_required()
def add_item():
    user_id = get_jwt_identity()
    
    db = get_db()

    # Check if user is admin
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get('is_admin', False):
        return jsonify({"msg": "Admin access required"}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'description', 'price', 'category', 'seller', 'image']
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"Missing required field: {field}"}), 400
    
    # Create item with basic fields
    new_item = {
        'name': data['name'],
        'description': data['description'],
        'price': float(data['price']),
        'category': data['category'],
        'seller': data['seller'],
        'image': data['image'],
        'rating': 0,
        'reviews': [],
        'number_of_reviewers': 0,
        'created_at': datetime.datetime.now()
    }
    
    # Add category-specific fields
    if data['category'] == 'GPS Sport Watches' and 'battery_life' in data:
        new_item['battery_life'] = data['battery_life']
    
    if data['category'] in ['Antique Furniture', 'Vinyls'] and 'age' in data:
        new_item['age'] = data['age']
        
    if data['category'] == 'Running Shoes' and 'size' in data:
        new_item['size'] = data['size']
        
    if data['category'] in ['Antique Furniture', 'Running Shoes'] and 'material' in data:
        new_item['material'] = data['material']
    
    result = db.items.insert_one(new_item)
    
    return jsonify({
        "msg": "Item added successfully",
        "item_id": str(result.inserted_id)
    }), 201

@items_bp.route('/<item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    user_id = get_jwt_identity()

    db = get_db()
    
    # Check if user is admin
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get('is_admin', False):
        return jsonify({"msg": "Admin access required"}), 403
    
    try:
        # Find item first
        item = db.items.find_one({"_id": ObjectId(item_id)})
        if not item:
            return jsonify({"msg": "Item not found"}), 404
        
        # Update users who reviewed this item
        if 'reviews' in item:
            for review in item['reviews']:
                if 'user_id' in review:
                    db.users.update_one(
                        {"_id": ObjectId(review['user_id'])},
                        {"$pull": {"reviews": {"item_id": item_id}}}
                    )
        
        # Delete the item
        db.items.delete_one({"_id": ObjectId(item_id)})
        
        return jsonify({"msg": "Item deleted successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error: {str(e)}"}), 400