"""Story → English + auto-filled title/description (Groq when keyed, offline mapper fallback)."""
from __future__ import annotations
import os
import re

# Hindi → English glossary for craft speech
GLOSSARY = [
    ("थाली", "plate"), ("थाल", "plate"), ("साड़ी", "saree"), ("दुपट्टा", "dupatta"),
    ("हाथी", "elephant"), ("दिया", "diya"), ("दीये", "diyas"), ("फूलदान", "vase"),
    ("वास", "vase"), ("पेंटिंग", "painting"), ("चित्र", "painting"),
    ("बक्सा", "box"), ("डिब्बा", "box"), ("कुशन", "cushion"), ("टोकरी", "basket"),
    ("मिट्टी", "clay"), ("रेशम", "silk"), ("पीतल", "brass"), ("लकड़ी", "wood"),
    ("कांच", "glass"), ("काँच", "glass"), ("नीली", "blue"), ("नीला", "blue"),
    ("सुनहरी", "golden"), ("चाँदी", "silver"), ("सोने", "gold"), ("ज़री", "zari"),
    ("हाथ से", "handmade"), ("हस्तनिर्मित", "handmade"), ("बुनाई", "weaving"),
    ("पेंट", "painted"), ("फूल-पत्ती", "floral"), ("मोर", "peacock"), ("मछली", "fish"),
    ("जयपुर", "Jaipur"), ("वाराणसी", "Varanasi"), ("बनारस", "Varanasi"),
    ("बस्तर", "Bastar"), ("कच्छ", "Kutch"), ("बिहार", "Bihar"),
    ("मुरादाबाद", "Moradabad"), ("सहारनपुर", "Saharanpur"), ("असम", "Assam"),
    ("राजस्थान", "Rajasthan"), ("गुजरात", "Gujarat"), ("छत्तीसगढ़", "Chhattisgarh"),
    ("घंटे", "hours"), ("कीमत", "price"), ("दाम", "price"),
]

# Romanized Hinglish (speech engines often return Latin script)
ROMAN = [
    ("thali", "plate"), ("thaal", "plate"), ("saree", "saree"), ("sari", "saree"),
    ("dupatta", "dupatta"), ("haathi", "elephant"), ("hathi", "elephant"),
    ("diya", "diya"), ("diye", "diyas"), ("phool", "flower"), ("patti", "leaf"),
    ("vase", "vase"), ("painting", "painting"), ("baksa", "box"), ("dibba", "box"),
    ("cushion", "cushion"), ("tokri", "basket"), ("mitti", "clay"),
    ("resham", "silk"), ("peetal", "brass"), ("lakdi", "wood"),
    ("neeli", "blue"), ("neela", "blue"), ("sunahri", "golden"),
    ("chandi", "silver"), ("sone", "gold"), ("zari", "zari"),
    ("hath se", "handmade"), ("haath se", "handmade"), ("bunai", "weaving"),
    ("phool-patti", "floral"), ("mor", "peacock"), ("machli", "fish"),
    ("jaipur", "Jaipur"), ("varanasi", "Varanasi"), ("banaras", "Varanasi"),
    ("bastar", "Bastar"), ("kutch", "Kutch"), ("bihar", "Bihar"),
    ("moradabad", "Moradabad"), ("saharanpur", "Saharanpur"), ("assam", "Assam"),
    ("rajasthan", "Rajasthan"), ("gujarat", "Gujarat"),
]

