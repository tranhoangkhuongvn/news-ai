from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class NewsArticleResponse(BaseModel):
    """Response model for news articles that matches frontend expectations"""
    id: str
    title: str
    summary: str
    content: str
    category: str
    source: str
    author: Optional[str] = ""
    publishedAt: str  # ISO format datetime string
    url: str
    highlights: List[str] = []
    imageUrl: Optional[str] = None

class NewsSourceResponse(BaseModel):
    """Response model for news sources"""
    id: str
    name: str
    url: str
    logo: Optional[str] = None

class CategoryResponse(BaseModel):
    """Response model for news categories"""
    category: str
    label: str
    color: str

class DashboardResponse(BaseModel):
    """Response model for dashboard data"""
    topArticles: List[NewsArticleResponse]
    categories: Dict[str, List[NewsArticleResponse]]
    sources: List[Dict[str, str]]

class ExtractionRequest(BaseModel):
    """Request model for news extraction"""
    sources: Optional[List[str]] = Field(default=['abc', 'guardian'], description="List of source IDs to extract from")
    categories: Optional[List[str]] = Field(default=['sports', 'finance', 'lifestyle', 'music'], description="List of categories to extract")
    max_articles: int = Field(default=20, ge=1, le=50, description="Maximum articles per category")

class ExtractionResponse(BaseModel):
    """Response model for extraction results"""
    success: bool
    message: str
    total_articles: int
    successful_saves: int
    failed_saves: int
    by_category: Dict[str, int]
    by_source: Dict[str, int]
    extraction_time: float
    errors: List[str]

class ArticleFilterParams(BaseModel):
    """Model for article filtering parameters"""
    category: Optional[str] = None
    source: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)