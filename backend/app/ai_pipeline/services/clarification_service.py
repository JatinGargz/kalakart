"""
Smart Clarifications -- one of the stated AI differentiators ("when unsure,
AI asks the artisan instead of guessing").

Takes the needs_clarification list already produced by extraction_service.py
(fields the AI couldn't confidently fill from the transcript) and turns
them into actual, friendly follow-up questions the app can show the
artisan, in whichever languages are requested.

Deliberately template-based rather than LLM-generated: the set of possible
fields is small and fixed, so a template gives instant, deterministic,
always-correctly-phrased questions with zero risk of the question itself
being awkward or wrong.

NOTE on translation quality: the Bengali and Marathi phrasings below are
straightforward, reviewed-once translations covering a small fixed set of
questions -- good enough for a hackathon demo, but worth having a native
speaker sanity-check them before wider use, same as any UI translation.
"""

from app.schemas.models import ClarificationQuestion, ClarificationsResponse, ExtractedProduct, SUPPORTED_LANGUAGES

QUESTION_TEMPLATES = {
    "product_name": {
        "en": "What would you like to call this product?",
        "hi": "Aap is product ka naam kya rakhna chahenge?",
        "bn": "Apni ei product-ti ki naam dite chan?",
        "mr": "Tumhala ha product kay naav dyaycha ahe?",
    },
    "material": {
        "en": "What material is this product made of?",
        "hi": "Yeh product kis material se bana hai?",
        "bn": "Ei product-ti kon upadan diye toiri?",
        "mr": "Ha product konatya materialpasun banla ahe?",
    },
    "category": {
        "en": "What category does this product belong to (e.g. home decor, textiles, jewellery)?",
        "hi": "Yeh product kis category mein aata hai (jaise ghar ki sajavat, kapda, gehne)?",
        "bn": "Ei product-ti kon category-r under-e pore (jemon ghor sajanor jinis, kapor, gohona)?",
        "mr": "Ha product konatya category madhe yeto (jase ghar sajavat, kapad, dagine)?",
    },
    "color": {
        "en": "What color is this product?",
        "hi": "Is product ka rang kya hai?",
        "bn": "Ei product-tir rong ki?",
        "mr": "Ya productcha rang kay ahe?",
    },
    "size": {
        "en": "What size is this product (e.g. small, medium, large, or dimensions)?",
        "hi": "Is product ka size kya hai (jaise chota, madhyam, bada, ya naapein)?",
        "bn": "Ei product-tir size ki (jemon choto, moddhom, boro, ba maap)?",
        "mr": "Ya productcha size kay ahe (jase lahan, madhyam, motha, kinva maap)?",
    },
    "quantity": {
        "en": "How many pieces are available right now?",
        "hi": "Abhi kitne pieces available hain?",
        "bn": "Ekhon koyta piece available ache?",
        "mr": "Sadhya kiti pieces uplabdha aahet?",
    },
}


def get_clarifications(product: ExtractedProduct, languages: list[str]) -> ClarificationsResponse:
    valid_languages = [code for code in languages if code in SUPPORTED_LANGUAGES]

    questions = []
    for field in product.needs_clarification:
        template = QUESTION_TEMPLATES.get(field)
        if not template:
            continue  # unknown field name, skip rather than guess a question

        translations = {code: template[code] for code in valid_languages if code in template}
        if translations:
            questions.append(ClarificationQuestion(field=field, questions=translations))

    return ClarificationsResponse(questions=questions, all_fields_complete=len(questions) == 0)