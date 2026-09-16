"""5-MARKETPLACE DISTRIBUTION — Amazon / Flipkart / GeM / Etsy / ONDC-Beckn."""
from __future__ import annotations
import hashlib
import re

INR_PER_USD = 83.0


def slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").upper()
    return s[:24] or "CRAFT"


def mock_asin(name: str) -> str:
    return "B0" + hashlib.md5(("asin" + name).encode()).hexdigest()[:8].upper()


def mock_fsn(name: str) -> str:
    return "FSN" + hashlib.md5(("fsn" + name).encode()).hexdigest()[:8].upper()


def publish_all(product_name: str, craft_type: str, price_inr: float,
                description: str, tags: list[str], location: str,
                image_url: str = "") -> dict:
    price_inr = float(price_inr)
    usd = round(price_inr / INR_PER_USD + 6, 2)  # + handling buffer
    bullets = [f"Authentic {craft_type} — handmade in {location}",
               "Eco-friendly materials, traditional technique",
               "MoSJE Seal of Authenticity included",
               "Direct-from-artisan — fair wage protected",
               (description[:180] + "…") if len(description) > 180 else description]
    return {
        "amazon_in": {
            "marketplace": "Amazon.in", "asin": mock_asin(product_name),
            "title": product_name[:200], "bullets": bullets,
            "price_inr": price_inr, "hsn": "9701 (handicrafts)",
            "status": "READY_TO_PUSH",
        },
        "flipkart": {
            "marketplace": "Flipkart", "fsn": mock_fsn(product_name),
            "title": product_name[:150], "vertical": "Home & Crafts",
            "price_inr": price_inr, "attributes": {"craft": craft_type, "origin": location},
            "status": "READY_TO_PUSH",
        },
        "gem": {
            "marketplace": "GeM (Govt e-Marketplace)",
            "quota": f"Handicrafts / {craft_type}",
            "price_inr": price_inr, "mosje_compliant": True,
            "udyam_required": True, "payment_terms": "T+10 days",
            "status": "READY_TO_PUSH",
        },
        "etsy": {
            "marketplace": "Etsy (Export)",
            "title": f"{product_name} | Handmade Indian {craft_type}",
            "price_usd": usd, "currency": "USD",
            "tags_13": (tags + ["gift", "boho", "vintage", "indian", "artisan"])[:13],
            "shipping_usd": 14.0, "status": "READY_TO_PUSH",
        },
        "ondc_beckn": {
            "marketplace": "ONDC (Beckn)",
            "beckn": {"context": {"domain": "retail", "action": "on_search"},
                      "message": {"catalog": {"name": product_name,
                                              "price": {"currency": "INR", "value": str(price_inr)},
                                              "tags": tags, "image": image_url or "processed-1080p.jpg"}}},
            "status": "READY_TO_PUSH",
        },
        "summary": f"1 listing → 5 channels. Domestic ₹{price_inr:,.0f} • Export ${usd} • GeM quota + ONDC Beckn ready.",
    }
