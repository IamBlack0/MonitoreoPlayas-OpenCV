# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)
db = SQLAlchemy()

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.String(50), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='images')
    segmentations = db.relationship('Segmentation', backref='image', lazy=True)
    turbidity = db.relationship('Turbidity', backref='image', lazy=True)
    trash = db.relationship('Trash', backref='image', lazy=True)

class Segmentation(db.Model):
    __tablename__ = 'segmentations'
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.String(50), db.ForeignKey('images.id'))
    class_name = db.Column(db.String(50))
    confidence = db.Column(db.Float)

class Turbidity(db.Model):
    __tablename__ = 'turbidity'
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.String(50), db.ForeignKey('images.id'))
    class_name = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    crop_path = db.Column(db.String(255))

class Trash(db.Model):
    __tablename__ = 'trash'
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.String(50), db.ForeignKey('images.id'))
    class_name = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    location = db.Column(db.String(100))