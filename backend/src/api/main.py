from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
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
from services.similarity import SimilarityService
from services.enhanced_news_pipeline import EnhancedNewsPipelineService
from api.chat import router as chat_router

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

# Initialize database and services
db = NewsDatabase()
similarity_service = SimilarityService(db)
enhanced_pipeline_service = EnhancedNewsPipelineService(db)

# Include chat router
app.include_router(chat_router)

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
            sources = ['abc', 'guardian', 'smh', 'news_com_au']  # Default to all 4 sources
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

@app.get("/articles/enhanced-latest")
async def get_enhanced_latest_articles(
    sources: Optional[List[str]] = Query(None, description="Sources to extract from (default: all 4 sources)"),
    categories: Optional[List[str]] = Query(None, description="Categories to include (default: all 4 categories)"),
    articles_per_category: int = Query(20, ge=1, le=50, description="Articles per category per source")
):
    """
    Enhanced 'Get Latest News' feature with intelligent prioritization.

    This endpoint:
    1. Extracts articles from multiple sources (up to 320 total articles)
    2. Runs AI classification for proper categorization
    3. Detects similarities and clusters related articles
    4. Applies intelligent prioritization based on breaking news indicators
    5. Returns top 10 prioritized stories with comprehensive metadata

    Processing typically takes 3-5 minutes for full extraction (320 articles).
    """
    try:
        logger.info(f"Starting enhanced latest articles extraction with "
                   f"sources: {sources}, categories: {categories}, "
                   f"articles_per_category: {articles_per_category}")

        # Run the enhanced pipeline
        results = await enhanced_pipeline_service.run_enhanced_extraction(
            sources=sources,
            categories=categories,
            articles_per_category=articles_per_category
        )

        if not results['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Enhanced extraction failed: {results.get('error', 'Unknown error')}"
            )

        # Return comprehensive results
        return {
            "success": True,
            "message": "Enhanced latest articles extraction completed successfully",
            "processing_time": results['processing_time'],
            "top_stories": results['top_stories'],
            "metrics": {
                "total_articles_extracted": results['metrics']['total_articles_extracted'],
                "similar_pairs_found": results['metrics']['similar_pairs_found'],
                "clusters_created": results['metrics']['clusters_created'],
                "stories_prioritized": results['metrics']['stories_prioritized'],
                "top_stories_selected": results['metrics']['top_stories_count']
            },
            "extraction_summary": {
                "expected_articles": results['extraction'].get('expected_articles', 0),
                "extraction_rate": results['extraction'].get('extraction_rate', 0),
                "sources_processed": results['extraction'].get('sources_processed', 0),
                "categories_processed": results['extraction'].get('categories_processed', 0),
                "by_category": results['extraction'].get('by_category', {}),
                "by_source": results['extraction'].get('by_source', {})
            },
            "similarity_summary": {
                "total_comparisons": results['similarity'].get('total_comparisons', 0),
                "similarity_rate": results['similarity'].get('similarity_rate', 0),
                "average_similarity_score": results['similarity'].get('average_similarity_score', 0)
            },
            "prioritization_summary": {
                "total_stories_analyzed": results['prioritization'].get('total_stories_analyzed', 0),
                "average_priority_score": results['prioritization'].get('average_priority_score', 0),
                "priority_distribution": results['prioritization'].get('priority_distribution', {})
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enhanced latest articles extraction: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced extraction failed: {str(e)}"
        )

@app.get("/articles/enhanced-status")
async def get_enhanced_pipeline_status():
    """Get status and health information for the enhanced news pipeline."""
    try:
        status = await enhanced_pipeline_service.get_pipeline_status()
        return {
            "success": True,
            "pipeline_status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting enhanced pipeline status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline status")

# Similarity Detection Endpoints

@app.get("/articles/{article_id}/similar")
async def get_similar_articles(article_id: int, limit: int = Query(5, ge=1, le=20)):
    """Get articles similar to the specified article"""
    try:
        similar_articles = similarity_service.find_similar_articles(article_id, limit)

        if not similar_articles:
            return {"message": "No similar articles found", "similar_articles": []}

        return {
            "article_id": article_id,
            "similar_articles": similar_articles,
            "count": len(similar_articles)
        }

    except Exception as e:
        logger.error(f"Error finding similar articles for {article_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar articles")

@app.get("/articles/clusters")
async def get_article_clusters(limit: int = Query(10, ge=1, le=50)):
    """Get clusters of similar articles grouped by story"""
    try:
        clusters = similarity_service.get_article_clusters(limit)

        return {
            "clusters": clusters,
            "count": len(clusters)
        }

    except Exception as e:
        logger.error(f"Error getting article clusters: {e}")
        raise HTTPException(status_code=500, detail="Failed to get article clusters")

@app.post("/articles/detect-similarity")
async def detect_article_similarities(hours_back: int = Query(48, ge=1, le=168)):
    """Trigger similarity detection for recent articles"""
    try:
        logger.info(f"Starting similarity detection for articles from last {hours_back} hours")

        metrics = similarity_service.detect_all_similarities(hours_back)

        return {
            "success": True,
            "message": "Similarity detection completed",
            "metrics": {
                "total_comparisons": metrics.total_comparisons,
                "similar_pairs_found": metrics.similar_pairs_found,
                "clusters_created": metrics.clusters_created,
                "average_similarity_score": round(metrics.average_similarity_score, 3),
                "processing_time": round(metrics.processing_time, 2),
                "similarity_rate": round(metrics.similarity_rate, 1)
            }
        }

    except Exception as e:
        logger.error(f"Error during similarity detection: {e}")
        return {
            "success": False,
            "message": f"Similarity detection failed: {str(e)}",
            "metrics": None
        }

@app.get("/articles/similarity-stats")
async def get_similarity_statistics():
    """Get statistics about similarity detection performance"""
    try:
        # Get recent similarity data from database
        recent_similarities = db.get_recent_similarities(limit=100)

        if not recent_similarities:
            return {
                "message": "No similarity data available",
                "stats": {
                    "total_similarities": 0,
                    "average_score": 0.0,
                    "high_similarity_count": 0,
                    "recent_detections": 0
                }
            }

        # Calculate statistics
        scores = [s['similarity_score'] for s in recent_similarities]
        high_similarity_count = len([s for s in scores if s >= 0.8])

        stats = {
            "total_similarities": len(recent_similarities),
            "average_score": round(sum(scores) / len(scores), 3),
            "high_similarity_count": high_similarity_count,
            "recent_detections": len([s for s in recent_similarities if s.get('created_at')]),
            "score_distribution": {
                "high (≥0.8)": high_similarity_count,
                "medium (0.6-0.8)": len([s for s in scores if 0.6 <= s < 0.8]),
                "low (<0.6)": len([s for s in scores if s < 0.6])
            }
        }

        return {
            "message": "Similarity statistics retrieved successfully",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting similarity statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get similarity statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)