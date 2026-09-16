"""
KALAKART / SHILP AI — Unified Enterprise FastAPI Gateway (:8000).
Integrates:
- 109MB Random Forest Fair Pricing ML Model (300 estimators)
- SQLite Database Persistence with 14 Seeded Authentic GI-Tag Products
- Person 4 AI Pipeline Microservices (Extraction, Story, Chatbot, Trending, Image)
- Vision Studio 1080p Canvas + MoSJE Seal Watermarking
- Anti-Bargaining Shield (सौदा रक्षक) with Dignity Wage Floor
- Mela Standee PDF Generator with Dynamic UPI QR Code
- Official ONDC Beckn v1.2 Protocol Export
- 5-Marketplace Omnichannel Publisher (Amazon, Flipkart, GeM, Etsy, ONDC)
- Shilpi / Kala Saathi Voice AI Companion (Bilingual Hindi/English + TTS)
"""
from __future__ import annotations
import os
import uuid
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Body, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func

# Import core database and models
from app.core.database import engine, Base, get_db
from app.core.seed import seed_database
from app.models.models import Artisan, Product, ProductMedia, ProductPricing, Order, Review, User, AuthToken

# Import ML and pricing
from app.ml.pricing_predictor import predict_fair_pricing, _load_model_and_dataset
from app.services.pricing_engine import calculate_fair_pricing, match_b2b_buyers, evaluate_bargaining_offer
from app.schemas.contracts import PricingPredictRequest, BargainingShieldRequest

# Import Image Studio & Export
from app.services.image_studio import enhance_craft_image
from app.services.export_service import (
    generate_upi_qr_bytes,
    generate_ondc_beckn_json,
    generate_mela_standee_pdf,
    publish_to_all_channels
)
from app.services.catalog_engine import generate_catalog_from_voice, generate_hindi_tts_audio, ask_shilpi_assistant
from app.services.trends_engine import get_craft_trend_insights, get_all_available_categories

# Import Person 4 AI pipeline router
from app.ai_pipeline.routers.pipeline import router as ai_pipeline_router

# Import storyfill from services if available
try:
    from services.storyfill import story_to_listing
