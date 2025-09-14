import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, User, Listing, Booking, Review
import cloudinary
import cloudinary.uploader
import requests
from bs4 import BeautifulSoup
from datetime import datetime

load_dotenv()
app = Flask(__name__)
CORS(app)

# --- Configurations ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sewa_mandi.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
cloudinary.config(
    cloud_name="dvtjxxbtm",
    api_key="223263778434147",
    api_secret="V7MVxbF-NWQtJvWTZbtvxy9yBPI"
)

# --- Initializations ---
db.init_app(app)
migrate = Migrate(app, db)


# --- API Endpoints ---

@app.route("/")
def home():
    return jsonify({"message": "SEWA Mandi Backend is running successfully 🎉"})

# ✅ FIXED: This version has a more robust scraper and better logging
@app.route("/price", methods=["GET"])
def get_price():
    state = request.args.get("state", "").strip().lower()
    commodity = request.args.get("commodity", "").strip().lower()
    mandi = request.args.get("mandi", "").strip().lower()

    if not state or not commodity:
        return jsonify({"error": "Please provide state and commodity"}), 400

    if mandi and mandi != "punjab":
        url = f"https://www.napanta.com/agri-commodity-prices/{state}/{mandi}/{commodity}/"
    else:
        url = f"https://www.napanta.com/agri-commodity-prices/{state}/{commodity}/"

    try:
        print(f"Scraping URL: {url}") # Log the URL being scraped
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        if response.status_code != 200:
            print(f"Scraping failed: Received status code {response.status_code}")
            return jsonify({"prices": []})

        soup = BeautifulSoup(response.text, "html.parser")
        
        # More robustly find the table inside the specific div
        table = soup.select_one("div.table-responsive > table") 
        if not table:
            print("Scraping failed: Could not find the price table on the page.")
            return jsonify({"prices": []})

        rows = table.find_all("tr")
        data = []
        # Use the table headers to create keys dynamically and safely
        headers = [th.text.strip().lower() for th in rows[0].find_all("th")] if rows else []
        
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) == len(headers):
                row_data = {headers[i]: col.text.strip() for i, col in enumerate(cols)}
                # Standardize key names to what the app expects
                processed_data = {
                    "date": row_data.get("date"),
                    "mandi": row_data.get("market"), # The site uses 'market', we'll call it 'mandi'
                    "avg": row_data.get("average price") # The site uses 'average price'
                }
                data.append(processed_data)
        
        print(f"Scraping successful: Found {len(data)} price records.")
        return jsonify({
            "state": state,
            "commodity": commodity,
            "prices": data
        })
    except Exception as e:
        print(f"An unexpected error occurred during scraping: {e}")
        return jsonify({"error": "Failed to scrape price data."}), 500

# --- Marketplace & Pest Detection Endpoints ---
# ... (All your other endpoints are correct and unchanged)
@app.route('/api/listings', methods=['POST'])
def create_listing():
    image_file = request.files.get('image')
    data = request.form
    if not image_file: return jsonify({"error": "Image is required"}), 400
    upload_result = cloudinary.uploader.upload(image_file)
    image_url = upload_result.get('secure_url')
    user = User.query.first()
    if not user:
        user = User(phone_number="1234567890", name="Sukhdev Singh", village="Moga")
        db.session.add(user)
        db.session.commit()
    new_listing = Listing(owner_id=user.id, listing_type=data.get('listing_type'), category=data.get('category'), title=data.get('title'), price=data.get('price'), price_unit=data.get('price_unit'), location_text=data.get('location_text'), image_url=image_url)
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

@app.route('/api/listings/<int:listing_id>', methods=['GET'])
def get_listing_detail(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing: return jsonify({"error": "Listing not found"}), 404
    return jsonify(listing.to_dict())

@app.route('/api/listings/<int:listing_id>/book', methods=['POST'])
def create_booking(listing_id):
    data = request.get_json()
    renter_id = data.get('renter_id', 1)
    new_booking = Booking(listing_id=listing_id, renter_id=renter_id, start_date=datetime.utcnow(), end_date=datetime.utcnow(), status='pending')
    db.session.add(new_booking)
    db.session.commit()
    return jsonify(new_booking.to_dict()), 201

@app.route('/api/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    data = request.get_json()
    booking = Booking.query.get(booking_id)
    if not booking: return jsonify({"error": "Booking not found"}), 404
    booking.status = data.get('status')
    db.session.commit()
    return jsonify(booking.to_dict())

@app.route('/api/my-listings', methods=['GET'])
def get_my_listings():
    owner_id = request.args.get('owner_id', 1) 
    user = User.query.get(owner_id)
    if not user: return jsonify({"error": "User not found"}), 404
    return jsonify([l.to_dict() for l in user.listings])

@app.route('/api/my-listings/<int:listing_id>/bookings', methods=['GET'])
def get_bookings_for_listing(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing: return jsonify({"error": "Listing not found"}), 404
    return jsonify([b.to_dict() for b in listing.bookings])

@app.route('/api/my-bookings', methods=['GET'])
def get_my_bookings():
    user_id = request.args.get('user_id', 1)
    bookings = Booking.query.filter_by(renter_id=user_id).all()
    return jsonify([b.to_dict() for b in bookings])

@app.route('/api/reviews', methods=['POST'])
def post_review():
    data = request.get_json()
    new_review = Review(booking_id=data.get('booking_id'), reviewer_id=data.get('reviewer_id'), reviewee_id=data.get('reviewee_id'), rating=data.get('rating'), comment=data.get('comment'))
    db.session.add(new_review)
    user_to_update = User.query.get(data.get('reviewee_id'))
    if user_to_update:
        ratings = [r.rating for r in Review.query.filter_by(reviewee_id=user_to_update.id).all()]
        user_to_update.average_rating = sum(ratings) / len(ratings) if ratings else 5.0
    db.session.commit()
    return jsonify({"message": "Review submitted successfully"}), 201
    
@app.route('/api/predict-disease', methods=['POST'])
def predict_disease():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    image_file = request.files['image']
    files_payload = {'image': (image_file.filename, image_file.stream, image_file.mimetype)}
    hf_endpoint = "https://anmol1357-crop-disease.hf.space/predict"
    try:
        response = requests.post(hf_endpoint, files=files_payload, timeout=60)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to contact AI service: {e}"}), 503