import os
import joblib
import pandas as pd
import numpy as np

# Resolve paths relative to this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, "artisan_price_model.pkl")
DATASET_PATH = os.path.join(CURRENT_DIR, "artisan_pricing_dataset.csv")

# Standard known categories and materials in the dataset
VALID_CATEGORIES = [
    "Bamboo Basket", "Cane Furniture", "Embroidered Cloth", "Handloom Saree",
    "Handmade Jewellery", "Jute Bag", "Metal Craft", "Pottery", "Terracotta", "Wooden Craft"
]

VALID_MATERIALS = [
    "Bamboo", "Beads", "Brass", "Cane", "Clay", "Cotton", "Jute", "Silk", "Terracotta", "Wood"
]

CATEGORY_ALIASES = {
    "textiles": "Handloom Saree",
    "textile": "Handloom Saree",
    "saree": "Handloom Saree",
    "cloth": "Embroidered Cloth",
    "embroidery": "Embroidered Cloth",
    "pottery": "Pottery",
    "ceramics": "Pottery",
    "terracotta": "Terracotta",
    "metalwork": "Metal Craft",
    "metal": "Metal Craft",
    "brass": "Metal Craft",
    "wood": "Wooden Craft",
    "woodcraft": "Wooden Craft",
    "woodwork": "Wooden Craft",
    "bamboo": "Bamboo Basket",
    "cane": "Cane Furniture",
    "jewellery": "Handmade Jewellery",
    "jewelry": "Handmade Jewellery",
    "jute": "Jute Bag",
}

MATERIAL_ALIASES = {
    "silk": "Silk",
    "cotton": "Cotton",
    "clay": "Clay",
    "terracotta": "Terracotta",
    "brass": "Brass",
    "wood": "Wood",
    "bamboo": "Bamboo",
    "cane": "Cane",
    "jute": "Jute",
    "beads": "Beads",
    "glass": "Beads",
    "metal": "Brass",
}

# Global singleton cache
_MODEL = None
_BENCHMARKS = None

def _load_model_and_dataset():
    global _MODEL, _BENCHMARKS
    if _MODEL is not None and _BENCHMARKS is not None:
        return _MODEL, _BENCHMARKS

    if os.path.exists(MODEL_PATH):
        _MODEL = joblib.load(MODEL_PATH)
    else:
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

    if os.path.exists(DATASET_PATH):
        df = pd.read_csv(DATASET_PATH)
        # Compute category-level median benchmarks
        benchmarks = {}
        for cat in df['category'].unique():
            cat_df = df[df['category'] == cat]
            benchmarks[cat] = {
                "default_material": cat_df['material'].mode()[0] if not cat_df['material'].empty else "Clay",
                "market_min": float(cat_df['market_min'].median()),
                "market_avg": float(cat_df['market_avg'].median()),
                "market_max": float(cat_df['market_max'].median()),
                "demand_score": float(cat_df['demand_score'].median()),
                "size": float(cat_df['size'].median()),
                "weight": float(cat_df['weight'].median()),
                "material_cost": float(cat_df['material_cost'].median()),
                "labour_cost": float(cat_df['labour_cost'].median()),
            }
        _BENCHMARKS = benchmarks
    else:
        _BENCHMARKS = {}

    return _MODEL, _BENCHMARKS

def normalize_category(cat: str) -> str:
    if not cat:
        return "Pottery"
    cat_lower = cat.strip().lower()
    if cat_lower in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[cat_lower]
    for valid in VALID_CATEGORIES:
        if valid.lower() in cat_lower or cat_lower in valid.lower():
            return valid
    return "Pottery"

def normalize_material(mat: str, category: str = "Pottery") -> str:
    if not mat:
        defaults = {
            "Handloom Saree": "Silk",
            "Embroidered Cloth": "Cotton",
            "Pottery": "Clay",
            "Terracotta": "Terracotta",
            "Metal Craft": "Brass",
            "Wooden Craft": "Wood",
            "Bamboo Basket": "Bamboo",
            "Cane Furniture": "Cane",
            "Handmade Jewellery": "Beads",
            "Jute Bag": "Jute"
        }
        return defaults.get(category, "Clay")
    mat_lower = mat.strip().lower()
    if mat_lower in MATERIAL_ALIASES:
        return MATERIAL_ALIASES[mat_lower]
    for valid in VALID_MATERIALS:
        if valid.lower() in mat_lower or mat_lower in valid.lower():
            return valid
    return "Clay"

