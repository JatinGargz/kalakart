import json
import os
import uuid
from gtts import gTTS


CRAFT_KNOWLEDGE = {
    "textiles": {
        "title_en": "Authentic Handcrafted Banarasi Silk Dupatta with Zari Border",
        "title_hi": "पारंपरिक ज़री बॉर्डर वाली हस्तनिर्मित बनारसी सिल्क दुपट्टा",
        "craft_type": "Banarasi Handloom Weaving",
        "material": "100% Pure Mulberry Silk",
        "story_en": "Hand-woven on traditional pit looms by Varanasi master weavers, preserving 500 years of handloom heritage.",
        "bullet_points": [
            "100% Handloom Certified Pure Silk",
            "Intricate golden zari floral motifs",
            "Direct procurement from MoSJE weaver cluster"
        ]
    },
    "metalwork": {
        "title_en": "Ancient Lost-Wax Cast Bastar Dokra Brass Diya",
        "title_hi": "प्राचीन लॉस्ट-वैक्स पद्धति से निर्मित बस्तर ढोकरा पीतल दीया",
        "craft_type": "Bastar Dokra Metal Casting",
        "material": "Bell Metal & Recycled Brass",
        "story_en": "Crafted by indigenous Bastar tribal artisans using a 4,000-year-old non-ferrous lost-wax metal casting technique.",
        "bullet_points": [
            "100% solid brass with rustic antique polish",
            "Hand-sculpted wax motif ensures each piece is unique",
            "Direct livelihood support for Chhattisgarh tribal artisans"
        ]
    },
    "pottery": {
        "title_en": "Handmade Jaipur Blue Pottery Ceramic Floral Vase",
        "title_hi": "हस्तनिर्मित जयपुर ब्लू पॉटरी सिरेमिक फूलदान",
        "craft_type": "Jaipur Blue Pottery",
        "material": "Quartz Stone Powder & Natural Cobalt Glaze",
        "story_en": "Crafted without clay using traditional Egyptian quartz paste and hand-painted with cobalt blue arabesque designs.",
        "bullet_points": [
            "Hand-painted traditional floral arabesque",
            "Lead-free eco-friendly quartz glaze",
            "GI-tagged craft from Jaipur artisan clusters"
        ]
    },
    "woodcraft": {
        "title_en": "Hand-Carved Saharanpur Sheesham Wood Trinket Box",
        "title_hi": "हस्तनिर्मित सहारनपुर शीशम की लकड़ी की नक्काशीदार डिब्बी",
        "craft_type": "Saharanpur Wood Carving",
        "material": "Seasoned Sheesham (Rosewood)",
        "story_en": "Carved by master artisans of Saharanpur showcasing delicate floral lattice jali work passed down through generations.",
        "bullet_points": [
            "Solid natural Sheesham wood with brass inlays",
            "Hand-buffed natural lacquer finish",
            "Fair wage certified woodcraft"
        ]
    }
}

def generate_catalog_from_voice(transcript: str, craft_category: str = "textiles") -> dict:
    category_key = craft_category.lower() if craft_category.lower() in CRAFT_KNOWLEDGE else "textiles"
    data = CRAFT_KNOWLEDGE[category_key].copy()
    
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            prompt = f"Extract facts from this voice transcript: '{transcript}'. Return JSON with title_en, title_hi, craft_type, material, story_en, bullet_points (array)."
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            parsed = json.loads(resp.choices[0].message.content)
            data.update(parsed)
        except Exception:
            pass

    return data

def generate_hindi_tts_audio(title_hi: str, price: float, prod_id: str, static_dir: str) -> str:
    try:
        price_num = float(price)
    except Exception:
        price_num = 2900.0
    text = f"Aapka {title_hi} safalta se catalog ho gaya hai. Tajveez daam {price_num:.0f} rupaye hai."
    filename = f"audio_{prod_id}.mp3"
    out_dir = os.path.join(static_dir, "audio")
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, filename)
    try:
        tts = gTTS(text=text, lang="hi", slow=False)
        tts.save(filepath)
        return f"/static/audio/{filename}"
    except Exception as e:
        return "/static/audio/fallback_sample.mp3"

def ask_shilpi_assistant(question: str, static_dir: str) -> dict:
    q = question.lower()
    
    if any(k in q for k in ["toolkit", "15000", "टूलकिट", "भत्ता", "पैसा"]):
        ans_hi = "पीएम विश्वकर्मा योजना के अंतर्गत आपको ₹15,000 का आधुनिक टूलकिट प्रोत्साहन मिलता है। इसके अलावा 5% ब्याज पर ₹1 लाख तक का बिना गारंटी का ऋण भी उपलब्ध है।"
        ans_en = "Under PM Vishwakarma, you receive a ₹15,000 digital e-voucher for modern toolkits, plus up to ₹1,00,000 collateral-free credit at 5% interest."
    elif any(k in q for k in ["mela", "surajkund", "stall", "मेला", "हाट", "प्रदर्शनी"]):
        ans_hi = "सूरजकुंड और दिल्ली हाट जैसे सरकारी मेलों में MoSJE और PM-DAKSH के तहत पंजीकृत कारीगरों को निःशुल्क स्टॉल आवंटित किए जाते हैं। अपने स्टॉल पर हमारा A4 स्टैंडी PDF जरूर लगाएं ताकि ग्राहक बाद में भी सालभर ऑर्डर कर सकें।"
        ans_en = "Under MoSJE and PM-DAKSH, certified artisans receive free or subsidized exhibition stalls at fairs like Surajkund Mela. Always display your A4 QR standee for year-round repeat orders."
    elif any(k in q for k in ["ondc", "paytm", "order", "ऑर्डर", "बिक्री", "ऑनलाइन"]):
        ans_hi = "आपका कैटलॉग ONDC नेटवर्क पर सक्रिय है। Paytm या PhonePe पर जब भी ग्राहक ऑर्डर करेगा, पैसा सीधे आपके बैंक खाते में बिना किसी बिचौलिये के पहुंचेगा।"
        ans_en = "Your products are broadcast on the ONDC open network. When buyers purchase via Paytm or PhonePe, payment is transferred directly to your bank account with zero intermediary commission."
    else:
        ans_hi = "शिल्प AI आपकी कला का संरक्षक है। अपनी मेहनत का उचित मूल्य लें, कम से कम ₹100 प्रति घंटा दिहाड़ी सुरक्षित रखें और अपनी हस्तकला का डिजिटल प्रमाण-पत्र हमेशा ग्राहकों को दिखाएं।"
        ans_en = "SHILP AI safeguards your traditional craftsmanship. Always ensure at least ₹100/hr wage floor and share your MoSJE authenticity certificate with buyers."

    filename = f"shilpi_{uuid.uuid4().hex[:8]}.mp3"
    filepath = os.path.join(static_dir, "audio", filename)
    audio_url = ""
    try:
        tts = gTTS(text=ans_hi, lang="hi", slow=False)
        tts.save(filepath)
        audio_url = f"/static/audio/{filename}"
    except Exception:
        audio_url = ""

    return {
        "question": question,
        "answer_hi": ans_hi,
        "answer_en": ans_en,
        "audio_url": audio_url
    }

