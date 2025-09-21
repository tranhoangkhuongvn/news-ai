"""
Business logic service for similarity detection and management.

This service coordinates similarity detection, clustering, and data persistence.
"""

import logging
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from src.models.news_model import NewsArticle
from src.db.database_conn import NewsDatabase
from .similarity_detector import SimilarityDetector
from .similarity_models import SimilarityResult, ArticleCluster, SimilarityMetrics

logger = logging.getLogger(__name__)

class SimilarityService:
    """
    High-level service for managing news article similarity detection.
    """

    def __init__(self, database: Optional[NewsDatabase] = None):
        """
        Initialize the similarity service.

        Args:
            database: Database connection (creates new if None)
        """
        self.db = database or NewsDatabase()
        self.detector = SimilarityDetector()
        logger.info("Initialized SimilarityService")

    def find_similar_articles(self, article_id: int, limit: int = 5) -> List[Dict]:
        """
        Find articles similar to the specified article.

        Args:
            article_id: ID of the target article
            limit: Maximum number of similar articles to return

        Returns:
            List of similar articles with similarity scores
        """
        try:
            # Get the target article
            target_article = self._get_article_by_id(article_id)
            if not target_article:
                return []

            # Get candidate articles (recent articles from different sources)
            candidates = self._get_candidate_articles(target_article)
            if not candidates:
                return []

            # Find similar articles
            similarities = self.detector.find_similar_articles(
                target_article, candidates, max_results=limit
            )

            # Convert to response format
            result = []
            for similarity in similarities:
                similar_article = self._get_article_by_id(similarity.article_id_2)
                if similar_article:
                    result.append({
                        'article': self._article_to_dict(similar_article),
                        'similarity_score': similarity.similarity_score,
                        'explanation': similarity.explanation
                    })

            logger.info(f"Found {len(result)} similar articles for article {article_id}")
            return result

        except Exception as e:
            logger.error(f"Error finding similar articles for {article_id}: {e}")
            return []

    def detect_all_similarities(self, hours_back: int = 48) -> SimilarityMetrics:
        """
        Detect similarities among recent articles and store results.

        Args:
            hours_back: How many hours back to analyze articles

        Returns:
            Metrics about the similarity detection process
        """
        start_time = time.time()
        logger.info(f"Starting similarity detection for articles from last {hours_back} hours")

        try:
            # Get recent articles
            articles = self._get_recent_articles(hours_back)
            if len(articles) < 2:
                logger.info("Not enough articles for similarity detection")
                return SimilarityMetrics(0, 0, 0, 0.0, 0.0)

            # Detect similarities
            similarities = self.detector.batch_similarity_detection(articles)

            # Store similarity results
            stored_count = self._store_similarities(similarities)

            # Create clusters
            clusters = self._create_article_clusters(similarities)

            # Calculate metrics
            processing_time = time.time() - start_time
            avg_score = sum(s.similarity_score for s in similarities) / len(similarities) if similarities else 0.0

            metrics = SimilarityMetrics(
                total_comparisons=len(articles) * (len(articles) - 1) // 2,
                similar_pairs_found=len(similarities),
                clusters_created=len(clusters),
                average_similarity_score=avg_score,
                processing_time=processing_time
            )

            logger.info(f"Similarity detection completed: {metrics.similar_pairs_found} pairs found, "
                       f"{metrics.clusters_created} clusters created in {processing_time:.2f}s")

            return metrics

        except Exception as e:
            logger.error(f"Error in similarity detection: {e}")
            return SimilarityMetrics(0, 0, 0, 0.0, time.time() - start_time)

    def get_article_clusters(self, limit: int = 10) -> List[Dict]:
        """
        Get clusters of similar articles grouped by story.

        Args:
            limit: Maximum number of clusters to return

        Returns:
            List of article clusters with metadata
        """
        try:
            # Get recent similarities
            similarities = self._get_stored_similarities(limit * 3)  # Get more to create clusters

            # Create clusters
            clusters = self._create_article_clusters(similarities)

            # Convert to response format
            result = []
            for cluster in clusters[:limit]:
                cluster_data = {
                    'cluster_id': cluster.cluster_id,
                    'main_article': self._article_to_dict(self._get_article_by_id(cluster.main_article_id)),
                    'similar_articles': [],
                    'summary': cluster.summary,
                    'sources_covered': cluster.sources_covered,
                    'article_count': cluster.article_count,
                    'cluster_score': cluster.cluster_score
                }

                # Add similar articles
                for article_id in cluster.similar_articles:
                    article = self._get_article_by_id(article_id)
                    if article:
                        cluster_data['similar_articles'].append(self._article_to_dict(article))

                result.append(cluster_data)

            logger.info(f"Retrieved {len(result)} article clusters")
            return result

        except Exception as e:
            logger.error(f"Error getting article clusters: {e}")
            return []

    def _get_article_by_id(self, article_id: int) -> Optional[NewsArticle]:
        """Convert database article to NewsArticle object."""
        import sqlite3
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
                row = cursor.fetchone()

                if row:
                    import json
                    article_dict = dict(row)
                    tags = json.loads(article_dict.get('tags', '[]')) if article_dict.get('tags') else []

                    article = NewsArticle(
                        title=article_dict.get('title', ''),
                        url=article_dict.get('url', ''),
                        category=article_dict.get('category', ''),
                        summary=article_dict.get('summary', ''),
                        published_date=article_dict.get('published_date', ''),
                        author=article_dict.get('author', ''),
                        content=article_dict.get('content', ''),
                        source=article_dict.get('source', ''),
                        tags=tags,
                        extracted_at=article_dict.get('extracted_at', '')
                    )
                    # Add ID for similarity comparison
                    article.id = article_dict['id']
                    return article

        except Exception as e:
            logger.error(f"Error getting article {article_id}: {e}")

        return None

    def _get_candidate_articles(self, target_article: NewsArticle, limit: int = 50) -> List[NewsArticle]:
        """Get candidate articles for similarity comparison."""
        try:
            # Get recent articles from different sources
            articles = self.db.get_articles(limit=limit)
            candidates = []

            for article_dict in articles:
                if article_dict.get('source') != target_article.source:  # Different source
                    article = self._dict_to_article(article_dict)
                    if article:
                        candidates.append(article)

            return candidates

        except Exception as e:
            logger.error(f"Error getting candidate articles: {e}")
            return []

    def _get_recent_articles(self, hours_back: int) -> List[NewsArticle]:
        """Get recent articles for similarity analysis."""
        try:
            # Get more articles to ensure we have enough after filtering
            articles = self.db.get_articles(limit=100)
            result = []

            for article_dict in articles:
                article = self._dict_to_article(article_dict)
                if article:
                    result.append(article)

            return result

        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []

    def _dict_to_article(self, article_dict: Dict) -> Optional[NewsArticle]:
        """Convert database dict to NewsArticle object."""
        try:
            import json
            tags = json.loads(article_dict.get('tags', '[]')) if article_dict.get('tags') else []

            article = NewsArticle(
                title=article_dict.get('title', ''),
                url=article_dict.get('url', ''),
                category=article_dict.get('category', ''),
                summary=article_dict.get('summary', ''),
                published_date=article_dict.get('published_date', ''),
                author=article_dict.get('author', ''),
                content=article_dict.get('content', ''),
                source=article_dict.get('source', ''),
                tags=tags,
                extracted_at=article_dict.get('extracted_at', '')
            )
            # Add ID for similarity comparison
            article.id = article_dict['id']
            return article

        except Exception as e:
            logger.error(f"Error converting dict to article: {e}")
            return None

    def _article_to_dict(self, article: NewsArticle) -> Dict:
        """Convert NewsArticle to dictionary for API response."""
        return {
            'id': getattr(article, 'id', 0),
            'title': article.title,
            'url': article.url,
            'category': article.category,
            'summary': article.summary,
            'published_date': article.published_date,
            'author': article.author,
            'source': article.source,
            'tags': article.tags
        }

    def _store_similarities(self, similarities: List[SimilarityResult]) -> int:
        """Store similarity results in database (placeholder for now)."""
        # TODO: Implement database storage when similarity table is added
        logger.info(f"Would store {len(similarities)} similarity results")
        return len(similarities)

    def _get_stored_similarities(self, limit: int) -> List[SimilarityResult]:
        """Get stored similarity results (placeholder for now)."""
        # TODO: Implement when similarity table is added
        return []

    def _create_article_clusters(self, similarities: List[SimilarityResult]) -> List[ArticleCluster]:
        """Create clusters of similar articles."""
        clusters = []
        processed_articles = set()

        for similarity in similarities:
            if similarity.article_id_1 in processed_articles or similarity.article_id_2 in processed_articles:
                continue

            # Create a new cluster
            main_article = self._get_article_by_id(similarity.article_id_1)
            similar_article = self._get_article_by_id(similarity.article_id_2)

            if main_article and similar_article:
                cluster = ArticleCluster(
                    cluster_id=f"cluster_{len(clusters) + 1}_{int(time.time())}",
                    main_article_id=similarity.article_id_1,
                    similar_articles=[similarity.article_id_2],
                    cluster_score=similarity.similarity_score,
                    created_at=datetime.now(),
                    summary=f"Similar coverage of: {main_article.title[:50]}...",
                    sources_covered=[main_article.source, similar_article.source]
                )

                clusters.append(cluster)
                processed_articles.add(similarity.article_id_1)
                processed_articles.add(similarity.article_id_2)

        return clusters