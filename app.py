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
# In app.py, add these new routes

@app.route('/api/listings/<int:listing_id>/book', methods=['POST'])
def create_booking(listing_id):
    data = request.get_json()
    # In a real app, renter_id would come from the logged-in user's token
    renter_id = data.get('renter_id', 1) # Using user 1 as default for now
    
    # Simple date handling for now
    from datetime import datetime
    start_date = datetime.utcnow()
    end_date = datetime.utcnow()

    new_booking = Booking(
        listing_id=listing_id,
        renter_id=renter_id,
        start_date=start_date,
        end_date=end_date,
        status='pending'
    )
    db.session.add(new_booking)
    db.session.commit()
    
    return jsonify(new_booking.to_dict()), 201

@app.route('/api/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    data = request.get_json()
    new_status = data.get('status')
    
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
        
    # Add logic here to ensure only the item owner can change the status
    
    booking.status = new_status
    db.session.commit()
    
    return jsonify(booking.to_dict())

@app.route('/api/my-bookings', methods=['GET'])
def get_my_bookings():
    # In a real app, user_id would come from the logged-in user's token
    user_id = request.args.get('user_id', 1)
    
    bookings = Booking.query.filter_by(renter_id=user_id).all()
    return jsonify([b.to_dict() for b in bookings])

# In app.py, add these new routes for the owner

@app.route('/api/my-listings', methods=['GET'])
def get_my_listings():
    # In a real app, user_id would come from a login token.
    # We'll use the default user 1 for now.
    owner_id = request.args.get('owner_id', 1) 
    
    user = User.query.get(owner_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    listings = user.listings # Using the backref relationship we defined in models.py
    return jsonify([l.to_dict() for l in listings])

@app.route('/api/my-listings/<int:listing_id>/bookings', methods=['GET'])
def get_bookings_for_listing(listing_id):
    # This fetches all booking requests for a specific item a user owns.
    listing = Listing.query.get(listing_id)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404

    # Add a check to ensure the person asking is the owner
    # owner_id = get_current_user_id()
    # if listing.owner_id != owner_id:
    #     return jsonify({"error": "Unauthorized"}), 403

    return jsonify([b.to_dict() for b in listing.bookings])