"""
API endpoints Person 4's pipeline exposes to Person 3 (backend):
/transcribe, /extract, /generate-catalog, /enhance-image, /trending-topics,
/chat, /generate-story, /clarifications

Kept as separate endpoints (rather than one mega-endpoint) so:
- Person 3 can call only what's needed for a given app flow
- Each stage can be tested/demoed independently -- useful for judging
- Failures are isolated (bad audio doesn't break image processing)
"""

import os
import shutil
import tempfile

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.schemas.models import (
    TranscriptionResult,
    ExtractedProduct,
    CatalogRequest,
    MultilingualCatalog,
    EnhancedImage,
    TrendingTopicsResponse,
    ChatRequest,
    ChatResponse,
    StoryRequest,
    MultilingualStory,
    ClarificationsRequest,
    ClarificationsResponse,
)
from app.ai_pipeline.services import (
    transcription_service,
    extraction_service,
    catalog_service,
    image_service,
    trending_service,
    chatbot_service,
    story_service,
    clarification_service,
)

router = APIRouter()


@router.post("/transcribe", response_model=TranscriptionResult)
async def transcribe(audio: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name

    try:
        return transcription_service.transcribe_audio(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        os.unlink(tmp_path)


from fastapi import Body

@router.post("/extract", response_model=ExtractedProduct)
async def extract(payload: dict = Body(...)):
    try:
        raw_text = payload.get("raw_text") or payload.get("text") or ""
        return extraction_service.extract_product_info(raw_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")


@router.post("/generate-catalog", response_model=MultilingualCatalog)
async def generate_catalog(request: CatalogRequest):
    """
    request.languages: any subset of SUPPORTED_LANGUAGES codes (en, hi, bn, mr).
    Defaults to ["en", "hi"] if omitted.
    """
    try:
        return catalog_service.generate_catalog(request.product, request.languages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Catalog generation failed: {e}")


@router.post("/enhance-image", response_model=EnhancedImage)
async def enhance_image(image: UploadFile = File(...), background: str = Form("auto")):
    """
    background: 'auto' (default, picks the best-contrast option automatically),
    or an explicit choice: 'white', 'light_gray', 'soft_beige', 'pastel_blue'.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp:
        shutil.copyfileobj(image.file, tmp)
        tmp_path = tmp.name

    try:
        return image_service.enhance_image(tmp_path, background=background)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image enhancement failed: {e}")
    finally:
        os.unlink(tmp_path)


@router.get("/trending-topics", response_model=TrendingTopicsResponse)
async def trending_topics():
    """
    Trending product categories/keywords B2B buyers are currently searching
    for, based on free Google Trends data (via pytrends). Cached for 1 hour
    server-side to avoid rate limits -- see trending_service.py.
    """
    try:
        return trending_service.get_trending_topics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trending topics fetch failed: {e}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    General Q&A assistant for artisans -- how to use the app, listing tips,
    what the AI features do. Uses the same local Ollama model as the rest
    of the pipeline, so no extra setup if Ollama is already running.
    """
    try:
        return chatbot_service.get_chat_reply(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")


@router.post("/generate-story", response_model=MultilingualStory)
async def generate_story(request: StoryRequest):
    """
    Artisan Story Generation differentiator -- a short, warm narrative
    grounded strictly in the artisan's own verified facts (same
    no-hallucination principle as /extract).
    request.languages: any subset of SUPPORTED_LANGUAGES codes (en, hi, bn, mr).
    """
    try:
        return story_service.generate_story(request.product, request.languages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story generation failed: {e}")


@router.post("/clarifications", response_model=ClarificationsResponse)
async def clarifications(request: ClarificationsRequest):
    """
    Smart Clarifications differentiator -- turns the needs_clarification
    list from /extract into actual follow-up questions the app can show
    the artisan, instead of guessing or leaving fields blank.
    Template-based, so it's instant and deterministic.
    request.languages: any subset of SUPPORTED_LANGUAGES codes (en, hi, bn, mr).
    """
    try:
        return clarification_service.get_clarifications(request.product, request.languages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clarification generation failed: {e}")