PRODUCT_HINTS = [
    ("plate", "Plate"), ("saree", "Saree"), ("dupatta", "Dupatta"),
    ("elephant", "Elephant"), ("diya", "Diya Set"), ("vase", "Vase"),
    ("painting", "Painting"), ("box", "Box"), ("cushion", "Cushion"),
    ("basket", "Basket"),
]
CRAFT_HINTS = [
    ("blue", "Jaipur Blue Pottery"), ("zari", "Banarasi Silk"), ("silk", "Banarasi Silk"),
    ("dokra", "Bastar Dokra"), ("brass", "Metalwork"), ("clay", "Pottery & Ceramics"),
    ("terracotta", "Pottery & Ceramics"), ("wood", "Woodwork"), ("carv", "Woodwork"),
    ("embroider", "Textiles"), ("weav", "Textiles"), ("loom", "Textiles"),
    ("mirror", "Textiles"), ("paint", "Paintings"), ("madhubani", "Paintings"),
]


def gloss_to_english(text: str) -> str:
    out = text
    for hi, en in GLOSSARY:
        out = out.replace(hi, en)
    low = out.lower()
    for ro, en in ROMAN:
        low = re.sub(r"\b" + re.escape(ro) + r"\b", en, low)
    out = low
    # strip leftover Devanagari tokens we don't know, keep Latin + numbers
    out = re.sub(r"[\u0900-\u097F]+", "", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" ,।.-")
    return out


def guess_fields(story_en: str, product_name: str = "") -> tuple[str, str]:
    low = (story_en + " " + product_name).lower()
    product = ""
    for key, label in PRODUCT_HINTS:
        if key in low:
            product = label
            break
    craft = ""
    for key, label in CRAFT_HINTS:
        if key in low:
            craft = label
            break
    return product or "Craft", craft or "Handmade Craft"


async def groq_extract(story: str) -> dict | None:
    """Use Groq for real translation + field extraction. None on any failure."""
    key = os.getenv("GROQ_API_KEY")
    if not key or not story.strip():
        return None
    try:
        import httpx
        sys = ("You help Indian artisans. Given the artisan's spoken story (Hindi ok), "
               "reply ONLY as compact JSON: {\"story_en\": \"<english translation, 1-2 lines>\", "
               "\"title_en\": \"<product title <= 12 words>\", "
               "\"description_en\": \"<buyer-facing 1 line>\", "
               "\"craft\": \"<craft type>\", \"material\": \"<main material>\"}. No other text.")
        async with httpx.AsyncClient(timeout=25) as c:
            r = await c.post("https://api.groq.com/openai/v1/chat/completions",
                             headers={"Authorization": f"Bearer {key}"},
                             json={"model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                                   "temperature": 0.2, "max_tokens": 300,
                                   "messages": [{"role": "system", "content": sys},
                                                {"role": "user", "content": story}]})
            r.raise_for_status()
            import json as _json
            txt = r.json()["choices"][0]["message"]["content"].strip()
            txt = re.sub(r"^```json|```$", "", txt).strip()
            d = _json.loads(txt)
            if "title_en" in d and "story_en" in d:
                return d
    except Exception:
        return None
    return None


async def story_to_listing(story: str, product_name: str = "", language: str | None = None) -> dict:
    from services.voice import detect_lang
    lang = language or detect_lang(story)
    ai = await groq_extract(story)
    if ai:
        return {"ok": True, "lang": lang, "engine": "groq-llama-3",
                "story_en": ai.get("story_en", ""),
                "title_en": ai.get("title_en", product_name or "Handmade Craft")[:120],
                "description_en": ai.get("description_en", "")[:400],
                "craft_guess": ai.get("craft", ""),
                "material_guess": ai.get("material", "")}
    story_en = gloss_to_english(story) if lang == "hi" else story.strip()
    product, craft = guess_fields(story_en, product_name)
    base = product_name.strip() or f"Handmade {product}"
    title = base if len(base) <= 90 else base[:90]
    if craft not in title:
        title = f"{title} — {craft}"
    desc_bits = [p for p in [story_en, f"Authentic {craft}, handmade in India."] if p]
    return {"ok": True, "lang": lang, "engine": "offline-glossary",
            "story_en": story_en[:400],
            "title_en": title[:120],
            "description_en": " ".join(desc_bits)[:400],
            "craft_guess": craft, "material_guess": ""}
