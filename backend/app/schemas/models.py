"""
Structured data contracts for the artisan AI pipeline.

Every endpoint returns one of these models, so Person 3 (backend) and
Person 5 (pricing ML) always get predictable, typed JSON — no guessing
about field names or shapes.
"""

from typing import Optional
from pydantic import BaseModel, Field

# Supported languages -- code -> full name (used when prompting the LLM).
# Add more here as needed; every language-aware endpoint below accepts
# any subset of these via a `languages` list in the request.
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "mr": "Marathi",
}
DEFAULT_LANGUAGES = ["en", "hi"]


class TranscriptionResult(BaseModel):
    """Output of /transcribe — raw speech converted to text."""

    raw_text: str = Field(..., description="Verbatim transcription of the artisan's voice note")
    detected_language: str = Field(..., description="e.g. 'hi', 'en', 'hi-en' for Hinglish")
    confidence: float = Field(..., ge=0.0, le=1.0)


class ExtractedProduct(BaseModel):
    """
    Output of /extract — structured facts pulled from raw_text.

    Every field is Optional[str] rather than str with a default, because
    "unknown" is a real, meaningful state here (see no-hallucination note
    in extraction_service.py). None means "the artisan did not say this",
    not "the AI forgot to fill it in".
    """

    product_name: Optional[str] = None
    material: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: Optional[str] = None
    raw_source_text: str = Field(..., description="The transcript this was extracted from, for traceability")
    needs_clarification: list[str] = Field(
        default_factory=list,
        description="Fields the AI could not confidently fill — used to trigger a follow-up question to the artisan instead of guessing",
    )


class CatalogEntry(BaseModel):
    """One language's worth of listing copy."""

    language: str = Field(..., description="Language code, e.g. 'en', 'hi', 'bn', 'mr'")
    title: str
    description: str
    keywords: list[str]
    category: str


class CatalogRequest(BaseModel):
    """Input to /generate-catalog."""

    product: ExtractedProduct
    languages: list[str] = Field(
        default_factory=lambda: list(DEFAULT_LANGUAGES),
        description=f"Language codes to generate, from: {list(SUPPORTED_LANGUAGES.keys())}. Defaults to English + Hindi.",
    )


class MultilingualCatalog(BaseModel):
    """Output of /generate-catalog — one entry per requested language."""

    entries: list[CatalogEntry]
    listing_quality_score: int = Field(..., ge=0, le=100)
    quality_suggestions: list[str] = Field(default_factory=list)


class EnhancedImage(BaseModel):
    """Output of /enhance-image."""

    original_filename: str
    enhanced_image_path: str
    background_removed: bool
    lighting_corrected: bool
    background_color: str = Field(..., description="Background applied: white, light_gray, soft_beige, or pastel_blue")
    dimensions: str = Field(..., description="e.g. '1024x1024'")


class ArtisanStory(BaseModel):
    """One language's worth of narrative story text."""

    story_text: str
    language: str


class StoryRequest(BaseModel):
    """Input to /generate-story."""

    product: ExtractedProduct
    languages: list[str] = Field(
        default_factory=lambda: list(DEFAULT_LANGUAGES),
        description=f"Language codes to generate, from: {list(SUPPORTED_LANGUAGES.keys())}. Defaults to English + Hindi.",
    )


class MultilingualStory(BaseModel):
    """Output of /generate-story — one of the stated AI differentiators.

    Grounded strictly in the artisan's own verified facts (ExtractedProduct)
    -- the LLM is instructed not to invent history, techniques, or
    materials beyond what's actually known, same no-hallucination
    principle as the extraction stage."""

    stories: list[ArtisanStory]


class FullListing(BaseModel):
    """
    The final combined object sent to Person 3's backend via /generate-catalog
    or a dedicated /integrate step. This is what "Integrate & Output" produces.
    """

    extracted_product: ExtractedProduct
    catalog: MultilingualCatalog
    image: Optional[EnhancedImage] = None
    story: Optional[MultilingualStory] = None


class ClarificationQuestion(BaseModel):
    """One follow-up question for a single missing field, in every requested language."""

    field: str = Field(..., description="The ExtractedProduct field this question is about, e.g. 'material'")
    questions: dict[str, str] = Field(..., description="Language code -> question text, e.g. {'en': '...', 'hi': '...'}")


class ClarificationsRequest(BaseModel):
    """Input to /clarifications."""

    product: ExtractedProduct
    languages: list[str] = Field(
        default_factory=lambda: list(DEFAULT_LANGUAGES),
        description=f"Language codes to generate questions in, from: {list(SUPPORTED_LANGUAGES.keys())}. Defaults to English + Hindi.",
    )


class ClarificationsResponse(BaseModel):
    """
    Output of /clarifications — implements the "Smart Clarifications"
    differentiator: turns needs_clarification (which fields are missing)
    into actual, friendly follow-up questions the app can show the artisan,
    instead of the app guessing or leaving the listing incomplete.

    Template-based, not LLM-generated -- deterministic and instant, and
    there's no risk of a clarification question itself being wrong or
    oddly-phrased for such a small, fixed set of fields.
    """

    questions: list[ClarificationQuestion]
    all_fields_complete: bool = Field(..., description="True if there was nothing to clarify")


class TrendingTopic(BaseModel):
    """One trending keyword/category, with a relative search-interest score."""

    keyword: str
    interest_score: int = Field(..., ge=0, le=100, description="Relative search interest, 0-100 (Google Trends scale)")
    category: str


class TrendingTopicsResponse(BaseModel):
    """Output of /trending-topics."""

    topics: list[TrendingTopic]
    region: str = Field(..., description="Region the trend data was pulled for, e.g. 'IN'")
    generated_note: str = Field(
        default="Based on relative search interest over the last 7 days.",
        description="Explains what the scores mean, shown to the artisan/app for transparency",
    )


class ChatMessage(BaseModel):
    """One turn in a chat conversation."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    """Input to /chat."""

    message: str = Field(..., description="The artisan's current question")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Prior turns in this conversation, oldest first, for context. Empty for a fresh conversation.",
    )
    language: Optional[str] = Field(
        default=None, description="Preferred reply language, e.g. 'hi' or 'en'. If omitted, replies in the language the artisan used."
    )


class ChatResponse(BaseModel):
    """Output of /chat."""

    reply: str
    language: str