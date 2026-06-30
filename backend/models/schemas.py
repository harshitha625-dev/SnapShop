from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    image_url:  str
    image_hash: str
    message:    str

class PlatformPrice(BaseModel):
    platform:         str
    price:            str
    original_price:   Optional[str] = None
    discount:         Optional[str] = None
    buy_url:          str
    is_lowest:        bool = False

class LowCostPrediction(BaseModel):
    low_cost_threshold: int
    average_price: int
    median_price: int
    min_price: int
    max_price: int
    bargain_count: int
    confidence_score: float
    deal_rating: str
    prediction_reasoning: str

class PlatformResult(BaseModel):
    platform:         str             # "Amazon India" | "Flipkart" etc.
    title:            str
    price:            Optional[str]
    original_price:   Optional[str]
    discount:         Optional[str]
    product_url:      str             # original URL
    affiliate_url:    str             # tagged URL for earnings
    thumbnail:        Optional[str]
    rating:           Optional[str]
    category:         Optional[str] = "unknown"
    similarity_score: Optional[float] = 0.0
    in_stock:         bool = True
    comparison_prices: Optional[list[PlatformPrice]] = None
    lowest_price_platform: Optional[str] = None
    lowest_price:     Optional[str] = None
    is_low_cost:      bool = False

class VisualMatch(BaseModel):
    title:            str
    link:             str
    thumbnail:        Optional[str]
    source:           Optional[str]
    price:            Optional[str]
    category:         Optional[str] = "unknown"
    similarity_score: Optional[float] = 0.0
    comparison_prices: Optional[list[PlatformPrice]] = None
    lowest_price_platform: Optional[str] = None
    lowest_price:     Optional[str] = None
    is_low_cost:      bool = False

class SearchRequest(BaseModel):
    image_url:   str
    image_hash:  str
    max_results: int = 20
    category:    Optional[str] = None

class TextSearchRequest(BaseModel):
    query:       str
    max_results: int = 20
    category:    Optional[str] = None

class IndexStats(BaseModel):
    total_products: int
    embedding_dim:  int
    device:         str
    model:          str
    index_size_kb:  float

class LowCostDeal(BaseModel):
    title:            str
    price:            str
    platform:         str
    buy_url:          str

class SearchResponse(BaseModel):
    query_image_url:  str
    visual_matches:   list[VisualMatch]
    platform_results: list[PlatformResult]
    total_results:    int
    cached:           bool = False
    search_id:        str
    low_cost_prediction: Optional[LowCostPrediction] = None
    lowest_price_deal: Optional[LowCostDeal] = None

class AnalyzeRequest(BaseModel):
    image_url: str

class AnalyzeResponse(BaseModel):
    description: str
    items: list[str]
    colors: list[str]
    style_tags: list[str]
    suggestions: list[str]
    detected_category: str
    brand: str
    symbols: list[str]