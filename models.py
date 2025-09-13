# In /Users/sambhavverma/Desktop/sewa/backend sewa/models.py

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    village = db.Column(db.String(100))
    # We will add ratings later
    listings = db.relationship('Listing', backref='owner', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "village": self.village
        }

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    listing_type = db.Column(db.String(10), nullable=False) # 'rent' or 'sell'
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    price_unit = db.Column(db.String(20), nullable=False) # 'per_hour', 'per_acre', 'total_price'
    includes_operator = db.Column(db.Boolean, default=False)
    location_text = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(20), default='available', nullable=False)
    image_url = db.Column(db.String(255)) # For MVP, we'll start with one image
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "owner": self.owner.to_dict(),
            "listing_type": self.listing_type,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "phone_number": self.phone_number,
            "price_unit": self.price_unit,
            "includes_operator": self.includes_operator,
            "location_text": self.location_text,
            "image_url": self.image_url,
            "status": self.status
        }