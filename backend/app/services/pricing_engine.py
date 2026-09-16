from app.ml.pricing_predictor import predict_fair_pricing, evaluate_bargaining_shield

def calculate_fair_pricing(
    material_cost=400.0,
    labor_hours=8.0,
    craft_type: str = "Pottery",
    material: str = "Clay"
) -> dict:
    """
    Delegates pricing calculations to the trained Random Forest regressor.
    """
    # Gracefully handle string/number swapped args
    if isinstance(material_cost, str):
        try:
            m_cost = float(labor_hours)
            l_hrs = float(craft_type) if not isinstance(craft_type, str) else 8.0
            c_type = material_cost
            material_cost, labor_hours, craft_type = m_cost, l_hrs, c_type
        except Exception:
            material_cost = 400.0
            labor_hours = 8.0

    return predict_fair_pricing(
        category=craft_type,
        material=material,
        material_cost=float(material_cost),
        labor_hours=float(labor_hours)
    )

def match_b2b_buyers(craft_type: str, price: float) -> list:
    all_buyers = [
        {"buyer_name": "FabIndia Sustainable Sourcing Desk", "category": "Handloom Saree", "demand_quantity": 100, "confidence_score": 96},
        {"buyer_name": "FabIndia Sustainable Sourcing Desk", "category": "Embroidered Cloth", "demand_quantity": 80, "confidence_score": 94},
        {"buyer_name": "Central Cottage Industries Emporium", "category": "Pottery", "demand_quantity": 120, "confidence_score": 93},
        {"buyer_name": "Khurja Potteries Collective", "category": "Terracotta", "demand_quantity": 150, "confidence_score": 95},
        {"buyer_name": "Tribes India Regional Procurement Hub", "category": "Metal Craft", "demand_quantity": 50, "confidence_score": 96},
        {"buyer_name": "Dastkar Craft Heritage Network", "category": "Wooden Craft", "demand_quantity": 60, "confidence_score": 92},
        {"buyer_name": "North East Handicrafts Corp (NEHHDC)", "category": "Bamboo Basket", "demand_quantity": 200, "confidence_score": 95},
        {"buyer_name": "Assam State Co-operative Emporium", "category": "Cane Furniture", "demand_quantity": 40, "confidence_score": 91},
        {"buyer_name": "National Jute Board Export Desk", "category": "Jute Bag", "demand_quantity": 300, "confidence_score": 97},
        {"buyer_name": "Amrapali Heritage Jewellery Guild", "category": "Handmade Jewellery", "demand_quantity": 75, "confidence_score": 94},
    ]
    matches = [b for b in all_buyers if craft_type.lower() in b["category"].lower() or b["category"].lower() in craft_type.lower()]
    if not matches:
        matches = [all_buyers[2]]
    return matches

def evaluate_bargaining_offer(
    material_cost: float,
    labor_hours: float,
    offered_price: float,
    craft_type: str = "Pottery",
    material: str = "Clay"
) -> dict:
    return evaluate_bargaining_shield(
        material_cost=float(material_cost),
        labor_hours=float(labor_hours),
        offered_price=float(offered_price),
        craft_type=craft_type,
        material=material
    )
