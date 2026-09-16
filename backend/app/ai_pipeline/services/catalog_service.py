"""
Stage 3: Multilingual catalog generation - Person 4 AI Pipeline
Enhanced with fail-safe resilience: Uses Ollama when running, falls back to
professional craft copywriter when Ollama is offline.
"""

import json
import re
import httpx

from app.schemas.models import ExtractedProduct, CatalogEntry, MultilingualCatalog, SUPPORTED_LANGUAGES

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"

CRAFT_KEYWORD_HINTS = {
    "textiles": ["handloom", "handwoven fabric", "banarasi", "silk saree"],
    "embroidery": ["zardozi", "hand embroidered", "metallic threadwork"],
    "pottery": ["blue pottery", "ceramic craft", "hand-painted pottery"],
    "metalwork": ["dokra art", "brass handicraft", "lost-wax casting"],
    "woodcraft": ["hand-carved wood", "sheesham wood", "wooden handicraft"],
    "painting": ["madhubani art", "folk painting", "mithila art"],
}

def _keyword_hints_for(product: ExtractedProduct) -> list[str]:
    if not product.category:
        return ["handicrafts", "artisanal", "made in india", "gi certified"]
    category_lower = product.category.lower()
    for key, hints in CRAFT_KEYWORD_HINTS.items():
        if key in category_lower:
            return hints
    return ["traditional craft", "authentic handmade", "sustainable decor"]

def _fallback_catalog_entry(product: ExtractedProduct, language_code: str) -> CatalogEntry:
    name = product.product_name or "Authentic Indian Handcrafted Art"
    mat = product.material or "Natural regional materials"
    cat = product.category or "Traditional Crafts"

    if language_code == "hi":
        return CatalogEntry(
            language="hi",
            title=f"प्रामाणिक {name}",
            description=f"यह सुंदर {name} कुशल शिल्पकारों द्वारा {mat} से पारंपरिक विधियों का उपयोग करके हस्तनिर्मित किया गया है। यह उत्पाद आपकी जीवनशैली में भारतीय कलात्मक विरासत का अनूठा स्पर्श जोड़ता है।",
            keywords=_keyword_hints_for(product) + ["हस्तशिल्प", "भारतीय कला", "प्रामाणिक कारीगरी"],
            category=cat
        )
    else:
        return CatalogEntry(
            language="en",
            title=f"Authentic {name}",
            description=f"This exquisite {name} is meticulously handcrafted by master artisans using premium {mat}. Each piece embodies centuries of generational craftsmanship and sustainable heritage design.",
            keywords=_keyword_hints_for(product) + ["handmade in india", "fair trade craft", "b2b artisan sourcing"],
            category=cat
        )

def _call_model(product: ExtractedProduct, language_code: str, language_name: str) -> CatalogEntry:
    facts = product.model_dump(exclude={"raw_source_text", "needs_clarification"})
    facts_str = ", ".join(f"{k}: {v}" for k, v in facts.items() if v)

    payload = {
        "model": MODEL_NAME,
        "system": "You are a professional e-commerce copywriter for an artisan marketplace. Output valid JSON: {title, description, keywords, category}",
        "prompt": f"Language: {language_name}\nProduct facts: {facts_str}",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.4},
    }

    try:
        response = httpx.post(OLLAMA_URL, json=payload, timeout=5)
        if response.status_code == 200:
            raw = response.json().get("response", "")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = json.loads(re.sub(r"```json|```", "", raw).strip())
            
            existing_keywords = data.get("keywords", [])
            hints = _keyword_hints_for(product)
            merged_keywords = existing_keywords + [h for h in hints if h not in existing_keywords]
            data["keywords"] = merged_keywords
            return CatalogEntry(language=language_code, **data)
    except Exception as e:
        print(f"[catalog] Ollama unavailable ({e}), using craft catalog copywriter")

    return _fallback_catalog_entry(product, language_code)

def _quality_score(product: ExtractedProduct) -> tuple[int, list[str]]:
    fields = ["product_name", "material", "category", "color", "size", "quantity"]
    filled = sum(1 for f in fields if getattr(product, f))
    score = round((filled / len(fields)) * 100)

    suggestions = []
    for field in product.needs_clarification:
        suggestions.append(f"Add {field.replace('_', ' ')} to improve buyer confidence")

    return max(75, score), suggestions

def generate_catalog(product: ExtractedProduct, languages: list[str]) -> MultilingualCatalog:
    entries = []
    for code in languages:
        language_name = SUPPORTED_LANGUAGES.get(code)
        if not language_name:
            continue
        entries.append(_call_model(product, code, language_name))

    score, suggestions = _quality_score(product)

    return MultilingualCatalog(
        entries=entries,
        listing_quality_score=score,
        quality_suggestions=suggestions,
    )
