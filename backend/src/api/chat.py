"""
FastAPI endpoints for RAG chatbot functionality
"""

import logging
from typing import Optional, List
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from src.services.chatbot.chat_service import ChatService
from src.services.chatbot.embedding_service import EmbeddingService
from src.services.chatbot.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/chat", tags=["chatbot"])

# Initialize services (will be shared across requests)
chat_service = ChatService()
embedding_service = EmbeddingService()
retrieval_service = RetrievalService()

# Pydantic models for request/response validation

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    category_filter: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[dict]
    context_articles: List[dict]

class SessionRequest(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    message: str

class EmbedRequest(BaseModel):
    batch_size: Optional[int] = 10
    category_filter: Optional[str] = None

class EmbedResponse(BaseModel):
    success: bool
    articles_processed: int
    articles_embedded: int
    message: str

@router.post("/ask", response_model=ChatResponse)
async def chat_ask(request: ChatRequest):
    """
    Ask a question to the chatbot

    Args:
        request: Chat request with message and optional parameters

    Returns:
        Chat response with answer and sources
    """
    try:
        logger.info(f"Chat request: '{request.message[:50]}...'")

        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session_id = chat_service.create_session(
                user_id=request.user_id,
                title=f"Chat: {request.message[:30]}..."
            )

        # Process chat message
        result = chat_service.chat(
            session_id=session_id,
            user_message=request.message,
            category_filter=request.category_filter
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            sources=result["sources"],
            context_articles=result["context_articles"]
        )

    except Exception as e:
        logger.error(f"Error in chat_ask: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """
    Create a new chat session

    Args:
        request: Session creation request

    Returns:
        New session ID and confirmation message
    """
    try:
        session_id = chat_service.create_session(
            user_id=request.user_id,
            title=request.title
        )

        return SessionResponse(
            session_id=session_id,
            message="Chat session created successfully"
        )

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, limit: int = Query(50, ge=1, le=100)):
    """
    Get chat messages for a session

    Args:
        session_id: Session ID
        limit: Maximum number of messages to return

    Returns:
        List of chat messages
    """
    try:
        messages = chat_service.get_session_history(session_id)

        # Limit results
        messages = messages[-limit:] if len(messages) > limit else messages

        return {
            "session_id": session_id,
            "messages": messages,
            "total_messages": len(messages)
        }

    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """
    Clear a chat session

    Args:
        session_id: Session ID to clear

    Returns:
        Success confirmation
    """
    try:
        success = chat_service.clear_session(session_id)

        if success:
            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to clear session")

    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_articles(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None)
):
    """
    Search for relevant articles without starting a chat

    Args:
        query: Search query
        limit: Maximum number of results
        category: Optional category filter

    Returns:
        List of relevant articles
    """
    try:
        results = retrieval_service.retrieve_context(
            query=query,
            max_articles=limit,
            category_filter=category
        )

        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }

    except Exception as e:
        logger.error(f"Error in article search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/embeddings/create", response_model=EmbedResponse)
async def create_embeddings(request: EmbedRequest):
    """
    Create embeddings for articles that don't have them

    Args:
        request: Embedding request with optional parameters

    Returns:
        Results of the embedding process
    """
    try:
        logger.info("Starting embedding creation process...")

        # Get articles without embeddings
        from src.db.database_conn import NewsDatabase
        db = NewsDatabase()

        # This is a simplified version - in production you'd want better pagination
        import sqlite3
        with sqlite3.connect(db.db_path, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row

            # Get articles that don't have embeddings
            sql = """
                SELECT a.id, a.title, a.summary, a.content, a.category,
                       a.source, a.tags, a.url, a.published_date,
                       a.author, a.extracted_at
                FROM articles a
                LEFT JOIN article_embeddings ae ON a.id = ae.article_id
                WHERE ae.article_id IS NULL
            """

            if request.category_filter:
                sql += " AND a.category = ?"
                cursor = conn.execute(sql, (request.category_filter,))
            else:
                cursor = conn.execute(sql)

            articles_to_process = []
            for row in cursor.fetchall():
                article_dict = dict(row)
                # Convert to NewsArticle
                from src.models.news_model import NewsArticle
                article = NewsArticle(
                    title=article_dict['title'],
                    url=article_dict['url'],
                    category=article_dict['category'],
                    summary=article_dict['summary'] or '',
                    published_date=article_dict['published_date'] or '',
                    author=article_dict['author'] or '',
                    content=article_dict['content'] or '',
                    source=article_dict['source'],
                    tags=article_dict['tags'].split(',') if article_dict['tags'] else [],
                    extracted_at=article_dict['extracted_at']
                )
                articles_to_process.append((article, article_dict['id']))

        total_articles = len(articles_to_process)
        logger.info(f"Found {total_articles} articles to embed")

        if total_articles == 0:
            return EmbedResponse(
                success=True,
                articles_processed=0,
                articles_embedded=0,
                message="No articles found that need embeddings"
            )

        # Process in batches
        embedded_count = embedding_service.embed_articles_batch(
            articles_to_process,
            batch_size=request.batch_size or 10
        )

        return EmbedResponse(
            success=True,
            articles_processed=total_articles,
            articles_embedded=embedded_count,
            message=f"Successfully embedded {embedded_count} out of {total_articles} articles"
        )

    except Exception as e:
        logger.error(f"Error creating embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_chat_stats():
    """
    Get statistics about the chat system

    Returns:
        System statistics and health information
    """
    try:
        chat_stats = chat_service.get_chat_stats()
        retrieval_stats = retrieval_service.get_retrieval_stats()
        embedding_stats = embedding_service.get_embedding_stats()

        return {
            "chat_stats": chat_stats,
            "retrieval_stats": retrieval_stats,
            "embedding_stats": embedding_stats,
            "system_health": {
                "openai_configured": chat_stats.get("openai_configured", False),
                "embeddings_available": embedding_stats.get("unique_articles", 0) > 0,
                "total_articles": retrieval_stats.get("total_articles", 0)
            }
        }

    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def chat_health():
    """
    Health check for chat system

    Returns:
        Health status of chat components
    """
    try:
        # Test basic functionality
        embedding_stats = embedding_service.get_embedding_stats()
        retrieval_stats = retrieval_service.get_retrieval_stats()

        health_status = {
            "status": "healthy",
            "components": {
                "embedding_service": "ok" if not embedding_stats.get("error") else "error",
                "retrieval_service": "ok" if not retrieval_stats.get("error") else "error",
                "chat_service": "ok",
                "database": "ok"
            },
            "embeddings_count": embedding_stats.get("unique_articles", 0),
            "articles_count": retrieval_stats.get("total_articles", 0)
        }

        # Check if any component has errors
        if "error" in health_status["components"].values():
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Error in chat health check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )