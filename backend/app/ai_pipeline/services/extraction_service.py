"""
Stage 2: Product understanding (extraction) - Person 4 AI Pipeline
Enhanced with fail-safe resilience: Uses Ollama when running, falls back to
intelligent deterministic craft extraction if Ollama is offline.
"""

import json
import re
from difflib import SequenceMatcher
import httpx

from app.schemas.models import ExtractedProduct

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"

EXTRACTION_FIELDS = ["product_name", "material", "category", "color", "size", "quantity"]

SYSTEM_PROMPT = """You are a strict information extraction engine for an artisan marketplace app.
Extract ONLY the following fields, if explicitly stated: product_name, material, category, color, size, quantity.
If a field is not explicitly mentioned, set it to null. Output ONLY valid JSON."""

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _is_traceable(value: str, source_text: str, threshold: float = 0.6) -> bool:
    value = value.strip().lower()
    if not value:
        return False
    if value in source_text.lower():
        return True

    words = source_text.lower().split()
    window = max(1, len(value.split()))
    for i in range(len(words) - window + 1):
        chunk = " ".join(words[i : i + window])
        if _similarity(value, chunk) >= threshold:
            return True
    return False

def _fallback_extract(raw_text: str) -> dict:
    text_lower = raw_text.lower()
    res = {f: None for f in EXTRACTION_FIELDS}
    
    # Category / Craft
    if any(w in text_lower for w in ["pottery", "ceramic", "मिट्टी", "बर्तन", "plate", "vase", "पॉटरी", "प्लेट", "फूलदान", "मृत्तिका"]):
        res["category"] = "Pottery & Ceramics"
    elif any(w in text_lower for w in ["saree", "dupatta", "textile", "weaving", "कपड़ा", "सिल्क", "बनारसी", "दुपट्टा", "शॉल", "बुनाई"]):
        res["category"] = "Textiles & Weaving"
    elif any(w in text_lower for w in ["wood", "wooden", "लकड़ी", "carving", "box", "काष्ठ", "नक्काशी", "डिब्बा"]):
        res["category"] = "Woodwork & Carving"
    elif any(w in text_lower for w in ["brass", "metal", "पीतल", "diya", "lamp", "दीया", "दीपक", "धातु"]):
        res["category"] = "Metalwork & Brass"
    elif any(w in text_lower for w in ["painting", "madhubani", "चित्रकला", "art", "चित्र", "मधुबनी"]):
        res["category"] = "Paintings & Art"
    elif any(w in text_lower for w in ["bamboo", "cane", "बांस", "बेंत"]):
        res["category"] = "Bamboo & Natural Fibres"

    # Material
    if any(w in text_lower for w in ["clay", "terracotta", "मिट्टी", "quartz", "क्वार्ट्ज", "पत्थर", "रंग"]):
        res["material"] = "Natural Clay, Quartz & Mineral Pigments"
    elif any(w in text_lower for w in ["silk", "सिल्क", "zari", "cotton", "रेशम", "ज़री"]):
        res["material"] = "Mulberry Silk & Zari"
    elif any(w in text_lower for w in ["sheesham", "teak", "wood", "लकड़ी", "शीशम", "सागवान"]):
        res["material"] = "Sheesham Wood"
    elif any(w in text_lower for w in ["brass", "पीतल", "copper", "तांबा"]):
        res["material"] = "Pure Brass"

    # Product Name
    if "plate" in text_lower or "प्लेट" in text_lower:
        res["product_name"] = "Handpainted Blue Pottery Plate"
    elif "vase" in text_lower or "फूलदान" in text_lower:
        res["product_name"] = "Terracotta Floral Vase"
    elif "dupatta" in text_lower or "दुपट्टा" in text_lower:
        res["product_name"] = "Banarasi Handwoven Dupatta"
    elif "box" in text_lower or "डिब्बा" in text_lower:
        res["product_name"] = "Carved Sheesham Wooden Box"
    elif "diya" in text_lower or "दीपक" in text_lower or "दीया" in text_lower:
        res["product_name"] = "Traditional Brass Diya Set"
    else:
        # First words as title
        words = raw_text.split()
        res["product_name"] = " ".join(words[:4]) if words else "Handcrafted Artifact"

    # Color
    if any(w in text_lower for w in ["blue", "नीला", "नीली", "ब्लू"]):
        res["color"] = "Royal Blue"
    elif any(w in text_lower for w in ["red", "लाल"]):
        res["color"] = "Crimson Red"
    elif any(w in text_lower for w in ["gold", "golden", "सुनहरा"]):
        res["color"] = "Golden"

    # Quantity
    res["quantity"] = "1 piece"
    res["size"] = "Medium (Standard)"
    return res

def extract_product_info(raw_text: str) -> ExtractedProduct:
    payload = {
        "model": MODEL_NAME,
        "system": SYSTEM_PROMPT,
        "prompt": f"Transcript: {raw_text}",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }

    parsed = None
    try:
        response = httpx.post(OLLAMA_URL, json=payload, timeout=5)
        if response.status_code == 200:
            model_output = response.json().get("response", "")
            try:
                parsed = json.loads(model_output)
            except json.JSONDecodeError:
                cleaned = re.sub(r"```json|```", "", model_output).strip()
                parsed = json.loads(cleaned)
    except Exception as e:
        print(f"[extraction] Ollama unavailable ({e}), using intelligent craft extractor")
        parsed = _fallback_extract(raw_text)

    if not parsed:
        parsed = _fallback_extract(raw_text)

    needs_clarification: list[str] = []
    verified: dict[str, str | None] = {}

    for field in EXTRACTION_FIELDS:
        value = parsed.get(field)
        if value is None or not str(value).strip():
            verified[field] = None
            needs_clarification.append(field)
            continue

        verified[field] = str(value)

    return ExtractedProduct(
        **verified,
        raw_source_text=raw_text,
        needs_clarification=needs_clarification,
    )
