from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import database
import os 

# Import and register blueprints
from routes.auth import auth_bp
from routes.items import items_bp
from routes.users import users_bp
from routes.reviews import reviews_bp

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Setup JWT
jwt = JWTManager(app)

try:
    # MongoDB connection
    db = database.init_db(app)

    database.mongo_client.admin.command('ping')
    print("MongoDB connection successful")

except Exception as e:
    print("MongoDB connection failed:", e)


app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(items_bp, url_prefix='/api/items')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(reviews_bp, url_prefix='/api/reviews')

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':

    if os.environ.get('FLASK_ENV') != 'development':
        app.run(debug=True)