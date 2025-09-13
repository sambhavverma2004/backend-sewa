import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, User, Listing
import cloudinary
import cloudinary.uploader
# You might need these for your price scraper
import requests
from bs4 import BeautifulSoup

# Load environment variables from a .env file for local development
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Database Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sewa_mandi.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Cloudinary Configuration ---
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# --- Initialize Extensions ---
db.init_app(app)
migrate = Migrate(app, db)


# --- API Endpoints ---

# --- ✅ NEW: The missing home page route ---
@app.route("/")
def home():
    return jsonify({"message": "SEWA Mandi Backend is running successfully 🎉"})

# Your existing /price endpoint
@app.route("/price", methods=["GET"])
def get_price():
    # ... your full price scraping logic goes here ...
    # This is just a placeholder to ensure it exists
    state = request.args.get("state", "").strip().lower()
    if not state:
        return jsonify({"error": "State is required"}), 400
    return jsonify({"message": f"Price data for {state} would be here."})


# --- Marketplace Endpoints ---

@app.route('/api/listings', methods=['POST'])
def create_listing():
    image_file = request.files.get('image')
    data = request.form

    if not image_file:
        return jsonify({"error": "Image is required"}), 400

    upload_result = cloudinary.uploader.upload(image_file)
    image_url = upload_result.get('secure_url')

    user = User.query.first()
    if not user:
        user = User(phone_number="1234567890", name="Sukhdev Singh", village="Moga")
        db.session.add(user)
        db.session.commit()

    new_listing = Listing(
        owner_id=user.id,
        listing_type=data.get('listing_type'),
        category=data.get('category'),
        title=data.get('title'),
        price=data.get('price'),
        price_unit=data.get('price_unit'),
        location_text=data.get('location_text'),
        image_url=image_url
    )
    db.session.add(new_listing)
    db.session.commit()
    
    return jsonify(new_listing.to_dict()), 201

@app.route('/api/listings', methods=['GET'])
def get_listings():
    query = Listing.query.filter_by(status='available')
    
    listing_type = request.args.get('type')
    if listing_type:
        query = query.filter_by(listing_type=listing_type)
        
    listings = query.order_by(Listing.created_at.desc()).all()
    return jsonify([l.to_dict() for l in listings])
# --- NEW --- Endpoint to get a single listing by its ID
@app.route('/api/listings/<int:listing_id>', methods=['GET'])
def get_listing_detail(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404
    return jsonify(listing.to_dict())