"""
Artisan Chatbot Service - Person 4 AI Pipeline
Enhanced with fail-safe resilience: Uses Ollama when running, falls back to
knowledgeable empathetic Kala Saathi assistant when Ollama is offline.
"""

import json
import re
import httpx

from app.schemas.models import ChatMessage, ChatRequest, ChatResponse

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.1:8b"

def _detect_reply_language(user_message: str, requested: str | None) -> str:
    if requested:
        return requested
    if re.search(r"[\u0900-\u097F]", user_message):
        return "hi"
    return "en"

def _fallback_reply(message: str, language: str) -> str:
    msg_lower = message.lower()
    if language == "hi":
        if any(w in msg_lower for w in ["price", "कीमत", "दाम", "रुपए", "सौदा"]):
            return "कलाकार्ट के 'सौदा रक्षक' के अनुसार: कच्ची सामग्री + कारीगरी के घंटे (कम से कम ₹100/घंटा) + 35% लाभ जोड़कर कीमत तय करें। हमारा रैंडम फॉरेस्ट मॉडल आपकी न्यूनतम मजदूरी की गारंटी देता है।"
        elif any(w in msg_lower for w in ["scheme", "योजना", "विश्वकर्मा", "सरकार"]):
            return "प्रधानमंत्री विश्वकर्मा योजना के तहत शिल्पकारों को ₹15,000 की टूलकिट सहायता, 5% की रियायती ब्याज दर पर ₹3 लाख तक का बिना गारंटी ऋण और निःशुल्क राष्ट्रीय प्रमाणन मिलता है।"
        elif any(w in msg_lower for w in ["photo", "फोटो", "तस्वीर", "camera"]):
            return "सुबह की प्राकृतिक रोशनी में उत्पाद की 3 अलग-अलग कोणों से तस्वीरें लें। कलाकार्ट का AI बैकग्राउंड हटाकर आपकी फोटो को स्टूडियो क्वालिटी में बदल देगा।"
        else:
            return "नमस्ते! मैं आपकी कला साथी हूँ। मैं आपको सही कीमत तय करने, सरकारी योजनाओं का लाभ लेने, उत्पाद लिस्टिंग और ऑनलाइन बिक्री बढ़ाने में पूरी सहायता कर सकती हूँ। आप क्या जानना चाहते हैं?"
    else:
        if any(w in msg_lower for w in ["price", "pricing", "cost", "bargain"]):
            return "According to KalaKart Bargaining Shield: Add raw materials + skilled labor hours (min ₹100/hr) + 35% artisan profit margin. Our Random Forest ML model protects your fair living wage floor!"
        elif any(w in msg_lower for w in ["scheme", "government", "vishwakarma", "loan"]):
            return "Under PM Vishwakarma Yojana, registered artisans receive ₹15,000 modern toolkit incentives, collateral-free credit up to ₹3 Lakh at 5% interest, and official GI recognition."
        elif any(w in msg_lower for w in ["photo", "picture", "camera", "image"]):
            return "Photograph your craft in natural daylight against a plain background. KalaKart AI Studio automatically removes clutter and adds soft studio shadows for marketplace readiness."
        else:
            return "Hello! I am Kala Saathi, your digital business companion. I can assist you with ethical pricing, government artisan schemes, photo enhancement, and multi-channel selling via ONDC. How can I assist you today?"

def get_chat_reply(request: ChatRequest) -> ChatResponse:
    reply_language = _detect_reply_language(request.message, request.language)

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are Kala Saathi, a friendly helper for Indian artisans. Keep answers clear and encouraging."},
            {"role": "user", "content": request.message}
        ],
        "stream": False,
        "options": {"temperature": 0.6},
    }

    try:
        response = httpx.post(OLLAMA_URL, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            reply_text = data.get("message", {}).get("content", "").strip()
            if reply_text:
                return ChatResponse(reply=reply_text, language=reply_language)
    except Exception as e:
        print(f"[chat] Ollama unavailable ({e}), using Kala Saathi empathetic responder")

    reply_text = _fallback_reply(request.message, reply_language)
    return ChatResponse(reply=reply_text, language=reply_language)
