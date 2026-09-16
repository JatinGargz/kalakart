from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Artisan(Base):
    __tablename__ = "artisans"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    state = Column(String, nullable=False)
    cluster = Column(String, nullable=False)
    craft_type = Column(String, nullable=False)
    scheme_id = Column(String, nullable=True) # PM Vishwakarma / PM-DAKSH
    bio = Column(Text, nullable=True)
    gi_tag = Column(String, nullable=True)
    experience_years = Column(Integer, default=15)
    total_sales = Column(Float, default=42850.0)
    active_listings = Column(Integer, default=18)
    pending_orders = Column(Integer, default=7)
    total_earnings = Column(Float, default=28400.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="artisan")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, index=True)
    artisan_id = Column(String, ForeignKey("artisans.id"), nullable=False)
    title_en = Column(String, nullable=False)
    title_hi = Column(String, nullable=False)
    craft_type = Column(String, nullable=False)
    material = Column(String, nullable=True)
    location = Column(String, nullable=True)
    production_time = Column(String, default="3-5 days")
    story_en = Column(Text, nullable=True)
    story_hi = Column(Text, nullable=True)
    dimensions = Column(String, default="Dia: 10 in • H: 1.5 in")
    weight = Column(String, default="650 grams")
    tags = Column(String, default="Handmade,GI Tag,Eco-friendly")
    rating = Column(Float, default=4.9)
    reviews_count = Column(Integer, default=24)
    is_trending = Column(Boolean, default=True)
    status = Column(String, default="PUBLISHED")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    artisan = relationship("Artisan", back_populates="products")
    media = relationship("ProductMedia", back_populates="product", uselist=False, cascade="all, delete-orphan")
    pricing = relationship("ProductPricing", back_populates="product", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="product")
    reviews = relationship("Review", back_populates="product")

class ProductMedia(Base):
    __tablename__ = "product_media"
    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    original_url = Column(String, nullable=False)
    enhanced_studio_url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)

    product = relationship("Product", back_populates="media")

class ProductPricing(Base):
    __tablename__ = "product_pricing"
    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    material_cost = Column(Float, default=400.0)
    labor_hours = Column(Float, default=8.0)
    guaranteed_labor_wage = Column(Float, default=800.0)
    cost_floor = Column(Float, nullable=False)
    recommended_retail_price = Column(Float, nullable=False)
    wholesale_b2b_price = Column(Float, nullable=False)
    profit_margin_pct = Column(Float, default=42.0)
    model_version = Column(String, default="RandomForest-v1.0 (300 estimators)")
    explanation = Column(Text, nullable=True)

    product = relationship("Product", back_populates="pricing")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    product_title = Column(String, nullable=False)
    buyer_name = Column(String, nullable=False)
    delivery_city = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    buyer_app = Column(String, default="Paytm ONDC Store")
    payment_status = Column(String, default="SETTLED_VIA_UPI")
    order_status = Column(String, default="Confirmed") # Confirmed, Processing, Shipped, Delivered
    tracking_id = Column(String, nullable=False)
    artisan_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="orders")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    user_name = Column(String, nullable=False)
    rating = Column(Float, default=5.0)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="reviews")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    role = Column(String, default="artisan")
    pw_salt = Column(String, nullable=False)
    pw_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")

class AuthToken(Base):
    __tablename__ = "auth_tokens"
    token_hash = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="tokens")
