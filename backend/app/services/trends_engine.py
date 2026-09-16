"""
KalaKart (SHILP AI) - Craft Trends & Demand Intelligence Engine ("शिल्प रुझान")
Provides category-specific market trend recommendations, motif intelligence, 
color palettes, and festival demand signals for rural artisans.
"""

from typing import Dict, Any, List

CRAFT_TRENDS_DATABASE: Dict[str, Dict[str, Any]] = {
    "textiles": {
        "craft_category": "textiles",
        "craft_name_hi": "हथकरघा एवं वस्त्र (Handloom & Weaving)",
        "craft_name_en": "Handloom & Textiles",
        "demand_index": 94,
        "surge_badge": "+88% Festive Surge",
        "primary_season": "Navratri, Diwali & Autumn Wedding Season 2026",
        "trending_motifs": [
            {
                "title": "Zari Lotus & Peacock Weaves (कमल और मोर की ज़री)",
                "growth": "+94%",
                "insight": "High demand in bridal Banarasi sarees and dupattas on Amazon Karigar."
            },
            {
                "title": "Indigo Natural Dye Geometrics (नील अजरख प्रिंट)",
                "growth": "+82%",
                "insight": "Trending heavily with urban millennial buyers on ONDC & Instagram shops."
            },
            {
                "title": "Minimalist Pastel Borders (हल्के पेस्टल बॉर्डर)",
                "growth": "+71%",
                "insight": "Strong export demand in Europe and USA via Etsy."
            }
        ],
        "trending_colors": [
            {"name": "Royal Indigo", "hex": "#1E3A8A"},
            {"name": "Marigold Rust", "hex": "#C54218"},
            {"name": "Mustard Saffron", "hex": "#D97706"},
            {"name": "Sage Khadi Green", "hex": "#4D7C0F"}
        ],
        "price_sweet_spot": "₹ 1,500 – ₹ 2,800",
        "fastest_clearing_item": "Pure Silk Dupattas & Hand-Block Stoles",
        "actionable_advice_hi": "इस महीने कॉटन और सिल्क दुपट्टे में गोल्ड ज़री बॉर्डर और नैचुरल इंडिगो रंग की सबसे ज्यादा मांग है। अपने उत्पाद का दाम ₹1,600 से ₹2,400 के बीच रखें, बिक्री सबसे तेज़ होगी।",
        "actionable_advice_en": "Gold zari borders and natural indigo dyes are in highest demand. Keep your price point between ₹1,600 - ₹2,400 for fastest inventory turnaround.",
        "channel_signals": {
            "amazon": "Searches for 'Handmade Pure Silk Dupatta' surged 3.4x",
            "etsy": "Global orders for 'Natural Dye Scarves' up 140%",
            "ondc": "High bulk inquiry from urban lifestyle boutiques"
        }
    },
    "pottery": {
        "craft_category": "pottery",
        "craft_name_hi": "मिट्टी एवं ब्लू पॉटरी (Terracotta & Pottery)",
        "craft_name_en": "Terracotta & Blue Pottery",
        "demand_index": 91,
        "surge_badge": "+96% Festival Pre-Orders",
        "primary_season": "Diwali Lighting & Eco-Friendly Home Decor",
        "trending_motifs": [
            {
                "title": "Matte Terracotta Handi Sets (टेराकोटा कुकिंग हांडी)",
                "growth": "+110%",
                "insight": "Health-conscious urban kitchens driving huge direct-to-consumer demand."
            },
            {
                "title": "Geometric Cobalt Floral Vases (जयपुर ब्लू पॉटरी फूलदान)",
                "growth": "+85%",
                "insight": "High gifting volume on ONDC & corporate bulk orders for festive hampers."
            },
            {
                "title": "Perforated Shadow Diya Lamps (जालीदार दिया लैंप)",
                "growth": "+125%",
                "insight": "Fastest-selling Diwali decor item across tier-1 cities."
            }
        ],
        "trending_colors": [
            {"name": "Cobalt Blue", "hex": "#1E40AF"},
            {"name": "Baked Terracotta", "hex": "#B45309"},
            {"name": "Turquoise Glaze", "hex": "#0D9488"},
            {"name": "Earthy Sand", "hex": "#78350F"}
        ],
        "price_sweet_spot": "₹ 450 – ₹ 1,200",
        "fastest_clearing_item": "Set of 6 Designer Terracotta Diyas & Table Vases",
        "actionable_advice_hi": "दिवाली के लिए जालीदार मिट्टी के दीयों और नीले रंग के फूलदानों का अग्रिम ऑर्डर बढ़ रहा है। 4 या 6 के सेट बनाकर ₹600 से ₹900 में बेचें।",
        "actionable_advice_en": "Pre-orders surging for perforated terracotta diya sets and blue pottery vases. Bundle as sets of 4 or 6 priced at ₹600 - ₹900.",
        "channel_signals": {
            "amazon": "Searches for 'Eco Friendly Clay Diyas' up 4.2x",
            "etsy": "US orders for 'Blue Pottery Kitchenware' up 95%",
            "ondc": "Corporate Diwali gift hamper tenders active on GeM"
        }
    },
    "metalwork": {
        "craft_category": "metalwork",
        "craft_name_hi": "ढोकरा एवं पीतल शिल्प (Dhokra & Brass Craft)",
        "craft_name_en": "Dhokra & Brass Metalware",
        "demand_index": 87,
        "surge_badge": "+76% Export & Gifting Surge",
        "primary_season": "Heritage Corporate Gifting & Dhanteras",
        "trending_motifs": [
            {
                "title": "Antique Finish Urli Bowls (एंटीक पीतल की उरली)",
                "growth": "+89%",
                "insight": "Centerpiece for floating flowers and floating diyas in high demand."
            },
            {
                "title": "Tribal Dhokra Musicians & Elephants (ढोकरा आदिवासी आकृतियां)",
                "growth": "+74%",
                "insight": "Art collectors and export buyers looking for authenticated tribal art."
            },
            {
                "title": "Carved Brass Bell Wind Chimes (नक्काशीदार पीतल की घंटियां)",
                "growth": "+68%",
                "insight": "Popular balcony & temple decor on Amazon Karigar."
            }
        ],
        "trending_colors": [
            {"name": "Antique Brass", "hex": "#CA8A04"},
            {"name": "Verdigris Patina", "hex": "#0F766E"},
            {"name": "Warm Bronze", "hex": "#92400E"},
            {"name": "Matte Gold", "hex": "#EAB308"}
        ],
        "price_sweet_spot": "₹ 1,800 – ₹ 3,500",
        "fastest_clearing_item": "Peacock Engraved Brass Urli (10 to 12 inch)",
        "actionable_advice_hi": "धनतेरस और शादी के सीजन के लिए 10-इंच की एंटीक पीतल की उरली की सबसे तेज बिक्री हो रही है। इस पर नेचुरल एंटीक पॉलिश रखें।",
        "actionable_advice_en": "10-inch antique brass urli bowls with peacock motifs are top sellers. Highlight GI authenticity seal for premium pricing.",
        "channel_signals": {
            "amazon": "Top search: 'Brass Urli for Diwali decoration'",
            "etsy": "Collectors paying up to $75 for authentic Dhokra lost-wax casting",
            "ondc": "State emporium wholesale tenders open"
        }
    },
    "woodwork": {
        "craft_category": "woodwork",
        "craft_name_hi": "काष्ठ एवं पारंपरिक खिलौने (Woodwork & Toys)",
        "craft_name_en": "Woodwork & Heritage Toys",
        "demand_index": 85,
        "surge_badge": "+68% Non-Toxic Toy Demand",
        "primary_season": "Children's Gifting & Educational Decor",
        "trending_motifs": [
            {
                "title": "Channapatna Non-Toxic Stacking Toys (चन्नापटना लकड़ी के खिलौने)",
                "growth": "+95%",
                "insight": "Parents switching from plastic to natural vegetable-dyed wooden toys."
            },
            {
                "title": "Saharanpur Floral Carved Spice Boxes (नक्काशीदार मसाला दानी)",
                "growth": "+72%",
                "insight": "Modern kitchen organizers trending across urban metros."
            },
            {
                "title": "Handcrafted Wooden Cutlery Sets (शीशम लकड़ी के चम्मच सेट)",
                "growth": "+60%",
                "insight": "Eco-friendly cafes and zero-waste homes driving consistent demand."
            }
        ],
        "trending_colors": [
            {"name": "Natural Sheesham", "hex": "#78350F"},
            {"name": "Turmeric Yellow Dye", "hex": "#F59E0B"},
            {"name": "Crimson Lacquer", "hex": "#DC2626"},
            {"name": "Indigo Wood Stain", "hex": "#1E3A8A"}
        ],
        "price_sweet_spot": "₹ 550 – ₹ 1,450",
        "fastest_clearing_item": "5-Piece Non-Toxic Vegetable Dyed Toy Sets",
        "actionable_advice_hi": "सुरक्षित और नैचुरल रंग वाले लकड़ी के खिलौनों की मांग बहुत तेज़ी से बढ़ रही है। '100% नॉन-टॉक्सिक नेचुरल रंग' का टैग जरूर लगाएं।",
        "actionable_advice_en": "Huge demand for non-toxic vegetable dyed wooden toys. Label clearly with 'Child-Safe Natural Lacquer' to attract urban parents.",
        "channel_signals": {
            "amazon": "'Wooden toys for toddlers organic' search volume +180%",
            "etsy": "Global Montessori parent communities placing repeat orders",
            "ondc": "GeM pre-school supply tenders open for handloom & craft boards"
        }
    }
}

def get_craft_trend_insights(category: str = "textiles") -> Dict[str, Any]:
    cat = (category or "textiles").lower().strip()
    if cat not in CRAFT_TRENDS_DATABASE:
        for k in CRAFT_TRENDS_DATABASE:
            if k in cat:
                return CRAFT_TRENDS_DATABASE[k]
        return CRAFT_TRENDS_DATABASE["textiles"]
    return CRAFT_TRENDS_DATABASE[cat]

def get_all_available_categories() -> List[Dict[str, str]]:
    return [
        {"id": "textiles", "name_hi": "हथकरघा एवं वस्त्र", "name_en": "Handloom & Textiles", "icon": "fa-shirt"},
        {"id": "pottery", "name_hi": "मिट्टी एवं पॉटरी", "name_en": "Pottery & Terracotta", "icon": "fa-jar"},
        {"id": "metalwork", "name_hi": "ढोकरा एवं पीतल", "name_en": "Brass & Dhokra Metal", "icon": "fa-gem"},
        {"id": "woodwork", "name_hi": "काष्ठ एवं खिलौने", "name_en": "Woodwork & Toys", "icon": "fa-tree"}
    ]
