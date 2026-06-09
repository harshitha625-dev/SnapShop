"""
backend/routers/analyze.py
Image analysis router using Gemini API.
"""
import os
import json
import logging
from io import BytesIO
from fastapi import APIRouter, HTTPException
import httpx
from PIL import Image

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from backend.config import settings
from backend.models.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Allowed product categories for search linkage
ALLOWED_CATEGORIES = [
    "fashion",
    "footwear",
    "watches",
    "electronics",
    "bags",
    "beauty",
    "accessories",
    "furniture"
]

def get_gemini_api_key() -> str:
    """Retrieve Gemini API key from settings or environment variables."""
    key = settings.GEMINI_API_KEY
    if not key:
        key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        key = os.environ.get("GOOGLE_API_KEY", "")
    return key.strip().replace('"', '').replace("'", "")

@router.post("/analyze-image", response_model=AnalyzeResponse)
async def analyze_image(payload: AnalyzeRequest):
    """
    Analyze the uploaded image using Gemini API and return structured descriptive data.
    """
    if genai is None:
        raise HTTPException(
            status_code=500,
            detail="The google-generativeai package is not installed on the server. Please check requirements."
        )

    api_key = get_gemini_api_key()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail=(
                "GEMINI_API_KEY is not configured. "
                "Please add GEMINI_API_KEY to your .env.local file or set it in the environment."
            )
        )

    # ── 1. Read Image Data ──
    image_bytes = None
    try:
        if "/static/uploads/" in payload.image_url:
            # Local file upload resolution
            filename = payload.image_url.split("/")[-1]
            filepath = os.path.join("data/uploads", filename)
            if not os.path.exists(filepath):
                raise HTTPException(status_code=404, detail="Uploaded image file not found.")
            with open(filepath, "rb") as f:
                image_bytes = f.read()
        else:
            # External URL download
            async with httpx.AsyncClient() as client:
                resp = await client.get(payload.image_url, timeout=15.0)
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch image from URL. Status code: {resp.status_code}"
                    )
                image_bytes = resp.content
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error reading image source: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read image source: {str(e)}")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty or invalid image data.")

    # ── 2. Run Gemini Multimodal Analysis ──
    try:
        # Configure the client
        genai.configure(api_key=api_key)
        
        # Load image via PIL
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        
        # We use gemini-1.5-flash for fast and cost-effective multimodal analysis
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = (
            "Analyze this image and describe its contents in detail. "
            "Identify the main item/product shown, its key features, colors, branding, logos, and styling suggestions. "
            "You MUST return the response in JSON format matching this exact schema: \n"
            "{\n"
            "  \"description\": \"A paragraph detailing the main subject, its style, look, and context.\",\n"
            "  \"items\": [\"list of primary items or components detected in the image (max 5)\"],\n"
            "  \"colors\": [\"list of dominant hex color codes (e.g. #3b82f6) present in the image (max 5)\"],\n"
            "  \"style_tags\": [\"list of aesthetic, vibe, or style keywords (e.g., Casual, Elegant, Streetwear) (max 5)\"],\n"
            "  \"suggestions\": [\"list of styling suggestions, usage tips, or product complements (max 3)\"],\n"
            "  \"brand\": \"The visible brand name or manufacturer if detectable from the image (e.g., 'Nike', 'Rolex', 'Unbranded' if none is seen/detectable)\",\n"
            "  \"symbols\": [\"list of visible logos, symbols, insignia, prints, or brand markings (e.g., 'Swoosh', 'Golden Crown logo', '3-stripes', 'floral pattern') (max 3)\"],\n"
            f"  \"detected_category\": \"The single best matching category for catalog search. Must be one of: {', '.join(ALLOWED_CATEGORIES)} or 'general'\"\n"
            "}"
        )
        
        logger.info("Sending image to Gemini for analysis...")
        response = model.generate_content(
            contents=[img, prompt],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse the JSON response
        result = json.loads(response.text)
        
        # Normalize category
        cat = str(result.get("detected_category", "general")).lower()
        if cat not in ALLOWED_CATEGORIES:
            cat = "general"
            
        return AnalyzeResponse(
            description=result.get("description", "No description generated."),
            items=result.get("items", []),
            colors=result.get("colors", []),
            style_tags=result.get("style_tags", []),
            suggestions=result.get("suggestions", []),
            detected_category=cat,
            brand=result.get("brand", "Unbranded"),
            symbols=result.get("symbols", [])
        )

    except Exception as e:
        logger.error(f"Gemini generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Gemini analysis failed: {str(e)}"
        )
