from typing import Dict, Any, List
import json
import hashlib
from datetime import datetime
from api.models import NewsArticleResponse
from models.news_model import NewsArticle

def convert_db_article_to_response(db_article: Dict[str, Any]) -> NewsArticleResponse:
    """Convert database article dictionary to API response model"""

    # Generate ID from URL if not present
    article_id = str(db_article.get('id', '')) or hashlib.md5(db_article.get('url', '').encode()).hexdigest()[:8]

    # Parse tags from JSON string
    tags = []
    if db_article.get('tags'):
        try:
            if isinstance(db_article['tags'], str):
                tags = json.loads(db_article['tags'])
            elif isinstance(db_article['tags'], list):
                tags = db_article['tags']
        except (json.JSONDecodeError, TypeError):
            tags = []

    # Create highlights from tags and summary
    highlights = []
    if tags:
        highlights.extend(tags[:3])  # Use first 3 tags as highlights

    # If no tags, create highlights from summary
    if not highlights and db_article.get('summary'):
        summary_parts = db_article['summary'].split('. ')
        if len(summary_parts) > 1:
            highlights = [part.strip() + '.' for part in summary_parts[:2] if part.strip()]

    # Ensure we have at least one highlight
    if not highlights:
        highlights = ["Breaking news update"]

    # Format published date
    published_at = db_article.get('published_date', '')
    if not published_at:
        # Use extracted_at as fallback
        published_at = db_article.get('extracted_at', datetime.now().isoformat())

    # Ensure ISO format
    try:
        if published_at and not published_at.endswith('Z') and '+' not in published_at:
            # Add Z for UTC if not present
            if 'T' in published_at:
                published_at = published_at + 'Z'
            else:
                published_at = datetime.now().isoformat() + 'Z'
    except:
        published_at = datetime.now().isoformat() + 'Z'

    return NewsArticleResponse(
        id=article_id,
        title=db_article.get('title', 'Untitled'),
        summary=db_article.get('summary', ''),
        content=db_article.get('content', ''),
        category=db_article.get('category', 'general'),
        source=db_article.get('source', 'Unknown'),
        author=db_article.get('author', ''),
        publishedAt=published_at,
        url=db_article.get('url', ''),
        highlights=highlights,
        imageUrl=None  # TODO: Add image extraction in future
    )

def convert_backend_article_to_response(backend_article: NewsArticle) -> NewsArticleResponse:
    """Convert backend NewsArticle dataclass to API response model"""

    # Generate ID from URL
    article_id = hashlib.md5(backend_article.url.encode()).hexdigest()[:8]

    # Create highlights from tags
    highlights = backend_article.tags[:3] if backend_article.tags else ["Breaking news update"]

    # Format published date
    published_at = backend_article.published_date
    if not published_at.endswith('Z') and '+' not in published_at:
        if 'T' in published_at:
            published_at = published_at + 'Z'
        else:
            published_at = datetime.now().isoformat() + 'Z'

    return NewsArticleResponse(
        id=article_id,
        title=backend_article.title,
        summary=backend_article.summary,
        content=backend_article.content,
        category=backend_article.category,
        source=backend_article.source,
        author=backend_article.author,
        publishedAt=published_at,
        url=backend_article.url,
        highlights=highlights,
        imageUrl=None
    )

def create_highlights_from_content(content: str, summary: str = "", tags: List[str] = None) -> List[str]:
    """Create highlights from article content, summary, and tags"""
    highlights = []

    # Use tags as highlights if available
    if tags:
        highlights.extend(tags[:2])

    # Extract key sentences from summary
    if summary and len(highlights) < 3:
        sentences = summary.split('. ')
        for sentence in sentences[:3-len(highlights)]:
            if sentence.strip() and len(sentence) > 20:
                highlights.append(sentence.strip() + '.')

    # Extract key sentences from content if still need more
    if content and len(highlights) < 3:
        sentences = content.split('. ')
        for sentence in sentences[:3-len(highlights)]:
            if sentence.strip() and len(sentence) > 30 and len(sentence) < 120:
                highlights.append(sentence.strip() + '.')

    # Ensure we have at least one highlight
    if not highlights:
        highlights = ["Latest news update"]

    return highlights[:3]  # Return maximum 3 highlights

def format_extraction_stats(results: Dict[str, Any]) -> str:
    """Format extraction results into a readable message"""
    total = results.get('total_articles', 0)
    saved = results.get('successful_saves', 0)
    failed = results.get('failed_saves', 0)
    time_taken = results.get('extraction_time', 0)

    message = f"Extracted {total} articles in {time_taken:.2f}s"
    if saved > 0:
        message += f", saved {saved} successfully"
    if failed > 0:
        message += f", {failed} failed to save"

    return message

def validate_category(category: str) -> bool:
    """Validate if category is supported"""
    valid_categories = ['music', 'lifestyle', 'finance', 'sports']
    return category.lower() in valid_categories

def validate_source(source: str) -> bool:
    """Validate if source is supported"""
    valid_sources = ['abc', 'guardian', 'news_com_au', 'smh']
    return source.lower() in valid_sources