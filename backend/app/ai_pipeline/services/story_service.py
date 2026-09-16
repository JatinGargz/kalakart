"""
Artisan Story Generation - Person 4 AI Pipeline
Enhanced with fail-safe resilience: Uses Ollama when running, falls back to
authentic heritage storyteller when Ollama is offline.
"""

import json
import re
import httpx

from app.schemas.models import ArtisanStory, MultilingualStory, ExtractedProduct, SUPPORTED_LANGUAGES

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"

def _fallback_story(product: ExtractedProduct, language_code: str) -> str:
    name = product.product_name or "हस्तनिर्मित कलाकृति"
    mat = product.material or "प्राकृतिक सामग्री"
    cat = product.category or "शिल्पकला"

    if language_code == "hi":
        return f"यह {name} भारतीय कारीगरों की पीढ़ियों पुरानी कला परंपरा का जीवंत प्रतीक है। शुद्ध {mat} और प्रामाणिक हस्तकौशल से निर्मित, हर कृति स्थानीय संस्कृति और श्रम की गरिमा का सम्मान करती है।"
    else:
        return f"This {name} represents generations of authentic Indian artisan tradition. Handcrafted using genuine {mat}, every piece preserves indigenous techniques while delivering fair dignified wages to master creators."

def _call_model(product: ExtractedProduct, language_name: str, language_code: str) -> str:
    facts = product.model_dump(exclude={"raw_source_text", "needs_clarification"})
    facts_str = ", ".join(f"{k}: {v}" for k, v in facts.items() if v)
    if not facts_str:
        facts_str = "Handmade artisan craft"

    payload = {
        "model": MODEL_NAME,
        "system": "You are writing a short, warm product story for an artisan marketplace. Output valid JSON: {\"story\": \"...\"}",
        "prompt": f"Language: {language_name}\nKnown product facts: {facts_str}",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.5},
    }

    try:
        response = httpx.post(OLLAMA_URL, json=payload, timeout=5)
        if response.status_code == 200:
            raw = response.json().get("response", "")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = json.loads(re.sub(r"```json|```", "", raw).strip())
            story = data.get("story", "").strip()
            if story:
                return story
    except Exception as e:
        print(f"[story] Ollama unavailable ({e}), using heritage craft storyteller")

    return _fallback_story(product, language_code)

def generate_story(product: ExtractedProduct, languages: list[str]) -> MultilingualStory:
    stories = []
    for code in languages:
        language_name = SUPPORTED_LANGUAGES.get(code)
        if not language_name:
            continue
        story_text = _call_model(product, language_name, code)
        stories.append(ArtisanStory(story_text=story_text, language=code))

    return MultilingualStory(stories=stories)