def predict_fair_pricing(
    category: str = "Pottery",
    material: str = "Clay",
    material_cost: float = 400.0,
    labour_cost: float = None,
    labor_hours: float = 8.0,
    size: float = None,
    weight: float = None,
    demand_score: float = None
) -> dict:
    """
    Predicts fair price using the trained Random Forest model.
    Enforces the MoSJE skilled artisan wage floor (Rs 100/hour).
    """
    model, benchmarks = _load_model_and_dataset()

    norm_cat = normalize_category(category)
    norm_mat = normalize_material(material, norm_cat)

    cat_bench = benchmarks.get(norm_cat, {
        "market_min": 1200.0, "market_avg": 1600.0, "market_max": 2200.0,
        "demand_score": 0.70, "size": 30.0, "weight": 2.0, "material_cost": 400.0, "labour_cost": 500.0
    })

    # Skilled wage floor calculation
    SKILLED_HOURLY_WAGE = 100.0
    hours = float(labor_hours) if labor_hours else 8.0
    if labour_cost is None or labour_cost <= 0:
        labour_cost = round(hours * SKILLED_HOURLY_WAGE, 2)
    else:
        labour_cost = float(labour_cost)

    material_cost = float(material_cost) if material_cost and material_cost > 0 else cat_bench["material_cost"]
    size_val = float(size) if size and size > 0 else cat_bench["size"]
    weight_val = float(weight) if weight and weight > 0 else cat_bench["weight"]
    demand_val = float(demand_score) if demand_score is not None else cat_bench["demand_score"]

    # Market ranges based on benchmarks & cost inputs
    market_min = max(cat_bench["market_min"], (material_cost + labour_cost) * 1.15)
    market_avg = max(cat_bench["market_avg"], (material_cost + labour_cost) * 1.40)
    market_max = max(cat_bench["market_max"], (material_cost + labour_cost) * 1.80)

    # Build input DataFrame exactly matching model preprocessor
    row_dict = {
        "category": [norm_cat],
        "material": [norm_mat],
        "material_cost": [float(material_cost)],
        "labour_cost": [float(labour_cost)],
        "size": [float(size_val)],
        "weight": [float(weight_val)],
        "market_min": [float(market_min)],
        "market_avg": [float(market_avg)],
        "market_max": [float(market_max)],
        "demand_score": [float(demand_val)],
    }
    input_df = pd.DataFrame(row_dict)

    # Run Random Forest prediction
    raw_pred = float(model.predict(input_df)[0])

    # Minimum ethical wage floor (Packaging Rs 50 + Materials + Skilled Labor)
    packaging_cost = 50.0
    cost_floor = round(material_cost + labour_cost + packaging_cost, 2)

    # Fair retail price is at least cost floor + 25% craft margin
    retail_price = max(raw_pred, cost_floor * 1.25)
    # Round to nearest Rs 10 or Rs 50 for clean presentation
    retail_price = round(retail_price / 10.0) * 10.0

    # Wholesale / B2B price: 20% discount on retail or cost_floor * 1.18
    wholesale_price = round(max(cost_floor * 1.18, retail_price * 0.78) / 10.0) * 10.0

    profit_margin = retail_price - cost_floor
    profit_margin_pct = round((profit_margin / retail_price) * 100, 1) if retail_price > 0 else 0.0

    return {
        "category": norm_cat,
        "material": norm_mat,
        "material_cost": round(material_cost, 2),
        "labour_cost": round(labour_cost, 2),
        "labor_hours": hours,
        "size": round(size_val, 1),
        "weight": round(weight_val, 2),
        "demand_score": round(demand_val, 2),
        "cost_floor": cost_floor,
        "minimum_wage_floor": cost_floor,
        "guaranteed_labor_wage": labour_cost,
        "recommended_retail_price": retail_price,
        "suggested_selling_price": retail_price,
        "wholesale_b2b_price": wholesale_price,
        "profit_margin": round(profit_margin, 2),
        "profit_margin_percentage": profit_margin_pct,
        "model_version": "RandomForest-v1.0 (300 estimators)",
        "explanation": f"Based on trained ML valuation for {norm_cat} ({norm_mat}) with ₹{material_cost:.0f} raw materials, {hours:.0f} hours skilled craftsmanship (₹{labour_cost:.0f} living wage), and market demand index {demand_val:.2f}."
    }

