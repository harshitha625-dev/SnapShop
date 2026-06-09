import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ─── STORAGE (Cloudflare R2 or AWS S3) ─────
    R2_ENDPOINT_URL:       str = ""
    R2_ACCESS_KEY:         str = ""
    R2_SECRET_KEY:         str = ""
    R2_BUCKET_NAME:        str = "snapshop"
    CDN_BASE_URL:          str = "https://cdn.yourdomain.com"

    # ─── CACHE ──────────────────────────────────
    REDIS_URL:             str = "redis://localhost:6379"

    # ─── AFFILIATE ──────────────────────────────
    AMAZON_AFFILIATE_TAG:  str = "yourtag-21"
    FLIPKART_AFFILIATE_ID: str = ""
    CUELINKS_CID:          str = ""      # covers Myntra/Ajio/Nykaa
    GEMINI_API_KEY:        str = ""      # API key for Gemini LLM image analyzer
    SERPAPI_KEY:           str = ""      # API key for SerpApi web search

    MAX_IMAGE_SIZE_MB:     int = 10
    ENVIRONMENT:           str = "development"


    class Config:
        env_file = ".env.local"
        extra = "ignore"

settings = Settings()