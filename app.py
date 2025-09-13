import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, User, Listing
import cloudinary
import cloudinary.uploader

# Load environment variables from a .env file for local development
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Database Configuration ---
# On Render, it will use the DATABASE_URL environment variable.
# Locally, it will use the sqlite file.
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
# Your existing /price endpoint remains unchanged...
@app.route("/price", methods=["GET"])
def get_price():
    # ... your price scraping logic ...
    pass # (Keeping this brief as it's unchanged)

# --- UPDATED Endpoint to create a listing WITH an image ---
@app.route('/api/listings', methods=['POST'])
def create_listing():
    # 'request.files' holds the image, 'request.form' holds the text data
    image_file = request.files.get('image')
    data = request.form

    if not image_file:
        return jsonify({"error": "Image is required"}), 400

    # Upload the image to Cloudinary
    upload_result = cloudinary.uploader.upload(image_file)
    image_url = upload_result.get('secure_url')

    # Find or create a user (replace with real auth later)
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
        image_url=image_url # Save the URL from Cloudinary
    )
    db.session.add(new_listing)
    db.session.commit()
    
    return jsonify(new_listing.to_dict()), 201

# Get listings endpoint remains the same
@app.route('/api/listings', methods=['GET'])
def get_listings():
    # ... your get listings logic ...
    query = Listing.query.filter_by(status='available')
    listings = query.order_by(Listing.created_at.desc()).all()
    return jsonify([l.to_dict() for l in listings])