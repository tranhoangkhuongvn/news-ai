"""
Embedding service for RAG chatbot
Handles text embeddings using sentence-transformers
"""

import logging
from typing import List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.db.database_conn import NewsDatabase
from src.models.news_model import NewsArticle

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for handling text embeddings and similarity search"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service

        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.db = NewsDatabase()

    def _load_model(self):
        """Lazy load the sentence transformer model"""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            try:
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Successfully loaded model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {self.model_name}: {e}")
                raise
        return self.model

    def create_text_embedding(self, text: str) -> List[float]:
        """
        Create embedding for a text string

        Args:
            text: Input text to embed

        Returns:
            List of float values representing the embedding
        """
        try:
            model = self._load_model()

            # Clean and prepare text
            cleaned_text = self._clean_text(text)

            # Generate embedding
            embedding = model.encode(cleaned_text, convert_to_tensor=False)

            # Convert to list for JSON serialization
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Error creating embedding for text: {e}")
            return []

    def create_article_embedding(self, article: NewsArticle) -> List[float]:
        """
        Create embedding for a news article

        Args:
            article: NewsArticle object

        Returns:
            List of float values representing the embedding
        """
        try:
            # Combine title, summary, and beginning of content for embedding
            content_preview = article.content[:500] if article.content else ""

            combined_text = f"""
            Title: {article.title}
            Category: {article.category}
            Source: {article.source}
            Summary: {article.summary}
            Content: {content_preview}
            Tags: {', '.join(article.tags) if article.tags else ''}
            """.strip()

            return self.create_text_embedding(combined_text)

        except Exception as e:
            logger.error(f"Error creating embedding for article {article.title}: {e}")
            return []

    def embed_and_store_article(self, article: NewsArticle, article_id: int) -> bool:
        """
        Create embedding for article and store it in database

        Args:
            article: NewsArticle object
            article_id: Database ID of the article

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if embedding already exists
            existing_embedding = self.db.get_article_embedding(article_id, self.model_name)
            if existing_embedding:
                logger.debug(f"Embedding already exists for article {article_id}")
                return True

            # Create new embedding
            embedding = self.create_article_embedding(article)
            if not embedding:
                logger.error(f"Failed to create embedding for article {article_id}")
                return False

            # Store in database
            success = self.db.save_article_embedding(article_id, embedding, self.model_name)
            if success:
                logger.info(f"Successfully stored embedding for article {article_id}")
            else:
                logger.error(f"Failed to store embedding for article {article_id}")

            return success

        except Exception as e:
            logger.error(f"Error embedding and storing article {article_id}: {e}")
            return False

    def embed_articles_batch(self, articles_with_ids: List[Tuple[NewsArticle, int]],
                           batch_size: int = 10) -> int:
        """
        Embed multiple articles in batches

        Args:
            articles_with_ids: List of (NewsArticle, article_id) tuples
            batch_size: Number of articles to process at once

        Returns:
            Number of successfully processed articles
        """
        success_count = 0
        total_articles = len(articles_with_ids)

        logger.info(f"Starting batch embedding of {total_articles} articles")

        for i in range(0, total_articles, batch_size):
            batch = articles_with_ids[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_articles + batch_size - 1)//batch_size}")

            for article, article_id in batch:
                if self.embed_and_store_article(article, article_id):
                    success_count += 1

        logger.info(f"Completed batch embedding: {success_count}/{total_articles} successful")
        return success_count

    def find_similar_articles(self, query_text: str, limit: int = 5,
                            category_filter: Optional[str] = None) -> List[dict]:
        """
        Find articles similar to query text

        Args:
            query_text: Text to search for
            limit: Maximum number of results to return
            category_filter: Optional category to filter by

        Returns:
            List of article dictionaries with similarity scores
        """
        try:
            # Create embedding for query
            query_embedding = self.create_text_embedding(query_text)
            if not query_embedding:
                logger.error("Failed to create query embedding")
                return []

            # Get all articles with embeddings from database
            articles_with_embeddings = self._get_articles_with_embeddings(category_filter)

            if not articles_with_embeddings:
                logger.warning("No articles with embeddings found")
                return []

            # Calculate similarities
            similarities = self._calculate_similarities(query_embedding, articles_with_embeddings)

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)

            return similarities[:limit]

        except Exception as e:
            logger.error(f"Error finding similar articles: {e}")
            return []

    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for embedding"""
        if not text:
            return ""

        # Basic text cleaning
        cleaned = text.strip()

        # Remove excessive whitespace
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned

    def _get_articles_with_embeddings(self, category_filter: Optional[str] = None) -> List[dict]:
        """Get articles that have embeddings from database"""
        try:
            import sqlite3
            import json

            with sqlite3.connect(self.db.db_path, timeout=30.0) as conn:
                conn.row_factory = sqlite3.Row

                if category_filter:
                    cursor = conn.execute("""
                        SELECT a.id, a.title, a.summary, a.category, a.source, a.url,
                               ae.embedding_vector
                        FROM articles a
                        JOIN article_embeddings ae ON a.id = ae.article_id
                        WHERE ae.embedding_model = ? AND a.category = ?
                        ORDER BY a.created_at DESC
                    """, (self.model_name, category_filter))
                else:
                    cursor = conn.execute("""
                        SELECT a.id, a.title, a.summary, a.category, a.source, a.url,
                               ae.embedding_vector
                        FROM articles a
                        JOIN article_embeddings ae ON a.id = ae.article_id
                        WHERE ae.embedding_model = ?
                        ORDER BY a.created_at DESC
                    """, (self.model_name,))

                articles = []
                for row in cursor.fetchall():
                    article_dict = dict(row)
                    article_dict['embedding'] = json.loads(article_dict['embedding_vector'])
                    del article_dict['embedding_vector']  # Remove raw JSON
                    articles.append(article_dict)

                return articles

        except Exception as e:
            logger.error(f"Error getting articles with embeddings: {e}")
            return []

    def _calculate_similarities(self, query_embedding: List[float],
                              articles_with_embeddings: List[dict]) -> List[dict]:
        """Calculate cosine similarities between query and articles"""
        try:
            # Convert query embedding to numpy array
            query_array = np.array(query_embedding).reshape(1, -1)

            similarities = []

            for article in articles_with_embeddings:
                try:
                    # Convert article embedding to numpy array
                    article_embedding = np.array(article['embedding']).reshape(1, -1)

                    # Calculate cosine similarity
                    similarity = cosine_similarity(query_array, article_embedding)[0][0]

                    # Add to results
                    result = {
                        'id': article['id'],
                        'title': article['title'],
                        'summary': article['summary'],
                        'category': article['category'],
                        'source': article['source'],
                        'url': article['url'],
                        'similarity_score': float(similarity)
                    }

                    similarities.append(result)

                except Exception as e:
                    logger.warning(f"Error calculating similarity for article {article.get('id')}: {e}")
                    continue

            return similarities

        except Exception as e:
            logger.error(f"Error calculating similarities: {e}")
            return []

    def get_embedding_stats(self) -> dict:
        """Get statistics about stored embeddings"""
        try:
            import sqlite3

            with sqlite3.connect(self.db.db_path, timeout=30.0) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_embeddings,
                        COUNT(DISTINCT article_id) as unique_articles,
                        embedding_model
                    FROM article_embeddings
                    WHERE embedding_model = ?
                    GROUP BY embedding_model
                """, (self.model_name,))

                result = cursor.fetchone()
                if result:
                    return {
                        'total_embeddings': result[0],
                        'unique_articles': result[1],
                        'model_name': result[2]
                    }
                else:
                    return {
                        'total_embeddings': 0,
                        'unique_articles': 0,
                        'model_name': self.model_name
                    }

        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {'error': str(e)}