def evaluate_bargaining_shield(
    material_cost: float,
    labor_hours: float,
    offered_price: float,
    craft_type: str = "Pottery",
    material: str = "Clay"
) -> dict:
    """
    Evaluates a buyer's offer using the Random Forest fair price and statutory wage floor.
    Generates actionable negotiation dialogues in Hindi and English.
    """
    pricing_info = predict_fair_pricing(
        category=craft_type,
        material=material,
        material_cost=material_cost,
        labor_hours=labor_hours
    )

    cost_floor = pricing_info["cost_floor"]
    suggested_price = pricing_info["recommended_retail_price"]

    packaging = 50.0
    effective_wage_pool = offered_price - material_cost - packaging
    effective_hourly_wage = max(0.0, effective_wage_pool / max(1.0, float(labor_hours)))
    SKILLED_HOURLY_WAGE = 100.0

    diff_from_suggested = offered_price - suggested_price
    diff_percent = round((diff_from_suggested / suggested_price) * 100)

    # Counter offer gives full wage floor + healthy artisan margin
    recommended_counter_offer = round(max(suggested_price * 0.90, cost_floor * 1.18) / 10.0) * 10.0

    if offered_price < cost_floor or effective_hourly_wage < SKILLED_HOURLY_WAGE * 0.75:
        status_key = "too_low"
        status_text = "Too Low"
        verdict = "EXPLOITATIVE_LOSS"
        badge_color = "red"
        advice = f"⚠️ You're underpriced. The offer fails to cover skilled artisan living wages. Counter at ₹{recommended_counter_offer:,.0f} or above."
        dialogue_hi = f"भैया, इस {pricing_info['category']} को बनाने में पूरे {labor_hours:.0f} घंटे की बारीक कारीगरी लगी है। ₹{offered_price:.0f} में हमारी ₹50 की भी दिहाड़ी नहीं बचती। सरकारी शिल्पकार मानकों के तहत हमारा न्यूनतम सम्मानजनक मूल्य ₹{recommended_counter_offer:,.0f} है।"
        dialogue_en = f"Sir, this authentic handcrafted piece requires {labor_hours:.0f} hours of master labor. At ₹{offered_price:.0f}, the effective wage drops to ₹{effective_hourly_wage:.0f}/hr (well below the MoSJE skilled floor of ₹100/hr). Our fair counter-offer is ₹{recommended_counter_offer:,.0f}."
    elif offered_price < suggested_price * 0.88:
        status_key = "tight"
        status_text = "Tight Margin"
        verdict = "TIGHT_MARGIN"
        badge_color = "amber"
        advice = f"⚡ Barely covers basic labor. Recommend counter-offering at ₹{recommended_counter_offer:,.0f} to protect your craft profit."
        dialogue_hi = f"नमस्ते जी! आपकी पेशकश समझ आई, लेकिन शुद्ध प्राकृतिक सामग्री और हाथ की बनावट के कारण हम इसे ₹{recommended_counter_offer:,.0f} से कम में नहीं दे सकते। यह आपके और हमारे दोनों के लिए श्रेष्ठ सौदा है।"
        dialogue_en = f"Thank you for the offer. Considering the premium natural materials and handmade quality, our best possible counter-offer is ₹{recommended_counter_offer:,.0f} to ensure sustainable craft production."
    else:
        status_key = "great"
        status_text = "Fair / High"
        verdict = "FAIR_PROFITABLE"
        badge_color = "green"
        advice = "✓ Safe and profitable to accept! Honors your master craft and full living wage."
        dialogue_hi = f"जी बहुत-बहुत धन्यवाद! यह सौदा बिल्कुल उचित है। ₹{offered_price:.0f} में हम आपका आर्डर तुरंत तैयार करना शुरू कर सकते हैं।"
        dialogue_en = f"Thank you! The offer of ₹{offered_price:.0f} is fair and accepted. We will dispatch your handcrafted order promptly."

    return {
        "offered_price": offered_price,
        "suggested_price": suggested_price,
        "recommended_retail_price": suggested_price,
        "wholesale_b2b_price": pricing_info["wholesale_b2b_price"],
        "cost_floor": cost_floor,
        "minimum_wage_floor": cost_floor,
        "material_cost": pricing_info["material_cost"],
        "labor_wage": pricing_info["guaranteed_labor_wage"],
        "labor_hours": labor_hours,
        "effective_hourly_wage": round(effective_hourly_wage, 1),
        "standard_hourly_wage": SKILLED_HOURLY_WAGE,
        "diff_percent": diff_percent,
        "status_key": status_key,
        "status_text": status_text,
        "verdict": verdict,
        "badge_color": badge_color,
        "advice": advice,
        "recommended_counter_offer": recommended_counter_offer,
        "dialogue_hi": dialogue_hi,
        "dialogue_en": dialogue_en,
        "artisan_dialogue_hindi": dialogue_hi,
        "artisan_dialogue_en": dialogue_en,
        "price_breakdown": {
            "material_cost": pricing_info["material_cost"],
            "production_effort": pricing_info["guaranteed_labor_wage"],
            "packaging_logistics": packaging,
            "craft_profit_margin": pricing_info["profit_margin"],
            "margin_percentage": pricing_info["profit_margin_percentage"]
        }
    }
