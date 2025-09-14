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

# ✅ FINAL WORKING VERSION of the price scraper
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
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return jsonify({"prices": []})

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("div.table-responsive > table")
        if not table:
            return jsonify({"prices": []})

        rows = table.find_all("tr")
        data = []
        headers = ["district", "market", "commodity", "variety", "max_price", "min_price", "average_price", "arrival_date"]
        
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 8:
                row_data = {headers[i].replace(' ', '_'): col.text.strip() for i, col in enumerate(cols)}
                processed_data = {
                    "date": row_data.get("arrival_date"),
                    "mandi": row_data.get("market"),
                    "avg": row_data.get("average_price")
                }
                data.append(processed_data)

        return jsonify({
            "state": state,
            "commodity": commodity,
            "prices": data
        })
    except Exception as e:
        print(f"Error scraping price data: {e}")
        return jsonify({"error": "Failed to scrape price data."}), 500

# --- Marketplace & Pest Detection Endpoints ---
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

# ... (All other endpoints are correct)