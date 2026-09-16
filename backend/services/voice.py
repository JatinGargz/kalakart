"""VOICE CATALOG — multilingual listing + Shilpi assistant (Groq Llama-3 optional, gTTS optional)."""
from __future__ import annotations
import base64
import io
import os

try:
    from gtts import gTTS
    HAS_GTTS = True
except Exception:
    HAS_GTTS = False

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

KB = {
    "price": ("Pricing: total=(material + hours×₹80 wage)×(1+12% overhead). "
              "Floor = total×1.10, Suggested = total×1.25. Never sell below floor — "
              "that is your dignity wage. / दाम: लागत पर 25% मुनाफा रखें, फ्लोर से नीचे कभी न बेचें।"),
    "vishwakarma": ("PM Vishwakarma: 18 traditional trades, ₹15,000 toolkit e-voucher, "
                    "₹1–2L loan at 5%, skill stipend ₹500/day. Apply at pmvishwakarma.gov.in via CSC. "
                    "/ पीएम विश्वकर्मा में टूलकिट + सस्ता लोन मिलता है।"),
    "gem": ("GeM portal: register as seller with Udyam + PAN, list under Handicrafts quota, "
            "MoSJE seal boosts trust. Payments in ~10 days. / GeM पर सरकारी खरीदार सीधे ऑर्डर देते हैं।"),
    "ondc": ("ONDC + Beckn: one listing reaches many buyer apps (Paytm, Pincode). "
             "Keep catalogue with clear images + GST invoice. / ONDC से कई ऐप्स पर बिक्री।"),
    "etsy": ("Etsy: price in USD (₹/83), charge $12–25 shipping, use 13 tags like 'banarasi silk saree handmade'."),
    "shipping": ("Fragile crafts: double-box, 2-inch cushioning, 'FRAGILE' + 'THIS SIDE UP'. "
                 "Delhivery/India Post for domestic, DHL for export. Insure above ₹5,000."),
    "order": ("Orders: ship pending orders within 48 hrs to protect SLA.Confirm → Pack → Ship → Share tracking."),
}

CRAFT_PRESETS = {
    "banarasi": {"craft": "Banarasi Silk", "material": "Silk, Zari",
                 "location": "Varanasi, UP", "hours": 40, "cost": 3500},
    "pottery": {"craft": "Jaipur Blue Pottery", "material": "Quartz, Glass, Clay",
                "location": "Jaipur, Rajasthan", "hours": 8, "cost": 400},
    "dokra": {"craft": "Bastar Dokra", "material": "Brass, Clay, Wax",
              "location": "Bastar, Chhattisgarh", "hours": 16, "cost": 900},
}


def detect_lang(text: str) -> str:
    if any("\u0900" <= ch <= "\u097f" for ch in text):
        return "hi"
    return "en"


def local_answer(query: str) -> tuple[str, str]:
    q = query.lower()
    if any(k in q for k in ["price", "dam", "दाम", "bargain", "भाव", "cost"]):
        return KB["price"], "pricing"
    if "vishwakarma" in q or "योजना" in q or "scheme" in q or "sarkar" in q:
        return KB["vishwakarma"], "scheme"
    if "gem" in q:
        return KB["gem"], "gem"
    if "ondc" in q or "beckn" in q:
        return KB["ondc"], "ondc"
    if "etsy" in q or "dollar" in q or "export" in q:
        return KB["etsy"], "export"
    if "ship" in q or "pack" in q or "order" in q or "ऑर्डर" in q:
        return KB["shipping"], "logistics"
    if any(k in q for k in ["namaste", "नमस्ते", "hello", "hi "]):
        return ("नमस्ते! मैं शिल्प सखी हूँ — दाम, सरकारी योजना, GeM/ONDC, या ऑर्डर — क्या पूछना है? "
                "Hello! I am Shilpi — ask me pricing, schemes, or orders."), "greeting"
    return (KB["price"] + " " + KB["vishwakarma"], "general")


async def groq_answer(query: str, lang: str) -> str | None:
    """Use Groq Llama-3 if GROQ_API_KEY is set, else None → local fallback."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    try:
        import httpx
        sys = ("You are Shilp Sakhi, a warm Hindi/English voice assistant for Indian artisans. "
               "Answer briefly (≤90 words), mix Hindi+English, always protect artisan wage floor. "
               f"User language: {lang}.")
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post("https://api.groq.com/openai/v1/chat/completions",
                             headers={"Authorization": f"Bearer {key}"},
                             json={"model": GROQ_MODEL, "temperature": 0.4, "max_tokens": 300,
                                   "messages": [{"role": "system", "content": sys},
                                                {"role": "user", "content": query}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def tts_base64(text: str, lang: str) -> str | None:
    if not HAS_GTTS:
        return None
    try:
        buf = io.BytesIO()
        gTTS(text=text[:450], lang="hi" if lang == "hi" else "en",
             tld="co.in").write_to_fp(buf)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def build_listing(product_name: str, craft_type: str, material: str,
                  location: str, story_text: str, lang: str = "hi") -> dict:
    title_en = f"Handmade {product_name} — Authentic {craft_type} from {location}"
    title_hi = f"हस्तनिर्मित {product_name} — असली {craft_type}, {location}"
    story = story_text.strip() or f"Made with love by a master artisan of {location}."
    desc_en = (f"{title_en}. {story} Eco-friendly, traditional technique, "
               "MoSJE authenticity seal included. Supports artisan livelihood directly.")
    desc_hi = (f"{title_hi}। {story} पर्यावरण-अनुकूल, पारंपरिक तकनीक, "
               "MoSJE प्रामाणिकता सील सहित। सीधे कारीगर को लाभ।")
    tags = [craft_type.lower(), location.split(',')[0].lower().strip(),
            "handmade", "indian-craft", "eco-friendly", "mosje-verified",
            material.split(',')[0].lower().strip()]
    return {"title_en": title_en[:200], "title_hi": title_hi,
            "description_en": desc_en, "description_hi": desc_hi,
            "tags": tags, "language": lang}