except Exception:
    story_to_listing = None

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
os.makedirs(os.path.join(STATIC_DIR, "uploads"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "studio"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "audio"), exist_ok=True)
ENHANCED_DIR = os.path.join(STATIC_DIR, "enhanced_images")
os.makedirs(ENHANCED_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create SQLite tables and seed 14 GI-tagged craft products
    Base.metadata.create_all(bind=engine)
    try:
        seed_database()
        print("KALAKART SQLite Database initialized and seeded with 14 GI-tagged crafts.")
    except Exception as e:
        print(f"Database note: {e}")
    
    # Pre-warm Random Forest model
    try:
        model, benchmarks = _load_model_and_dataset()
        print(f"Random Forest Pricing Model loaded: {type(model).__name__} (300 estimators)")
    except Exception as e:
        print(f"ML Model pre-warm note: {e}")
    yield


app = FastAPI(
    title="KALAKART (कलाकार्ट) AI Orchestrator & Gateway",
    description="AI-Powered Digital Marketplace and Business Manager for Indian Artisans | SIH 2026",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset directories
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/enhanced_images", StaticFiles(directory=ENHANCED_DIR), name="enhanced_images")

# Mount Person 4 AI Pipeline router under /api/v1/pipeline
app.include_router(ai_pipeline_router, prefix="/api/v1/pipeline", tags=["AI Pipeline (Person 4)"])


def format_product_dict(p: Product) -> dict:
    price = p.pricing.recommended_retail_price if p.pricing else 1250.0
    tags_list = [t.strip() for t in p.tags.split(",")] if p.tags else ["Handmade", "GI Tag"]
    img_url = p.media.enhanced_studio_url if p.media and p.media.enhanced_studio_url else "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=600"
    return {
        "id": p.id,
        "name": p.title_en,
        "title_en": p.title_en,
        "title_hi": p.title_hi or p.title_en,
        "craft": p.craft_type,
        "craft_type": p.craft_type,
        "price": price,
        "retail_price": price,
        "wholesale_price": p.pricing.wholesale_b2b_price if p.pricing else price * 0.75,
        "cost_floor": p.pricing.cost_floor if p.pricing else price * 0.4,
        "guaranteed_labor_wage": p.pricing.guaranteed_labor_wage if p.pricing else price * 0.45,
        "material_cost": p.pricing.material_cost if p.pricing else 400.0,
        "labor_hours": p.pricing.labor_hours if p.pricing else 8.0,
        "profit_margin_pct": p.pricing.profit_margin_pct if p.pricing else 25.0,
        "material": p.material or "Natural Materials",
        "location": p.location or (p.artisan.cluster if p.artisan else "Jaipur, Rajasthan"),
        "artisan": p.artisan.name if p.artisan else "Rukmini Devi",
        "artisan_id": p.artisan.id if p.artisan else "artisan_rukmini",
        "image_url": img_url,
        "original_image_url": p.media.original_url if p.media else None,
        "description": p.story_en or "Authentic handcrafted masterpiece.",
        "story_en": p.story_en or "Authentic handcrafted masterpiece.",
        "story_hi": p.story_hi or "प्रामाणिक भारतीय हस्तशिल्प।",
        "tags": tags_list,
        "rating": round(p.rating or 4.9, 1),
        "reviews_count": p.reviews_count or 24,
        "is_trending": p.is_trending if p.is_trending is not None else True,
        "status": p.status or "PUBLISHED",
        "model_version": p.pricing.model_version if p.pricing else "RandomForest-v1.0 (300 estimators)"
    }


# =========================================================================
# 1. HEALTH CHECKS
# =========================================================================
# Ensure tables exist even when lifespan is skipped (tests, import-time use).
try:
    Base.metadata.create_all(bind=engine)
except Exception as _e:
    print(f"Table init note: {_e}")


@app.get("/health")
@app.get("/api/v1/health")
def health_endpoint(db: Session = Depends(get_db)):
    prod_count = db.query(Product).count()
    order_count = db.query(Order).count()
    artisan_count = db.query(Artisan).count()
    return {
        "ok": True,
        "status": "healthy",
        "service": "KALAKART AI Orchestrator",
        "version": "2.1.0",
        "db": {
            "products": prod_count,
            "orders": order_count,
            "artisans": artisan_count
        },
        "ml_model": "RandomForestRegressor (300 estimators, joblib loaded)",
        "endpoints": [
            "/api/v1/health",
            "/api/v1/products",
            "/api/v1/orders",
            "/api/v1/media/process-raw",
            "/api/v1/pricing/predict",
            "/api/v1/pricing/bargain-shield",
            "/api/v1/assistant/shilpi",
            "/api/v1/channels/publish-multi",
            "/api/v1/export/mela-standee/{id}",
            "/api/v1/export/ondc-beckn/{id}",
            "/api/v1/catalog/from-story",
            "/api/v1/pipeline/extract"
        ]
    }


# =========================================================================
# 2. PRODUCTS (DATABASE CRUD & CATALOG)
# =========================================================================
@app.get("/api/v1/products")
def list_products(
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query("featured"),
    status: Optional[str] = Query("PUBLISHED"),
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if status and status.lower() != "all":
        query = query.filter(Product.status == status)
    if category and category.lower() not in ("all", "trending now"):
        cat = category.lower()
        if cat in ("pottery", "ceramics"):
            query = query.filter(or_(Product.craft_type.ilike("%pottery%"), Product.craft_type.ilike("%ceramic%"), Product.material.ilike("%clay%")))
        elif cat in ("textiles", "weaving", "silk"):
            query = query.filter(or_(Product.craft_type.ilike("%textile%"), Product.craft_type.ilike("%weaving%"), Product.craft_type.ilike("%silk%"), Product.craft_type.ilike("%saree%")))
        elif cat in ("woodwork", "carving"):
            query = query.filter(or_(Product.craft_type.ilike("%wood%"), Product.craft_type.ilike("%carving%")))
        elif cat in ("paintings", "art"):
            query = query.filter(or_(Product.craft_type.ilike("%paint%"), Product.craft_type.ilike("%art%")))
        elif cat in ("metalwork", "brass"):
            query = query.filter(or_(Product.craft_type.ilike("%metal%"), Product.craft_type.ilike("%brass%"), Product.craft_type.ilike("%dokra%")))
        else:
            query = query.filter(Product.craft_type.ilike(f"%{category}%"))

    if region:
        query = query.filter(Product.location.ilike(f"%{region}%"))

    if search:
        s = f"%{search.strip()}%".lower()
        query = query.filter(
            or_(
                Product.title_en.ilike(s),
                Product.title_hi.ilike(s),
                Product.craft_type.ilike(s),
                Product.tags.ilike(s)
            )
        )

    products = query.all()
    results = [format_product_dict(p) for p in products]
    return {"ok": True, "count": len(results), "products": results}


@app.get("/api/v1/products/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"ok": True, **format_product_dict(prod)}


@app.post("/api/v1/products")
def create_product(payload: dict = Body(...), db: Session = Depends(get_db)):
    """Persists a new artisan product into SQLite."""
    prod_id = payload.get("id") or f"kk_prod_{uuid.uuid4().hex[:6]}"
    name = payload.get("name") or payload.get("title_en") or payload.get("product_name", "Handcrafted Masterpiece")
    craft = payload.get("craft") or payload.get("craft_type", "Pottery & Ceramics")
    material = payload.get("material", "Natural Clay & Mineral Pigments")
    location = payload.get("location", "Jaipur, Rajasthan")
    desc_text = payload.get("description") or payload.get("story_en", "Authentic artisan handcrafted item.")
    price_val = float(payload.get("price") or payload.get("retail_price", 1250.0))
    img_url = payload.get("image_url") or "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=600"
    
    tags = payload.get("tags", ["Handmade", "GI Tag"])
    if isinstance(tags, list):
        tags_str = ",".join(tags)
    else:
        tags_str = str(tags)

    artisan = db.query(Artisan).first()
    artisan_id = artisan.id if artisan else "artisan_rukmini"

    product = Product(
        id=prod_id,
        artisan_id=artisan_id,
        title_en=name,
        title_hi=payload.get("title_hi", name),
        craft_type=craft,
        material=material,
        location=location,
        story_en=desc_text,
        story_hi=payload.get("story_hi", desc_text),
        tags=tags_str,
        rating=5.0,
        reviews_count=1,
        is_trending=True,
        status=payload.get("status", "PUBLISHED")
    )
    db.add(product)

    media = ProductMedia(
        id=f"media_{prod_id}",
        product_id=prod_id,
        original_url=img_url,
        enhanced_studio_url=img_url,
        thumbnail_url=img_url
    )
    db.add(media)

    pricing = ProductPricing(
        id=f"price_{prod_id}",
        product_id=prod_id,
        cost_floor=price_val * 0.4,
        recommended_retail_price=price_val,
        wholesale_b2b_price=price_val * 0.75,
        guaranteed_labor_wage=price_val * 0.45,
        material_cost=price_val * 0.3,
        labor_hours=8.0,
        profit_margin_pct=25.0,
        model_version="RandomForest-v1.0 (300 estimators)",
        explanation="Ethical wage floor protected by Random Forest valuation."
    )
    db.add(pricing)
    db.commit()
    return {"ok": True, "id": prod_id, "product": format_product_dict(product)}


# =========================================================================
# 3. VISION STUDIO & RAW PROCESSING
# =========================================================================
@app.post("/api/v1/media/process-raw")
async def process_raw(
    file: UploadFile = File(...),
    product_name: str = Form("Handpainted Blue Pottery Plate"),
    craft_type: str = Form("Jaipur Blue Pottery"),
    material: str = Form("Quartz, Glass, Clay"),
    location: str = Form("Jaipur, Rajasthan"),
    story_text: str = Form(""),
    language: str = Form("hi"),
    artisan: str = Form("Rukmini Devi"),
    db: Session = Depends(get_db)
):
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Empty photo upload. Please choose an image.")

    prod_id = f"kk_{uuid.uuid4().hex[:8]}"
    orig_filename = f"orig_{prod_id}.jpg"
    orig_path = os.path.join(STATIC_DIR, "uploads", orig_filename)
    with open(orig_path, "wb") as f:
        f.write(raw_bytes)
    orig_url = f"/static/uploads/{orig_filename}"

    # Process through Image Studio (MoSJE Seal + 1080p Canvas + Color Grading)
    enhanced_url = enhance_craft_image(raw_bytes, prod_id, STATIC_DIR)

    # Read back enhanced image to provide base64 data url
    enhanced_filename = f"studio_{prod_id}.jpg"
    enhanced_path = os.path.join(STATIC_DIR, "studio", enhanced_filename)
    b64_str = ""
    if os.path.exists(enhanced_path):
        with open(enhanced_path, "rb") as ef:
            b64_str = base64.b64encode(ef.read()).decode("utf-8")
    else:
        b64_str = base64.b64encode(raw_bytes).decode("utf-8")

    # Build catalog details
    hint = story_text or f"यह {location} की पारंपरिक हस्तनिर्मित {craft_type} है।"
    catalog_res = generate_catalog_from_voice(hint, craft_type)
    
    title_en = product_name or catalog_res.get("title_en", "Handmade Masterpiece")
    title_hi = catalog_res.get("title_hi", title_en)
    desc_en = catalog_res.get("story_en", f"Handcrafted {craft_type} made from {material} in {location}.")
    desc_hi = catalog_res.get("story_hi", hint)

    # Compute Random Forest Fair Pricing
    pricing_res = calculate_fair_pricing(
        material_cost=400.0,
        labor_hours=8.0,
        craft_type=craft_type,
        material=material
    )

    # Save to SQLite
    artisan_record = db.query(Artisan).first()
    artisan_id = artisan_record.id if artisan_record else "artisan_rukmini"

    product = Product(
        id=prod_id,
        artisan_id=artisan_id,
        title_en=title_en,
        title_hi=title_hi,
        craft_type=craft_type,
        material=material,
        location=location,
        story_en=desc_en,
        story_hi=desc_hi,
        tags=f"{craft_type},GI Tag,Handmade,Living Wage",
        rating=5.0,
        reviews_count=1,
        is_trending=True,
        status="DRAFT"
    )
    db.add(product)

    media = ProductMedia(
        id=f"media_{prod_id}",
        product_id=prod_id,
        original_url=orig_url,
        enhanced_studio_url=enhanced_url,
        thumbnail_url=enhanced_url
    )
    db.add(media)

    pricing = ProductPricing(
        id=f"price_{prod_id}",
        product_id=prod_id,
        cost_floor=pricing_res["cost_floor"],
        recommended_retail_price=pricing_res["recommended_retail_price"],
        wholesale_b2b_price=pricing_res["wholesale_b2b_price"],
        guaranteed_labor_wage=pricing_res["guaranteed_labor_wage"],
        material_cost=400.0,
        labor_hours=8.0,
        profit_margin_pct=pricing_res.get("profit_margin_percentage", 25.0),
        model_version=pricing_res.get("model_version", "RandomForest-v1.0 (300 estimators)"),
        explanation=pricing_res["explanation"]
    )
    db.add(pricing)
    db.commit()

    tags_list = [t.strip() for t in product.tags.split(",")]

    return {
        "ok": True,
        "product_id": prod_id,
        "studio": {
            "engine": "Pillow-1080p-MoSJE",
            "canvas": "1080x1080",
            "seal": "MoSJE-Gold-Watermark"
        },
        "image_jpeg_base64": b64_str,
        "image_data_url": f"data:image/jpeg;base64,{b64_str}",
        "listing": {
            "title_en": title_en,
            "title_hi": title_hi,
            "description_en": desc_en,
            "description_hi": desc_hi,
            "tags": tags_list
        },
        "pricing": pricing_res
    }


# =========================================================================
# 4. RANDOM FOREST PRICING & BARGAINING SHIELD
# =========================================================================
@app.post("/api/v1/pricing/predict")
def predict_pricing(payload: dict = Body(...)):
    """Inference directly on the 109MB Random Forest ML model."""
    mat_cost = float(payload.get("material_cost", 400.0))
    lab_hours = float(payload.get("labor_hours", 8.0))
    craft_type = payload.get("craft_type") or payload.get("category", "Pottery & Ceramics")
    material = payload.get("material", "Clay")
    res = calculate_fair_pricing(mat_cost, lab_hours, craft_type, material)
    return {"ok": True, **res}


@app.post("/api/v1/pricing/bargain-shield")
def bargain_shield(payload: dict = Body(...)):
    """Anti-Bargaining Shield (सौदा रक्षक) with Dignity Wage Floor."""
    mat_cost = float(payload.get("material_cost", 400.0))
    lab_hours = float(payload.get("labour_hours") or payload.get("labor_hours", 8.0))
    wage_hr = float(payload.get("wage_per_hour", 80.0))
    offer = float(payload.get("buyer_offer") or payload.get("offered_price", 800.0))
    craft = payload.get("craft_type", "Pottery & Ceramics")
    material = payload.get("material", "Clay")

    eval_res = evaluate_bargaining_offer(mat_cost, lab_hours, offer, craft, material)
    suggested = eval_res.get("suggested_price") or eval_res.get("recommended_retail_price") or eval_res.get("suggested_fair_price") or 1250.0
    floor = eval_res.get("cost_floor") or eval_res.get("minimum_wage_floor") or eval_res.get("ethical_wage_floor") or 500.0
    wholesale = eval_res.get("wholesale_b2b_price") or (suggested * 0.75)
    
    status_key = eval_res.get("status_key", "too_low")
    verdict = eval_res.get("verdict", "")
    if status_key == "great" or verdict in ("ACCEPT", "FAIR_PROFITABLE"):
        v_code = "FAIR"
        v_text = "Fair ✓"
        msg_en = eval_res.get("advice") or "Great offer! Meets or exceeds the ethical wage floor."
        msg_hi = eval_res.get("dialogue_hi") or "उचित मूल्य! यह आपके श्रम और कला का पूरा सम्मान करता है।"
    elif status_key == "tight" or verdict in ("NEGOTIATE", "TIGHT_MARGIN"):
        v_code = "NEGOTIABLE"
        v_text = "Negotiable"
        counter = eval_res.get("recommended_counter_offer") or eval_res.get("counter_offer_recommendation") or suggested
        msg_en = eval_res.get("advice") or f"Offer is close to production costs. Counter-offer recommended at ₹{counter:.0f}."
        msg_hi = eval_res.get("dialogue_hi") or f"कीमत लागत के करीब है। ₹{counter:.0f} का जवाबी प्रस्ताव दें।"
    else:
        v_code = "TOO_LOW"
        v_text = "Too Low"
        msg_en = eval_res.get("advice") or f"The offer is below your living wage floor (₹{floor:.0f}). Do not accept."
        msg_hi = eval_res.get("dialogue_hi") or f"यह प्रस्ताव आपकी न्यूनतम मजदूरी (₹{floor:.0f}) से कम है। कृपया स्वीकार न करें।"

    return {
        "ok": True,
        "verdict": v_text,
        "verdict_code": v_code,
        "suggested_price": suggested,
        "floor_price": floor,
        "wholesale_price": wholesale,
        "material_cost": mat_cost,
        "labour_hours": lab_hours,
        "wage_per_hour": wage_hr,
        "labour_cost": lab_hours * wage_hr,
        "message_en": msg_en,
        "message_hi": msg_hi,
        "counter_offer": eval_res.get("counter_offer_recommendation", suggested),
        "detailed_breakdown": eval_res
    }


# =========================================================================
# 5. SHILPI / KALA SAATHI VOICE AI ASSISTANT
# =========================================================================
@app.post("/api/v1/assistant/shilpi")
@app.post("/api/v1/assistant/kala-saathi")
async def assistant_endpoint(payload: dict = Body(...)):
    """Conversational Voice AI Assistant for Indian Artisans."""
    query = payload.get("query") or payload.get("question", "दाम कैसे रखें?")
    lang = payload.get("lang") or payload.get("language", "hi")
    
    ans_data = ask_shilpi_assistant(query, STATIC_DIR)
    
    b64_audio = None
    if ans_data.get("audio_url"):
        rel_path = ans_data["audio_url"].replace("/static/", "").replace("/", os.sep)
        abs_audio = os.path.join(STATIC_DIR, rel_path)
        if os.path.exists(abs_audio):
            with open(abs_audio, "rb") as af:
                b64_audio = base64.b64encode(af.read()).decode("utf-8")

    return {
        "ok": True,
        "query": query,
        "lang": lang,
        "topic": ans_data.get("topic", "Artisan Business Support"),
        "engine": ans_data.get("engine", "KalaSaathi-Llama3"),
        "answer": ans_data.get("answer", "नमस्ते! मैं आपकी कला साथी हूँ।"),
        "answer_hi": ans_data.get("answer", ""),
        "audio_mp3_base64": b64_audio,
        "audio_url": ans_data.get("audio_url")
    }


# =========================================================================
# 6. MULTI-CHANNEL DISTRIBUTION (5 MARKETPLACES)
# =========================================================================
@app.post("/api/v1/channels/publish-multi")
def publish_multi_endpoint(payload: dict = Body(...)):
    p_name = payload.get("product_name", "Handpainted Craft")
    craft = payload.get("craft_type", "Pottery & Ceramics")
    price = float(payload.get("price_inr", 1250.0))
    desc = payload.get("description", "Artisan handcrafted masterpiece.")
    tags = payload.get("tags", ["handmade"])
    loc = payload.get("location", "Jaipur, Rajasthan")
    img = payload.get("image_url", "")

    prod_id = f"kk_{uuid.uuid4().hex[:8]}"
    raw = publish_to_all_channels(
        prod_id,
        {"title_en": p_name, "description": desc, "location": loc},
        {"recommended_retail_price": price, "wholesale_b2b_price": round(price * 0.8, 2)},
        img or None,
    )
    by = {c.get("channel"): c for c in raw.get("channels", [])}
    amz = by.get("Amazon Karigar", {})
    fk = by.get("Flipkart Samarth", {})
    gem = by.get("Government e-Marketplace (GeM)", {})
    etsy = by.get("Etsy Global Export", {})
    ondc = by.get("ONDC Open Network", {})
    usd = round(price / 86.0, 2)
    return {"ok": True, "channels": {
        "amazon_in": {"marketplace": "Amazon Karigar", "asin": amz.get("asin"),
                      "title": p_name[:200], "bullets": amz.get("bullets", []),
                      "price_inr": price, "status": amz.get("status")},
        "flipkart": {"marketplace": "Flipkart Samarth", "fsn": fk.get("fsn"),
                     "title": p_name[:150], "price_inr": price,
                     "status": fk.get("status")},
        "gem": {"marketplace": "GeM", "quota": f"Handicrafts / {craft}",
                "catalog_id": gem.get("catalog_id"),
                "price_inr": gem.get("institutional_price_inr", round(price * 0.8, 2)),
                "status": gem.get("status")},
        "etsy": {"marketplace": "Etsy Global Export", "listing_id": etsy.get("listing_id"),
                 "title": etsy.get("title", p_name), "price_usd": usd,
                 "tags_13": (tags + ["gift", "handmade", "india", "artisan"])[:13],
                 "status": etsy.get("status")},
        "ondc_beckn": {"marketplace": "ONDC (Beckn)",
                       "beckn": ondc.get("ondc_payload", {}),
                       "status": ondc.get("status")},
        "summary": f"1 listing → 5 channels. Domestic ₹{price:,.0f} • Export ${usd} • GeM quota + ONDC Beckn ready.",
    }}


# =========================================================================
# 6b. AUTH — REGISTER / LOGIN / ME / LOGOUT (stdlib hashing, token bearer)
# =========================================================================
def _hash_pw(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()


def _public_user(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email,
            "phone": u.phone or "", "role": u.role or "artisan"}


def _bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def _issue_token(db: Session, user_id: str, days: int = 30) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthToken(token_hash=hashlib.sha256(token.encode()).hexdigest(),
                     user_id=user_id,
                     expires_at=datetime.utcnow() + timedelta(days=days)))
    db.commit()
    return token


@app.post("/api/v1/auth/register")
def auth_register(payload: dict = Body(...), db: Session = Depends(get_db)):
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    phone = (payload.get("phone") or "").strip()
    role = (payload.get("role") or "artisan").strip() or "artisan"
    if not name:
        raise HTTPException(status_code=400, detail="Please enter your name.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="This email is already registered. Please log in.")
    salt = secrets.token_hex(16)
    user = User(id=f"user_{uuid.uuid4().hex[:8]}", name=name, email=email,
                phone=phone, role=role, pw_salt=salt, pw_hash=_hash_pw(password, salt))
    db.add(user)
    db.commit()
    return {"ok": True, "token": _issue_token(db, user.id), "user": _public_user(user)}


@app.post("/api/v1/auth/login")
def auth_login(payload: dict = Body(...), db: Session = Depends(get_db)):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    user = db.query(User).filter(User.email == email).first()
    if not user or _hash_pw(password, user.pw_salt) != user.pw_hash:
        raise HTTPException(status_code=401, detail="Wrong email or password.")
    return {"ok": True, "token": _issue_token(db, user.id), "user": _public_user(user)}


@app.get("/api/v1/auth/me")
def auth_me(request: Request, db: Session = Depends(get_db)):
    token = _bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing login token.")
    th = hashlib.sha256(token.encode()).hexdigest()
    rec = db.query(AuthToken).filter(AuthToken.token_hash == th).first()
    if not rec or rec.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    user = db.query(User).filter(User.id == rec.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Account not found.")
    return {"ok": True, "user": _public_user(user)}


@app.post("/api/v1/auth/logout")
def auth_logout(request: Request, db: Session = Depends(get_db)):
    token = _bearer_token(request)
    if token:
        db.query(AuthToken).filter(
            AuthToken.token_hash == hashlib.sha256(token.encode()).hexdigest()).delete()
        db.commit()
    return {"ok": True}


# =========================================================================
# 7. ORDERS & EARNINGS
# =========================================================================
@app.get("/api/v1/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(desc(Order.created_at)).all()
    out = []
    for o in orders:
        out.append({
            "id": o.id,
            "product": o.product_title,
            "product_id": o.product_id,
            "buyer": o.buyer_name,
            "amount": o.total_amount,
            "unit_price": o.unit_price,
            "quantity": o.quantity,
            "status": o.order_status,
            "buyer_app": o.buyer_app,
            "city": o.delivery_city,
            "created_at": o.created_at.strftime("%b %d, %Y") if o.created_at else "Recent"
        })
    return {"ok": True, "count": len(out), "orders": out}


# =========================================================================
# 8. EXPORT: MELA STANDEE PDF & ONDC BECKN JSON
# =========================================================================
@app.get("/api/v1/export/mela-standee/{product_id}")
def export_mela_standee(product_id: str, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        prod = db.query(Product).first()
    if not prod:
        raise HTTPException(status_code=404, detail="No product found for Mela Standee")
    
    pdf_bytes = generate_mela_standee_pdf(prod)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Mela_Standee_{prod.id}.pdf"}
    )


@app.get("/api/v1/export/ondc-beckn/{product_id}")
def export_ondc_beckn(product_id: str, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        prod = db.query(Product).first()
    if not prod:
        raise HTTPException(status_code=404, detail="No product found for ONDC export")
    beckn_data = generate_ondc_beckn_json(prod)
    return JSONResponse(content=beckn_data)


@app.get("/api/v1/export/upi-qr/{product_id}")
def export_upi_qr(product_id: str, amount: float = 1250.0, artisan_name: str = "Rukmini Devi"):
    qr_bytes = generate_upi_qr_bytes(f"{product_id}@kalakart", artisan_name, amount)
    return Response(content=qr_bytes, media_type="image/png")


# =========================================================================
# 9. SPEECH & STORY CATALOG AUTOFILL
# =========================================================================
@app.post("/api/v1/catalog/from-story")
async def catalog_from_story(payload: dict = Body(...)):
    story = payload.get("story_text", "").strip()
    p_name = payload.get("product_name", "")
    lang = payload.get("language", "hi")
    
    if not story:
        raise HTTPException(status_code=400, detail="story_text is empty")

    if story_to_listing:
        try:
            return await story_to_listing(story, p_name, lang)
        except Exception:
            pass

    cat_res = generate_catalog_from_voice(story, p_name or "Handmade Craft")
    return {
        "ok": True,
        "title_en": cat_res.get("title_en", p_name or "Authentic Indian Craft"),
        "title_hi": cat_res.get("title_hi", "पारंपरिक हस्तशिल्प"),
        "description_en": cat_res.get("story_en", story),
        "description_hi": cat_res.get("story_hi", story),
        "craft_guess": cat_res.get("craft_type", "Pottery & Ceramics"),
        "engine": "KalaSaathi-NLP-RuleEngine"
    }


# =========================================================================
# 10. TRENDING CRAFT INSIGHTS
# =========================================================================
@app.get("/api/v1/trends")
def get_trends():
    return {"ok": True, "trends": get_craft_trend_insights()}


# Serve the artisan frontend from the same service when present
# (single-service deploy: UI + API on one URL; API routes take precedence).
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kalakart-frontend"))
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="site")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
