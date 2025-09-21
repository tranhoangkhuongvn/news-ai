from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import asyncio
import logging
import os
import sys

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Production configuration
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

from services.news_extraction_pipeline import run_extraction_pipeline
from scrapers.aussie_news_extractor import ExtractorFactory
from db.database_conn import NewsDatabase
from api.models import NewsArticleResponse, DashboardResponse, ExtractionRequest, ExtractionResponse
from api.utils import convert_db_article_to_response, convert_backend_article_to_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Australian News AI API",
    description="API for aggregating and serving Australian news from multiple sources",
    version="1.0.0"
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "https://cool-news-ai-app-2qwl5.ondigitalocean.app"
    ],  # Vite dev server (various ports), React dev server, and deployed frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = NewsDatabase()

@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    return {"message": "Australian News AI API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}

@app.get("/sources")
async def get_available_sources():
    """Get list of available news sources"""
    sources = ExtractorFactory.get_available_sources()
    source_info = {
        'abc': {'name': 'ABC News', 'url': 'https://www.abc.net.au'},
        'guardian': {'name': 'The Guardian AU', 'url': 'https://www.theguardian.com'},
        'news_com_au': {'name': 'News.com.au', 'url': 'https://www.news.com.au'},
        'smh': {'name': 'Sydney Morning Herald', 'url': 'https://www.smh.com.au'}
    }

    return {
        "sources": [
            {
                "id": source_id,
                "name": source_info.get(source_id, {}).get('name', source_id),
                "url": source_info.get(source_id, {}).get('url', '')
            }
            for source_id in sources
        ]
    }

@app.get("/categories")
async def get_available_categories():
    """Get list of available news categories"""
    return {
        "categories": [
            {"category": "music", "label": "Music", "color": "#8B5CF6"},
            {"category": "lifestyle", "label": "Lifestyle", "color": "#10B981"},
            {"category": "finance", "label": "Finance", "color": "#F59E0B"},
            {"category": "sports", "label": "Sports", "color": "#EF4444"}
        ]
    }

@app.get("/articles", response_model=List[NewsArticleResponse])
async def get_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(50, ge=1, le=200, description="Number of articles to return")
):
    """Get articles from the database with optional filtering"""
    try:
        # Get articles from database
        articles = db.get_articles(category=category, limit=limit)

        # Filter by source if specified
        if source:
            articles = [article for article in articles if article.get('source', '').lower() == source.lower()]

        # Convert to response format
        response_articles = [convert_db_article_to_response(article) for article in articles]

        logger.info(f"Returning {len(response_articles)} articles")
        return response_articles

    except Exception as e:
        logger.error(f"Error retrieving articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve articles")

@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data():
    """Get dashboard data including top articles by category"""
    try:
        # Get articles from database
        all_articles = db.get_articles(limit=100)

        if not all_articles:
            # If no articles in database, return empty dashboard
            return DashboardResponse(
                topArticles=[],
                categories={"music": [], "lifestyle": [], "finance": [], "sports": []},
                sources=[]
            )

        # Convert to response format
        articles = [convert_db_article_to_response(article) for article in all_articles]

        # Get balanced selection of articles from all sources
        source_articles = {}
        for article in articles:
            source = article.source
            if source not in source_articles:
                source_articles[source] = []
            source_articles[source].append(article)

        # Get 2-3 articles from each source for balanced representation
        top_articles = []
        articles_per_source = max(2, 10 // len(source_articles)) if source_articles else 10

        for source, source_article_list in source_articles.items():
            top_articles.extend(source_article_list[:articles_per_source])

        # If we still need more articles, add the remaining newest ones
        if len(top_articles) < 10:
            remaining = [a for a in articles if a not in top_articles]
            top_articles.extend(remaining[:10 - len(top_articles)])

        # Limit to 10 articles total
        top_articles = top_articles[:10]

        # Group articles by category
        categories = {
            "music": [article for article in articles if article.category == "music"],
            "lifestyle": [article for article in articles if article.category == "lifestyle"],
            "finance": [article for article in articles if article.category == "finance"],
            "sports": [article for article in articles if article.category == "sports"]
        }

        # Get unique sources
        sources = []
        seen_sources = set()
        source_mapping = {
            'ABC News': {'id': 'abc', 'name': 'ABC News', 'url': 'https://www.abc.net.au'},
            'The Guardian AU': {'id': 'guardian', 'name': 'The Guardian AU', 'url': 'https://www.theguardian.com'},
            'News.com.au': {'id': 'news_com_au', 'name': 'News.com.au', 'url': 'https://www.news.com.au'},
            'Sydney Morning Herald': {'id': 'smh', 'name': 'Sydney Morning Herald', 'url': 'https://www.smh.com.au'}
        }

        for article in articles:
            if article.source not in seen_sources:
                seen_sources.add(article.source)
                source_info = source_mapping.get(article.source, {
                    'id': article.source.lower().replace(' ', '_'),
                    'name': article.source,
                    'url': ''
                })
                sources.append(source_info)

        return DashboardResponse(
            topArticles=top_articles,
            categories=categories,
            sources=sources
        )

    except Exception as e:
        logger.error(f"Error retrieving dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

@app.post("/extract", response_model=ExtractionResponse)
async def extract_news(request: ExtractionRequest):
    """Trigger news extraction from specified sources and categories"""
    try:
        logger.info(f"Starting extraction for sources: {request.sources}, categories: {request.categories}")

        # Run the extraction pipeline
        results = await run_extraction_pipeline(
            sources=request.sources,
            categories=request.categories,
            max_articles=request.max_articles
        )

        # Convert the results to response format
        return ExtractionResponse(
            success=True,
            message=f"Extraction completed successfully",
            total_articles=results.get('total_articles', 0),
            successful_saves=results.get('successful_saves', 0),
            failed_saves=results.get('failed_saves', 0),
            by_category=results.get('by_category', {}),
            by_source=results.get('by_source', {}),
            extraction_time=results.get('extraction_time', 0),
            errors=results.get('errors', [])
        )

    except Exception as e:
        logger.error(f"Error during news extraction: {e}")
        return ExtractionResponse(
            success=False,
            message=f"Extraction failed: {str(e)}",
            total_articles=0,
            successful_saves=0,
            failed_saves=0,
            by_category={},
            by_source={},
            extraction_time=0,
            errors=[str(e)]
        )

@app.get("/articles/latest", response_model=List[NewsArticleResponse])
async def get_latest_articles(
    sources: Optional[List[str]] = Query(None, description="Sources to extract from"),
    categories: Optional[List[str]] = Query(None, description="Categories to include"),
    max_articles: int = Query(20, ge=1, le=50, description="Max articles per category")
):
    """Extract and return the latest articles from news sources"""
    try:
        # Use default sources and categories if not specified
        if not sources:
            sources = ['abc', 'guardian']  # Default to ABC and Guardian for speed
        if not categories:
            categories = ['sports', 'finance', 'lifestyle', 'music']

        logger.info(f"Extracting latest articles from sources: {sources}, categories: {categories}")

        # Run extraction pipeline
        results = await run_extraction_pipeline(
            sources=sources,
            categories=categories,
            max_articles=max_articles
        )

        # Get the newly extracted articles from database
        latest_articles = db.get_articles(limit=max_articles * len(categories))

        # Convert to response format
        response_articles = [convert_db_article_to_response(article) for article in latest_articles]

        logger.info(f"Extracted and returning {len(response_articles)} latest articles")
        return response_articles

    except Exception as e:
        logger.error(f"Error extracting latest articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract latest articles")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)