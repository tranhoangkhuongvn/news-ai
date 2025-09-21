"""
Retrieval service for RAG chatbot
Handles context retrieval using hybrid search (semantic + keyword + recency)
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re

from src.services.chatbot.embedding_service import EmbeddingService
from src.db.database_conn import NewsDatabase

logger = logging.getLogger(__name__)

class RetrievalService:
    """Service for retrieving relevant articles for chatbot context"""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize retrieval service

        Args:
            embedding_service: Optional embedding service instance
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.db = NewsDatabase()

    def retrieve_context(self, query: str, max_articles: int = 5,
                        category_filter: Optional[str] = None,
                        days_back: int = 30) -> List[Dict]:
        """
        Retrieve relevant articles for a query using hybrid search

        Args:
            query: User's question or query
            max_articles: Maximum number of articles to return
            category_filter: Optional category to filter by
            days_back: How many days back to search for articles

        Returns:
            List of article dictionaries with relevance scores
        """
        try:
            logger.info(f"Retrieving context for query: '{query[:50]}...'")

            # Extract query information
            query_info = self._analyze_query(query)
            logger.debug(f"Query analysis: {query_info}")

            # Apply category filter from query if not provided
            if not category_filter and query_info.get('category'):
                category_filter = query_info['category']

            # 1. Semantic similarity search (primary method)
            semantic_results = self._semantic_search(
                query, max_articles * 2, category_filter
            )

            # 2. Keyword search (complementary)
            keyword_results = self._keyword_search(
                query, max_articles, category_filter, days_back
            )

            # 3. Recent articles (for time-sensitive queries)
            recent_results = []
            if query_info.get('time_sensitive'):
                recent_results = self._get_recent_articles(
                    max_articles // 2, category_filter, days_back=7
                )

            # 4. Merge and rank results
            merged_results = self._merge_and_rank_results(
                semantic_results, keyword_results, recent_results,
                query_info, max_articles
            )

            logger.info(f"Retrieved {len(merged_results)} relevant articles")
            return merged_results

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []

    def _analyze_query(self, query: str) -> Dict:
        """
        Analyze query to extract intent, category, and other metadata

        Args:
            query: User's query

        Returns:
            Dictionary with query analysis
        """
        query_lower = query.lower()

        # Category detection
        category_keywords = {
            'sports': ['sport', 'afl', 'nrl', 'rugby', 'cricket', 'tennis', 'football', 'soccer',
                      'basketball', 'olympics', 'grand final', 'match', 'game', 'team', 'player'],
            'finance': ['finance', 'economy', 'business', 'market', 'stock', 'asx', 'banking',
                       'investment', 'company', 'profit', 'revenue', 'gdp', 'inflation', 'rates'],
            'lifestyle': ['health', 'lifestyle', 'wellness', 'food', 'travel', 'culture',
                         'entertainment', 'celebrity', 'fashion', 'art', 'movie', 'book'],
            'music': ['music', 'album', 'song', 'artist', 'concert', 'festival', 'band',
                     'singer', 'musician', 'tour', 'record']
        }

        detected_category = None
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_category = category
                break

        # Time sensitivity detection
        time_keywords = ['today', 'latest', 'recent', 'breaking', 'now', 'current',
                        'this week', 'yesterday', 'happening', 'update']
        time_sensitive = any(keyword in query_lower for keyword in time_keywords)

        # Question type detection
        question_types = {
            'what': ['what', 'which'],
            'when': ['when', 'time'],
            'where': ['where', 'location'],
            'who': ['who', 'person'],
            'why': ['why', 'reason'],
            'how': ['how', 'method']
        }

        question_type = None
        for q_type, keywords in question_types.items():
            if any(keyword in query_lower for keyword in keywords):
                question_type = q_type
                break

        return {
            'category': detected_category,
            'time_sensitive': time_sensitive,
            'question_type': question_type,
            'original_query': query
        }

    def _semantic_search(self, query: str, limit: int,
                        category_filter: Optional[str] = None) -> List[Dict]:
        """
        Perform semantic similarity search using embeddings

        Args:
            query: Search query
            limit: Maximum number of results
            category_filter: Optional category filter

        Returns:
            List of articles with similarity scores
        """
        try:
            results = self.embedding_service.find_similar_articles(
                query, limit, category_filter
            )

            # Add result source
            for result in results:
                result['retrieval_method'] = 'semantic'
                result['relevance_score'] = result['similarity_score']

            return results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def _keyword_search(self, query: str, limit: int,
                       category_filter: Optional[str] = None,
                       days_back: int = 30) -> List[Dict]:
        """
        Perform keyword-based search on article titles and content

        Args:
            query: Search query
            limit: Maximum number of results
            category_filter: Optional category filter
            days_back: How many days back to search

        Returns:
            List of articles with keyword relevance scores
        """
        try:
            import sqlite3

            # Extract keywords from query
            keywords = self._extract_keywords(query)
            if not keywords:
                return []

            # Build search conditions
            search_conditions = []
            search_params = []

            # Create LIKE conditions for keywords
            for keyword in keywords:
                search_conditions.append(
                    "(LOWER(title) LIKE ? OR LOWER(summary) LIKE ? OR LOWER(content) LIKE ?)"
                )
                keyword_pattern = f"%{keyword.lower()}%"
                search_params.extend([keyword_pattern, keyword_pattern, keyword_pattern])

            # Add category filter
            if category_filter:
                search_conditions.append("category = ?")
                search_params.append(category_filter)

            # Add date filter
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            search_conditions.append("created_at >= ?")
            search_params.append(cutoff_date)

            # Build SQL query
            where_clause = " AND ".join(search_conditions)
            sql = f"""
                SELECT id, title, summary, category, source, url, created_at
                FROM articles
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """
            search_params.append(limit)

            with sqlite3.connect(self.db.db_path, timeout=30.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql, search_params)

                results = []
                for row in cursor.fetchall():
                    article = dict(row)

                    # Calculate keyword relevance score
                    relevance_score = self._calculate_keyword_relevance(
                        keywords, article['title'], article['summary']
                    )

                    article['retrieval_method'] = 'keyword'
                    article['relevance_score'] = relevance_score
                    results.append(article)

                return results

        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []

    def _get_recent_articles(self, limit: int,
                           category_filter: Optional[str] = None,
                           days_back: int = 7) -> List[Dict]:
        """
        Get most recent articles

        Args:
            limit: Maximum number of results
            category_filter: Optional category filter
            days_back: How many days back to search

        Returns:
            List of recent articles
        """
        try:
            import sqlite3

            # Build query
            params = []
            conditions = []

            if category_filter:
                conditions.append("category = ?")
                params.append(category_filter)

            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff_date)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            sql = f"""
                SELECT id, title, summary, category, source, url, created_at
                FROM articles
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params.append(limit)

            with sqlite3.connect(self.db.db_path, timeout=30.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql, params)

                results = []
                for row in cursor.fetchall():
                    article = dict(row)
                    article['retrieval_method'] = 'recent'
                    article['relevance_score'] = 0.7  # Base score for recent articles
                    results.append(article)

                return results

        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from query

        Args:
            query: Input query

        Returns:
            List of keywords
        """
        # Remove common stop words
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'what', 'when', 'where', 'who', 'why',
            'how', 'tell', 'me', 'about', 'can', 'you', 'i', 'do', 'did'
        }

        # Split and clean words
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords[:10]  # Limit to 10 keywords

    def _calculate_keyword_relevance(self, keywords: List[str],
                                   title: str, summary: str) -> float:
        """
        Calculate relevance score based on keyword matches

        Args:
            keywords: List of search keywords
            title: Article title
            summary: Article summary

        Returns:
            Relevance score between 0 and 1
        """
        if not keywords:
            return 0.0

        title_lower = title.lower() if title else ""
        summary_lower = summary.lower() if summary else ""

        score = 0.0
        total_keywords = len(keywords)

        for keyword in keywords:
            # Title matches are weighted higher
            if keyword in title_lower:
                score += 0.6

            # Summary matches
            if keyword in summary_lower:
                score += 0.4

        # Normalize by number of keywords
        return min(score / total_keywords, 1.0)

    def _merge_and_rank_results(self, semantic_results: List[Dict],
                               keyword_results: List[Dict],
                               recent_results: List[Dict],
                               query_info: Dict,
                               max_articles: int) -> List[Dict]:
        """
        Merge and rank results from different search methods

        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            recent_results: Results from recent articles
            query_info: Query analysis information
            max_articles: Maximum articles to return

        Returns:
            List of ranked and merged articles
        """
        try:
            # Combine all results
            all_results = {}

            # Add semantic results (primary)
            for result in semantic_results:
                article_id = result['id']
                result['final_score'] = result['relevance_score'] * 0.7  # 70% weight
                all_results[article_id] = result

            # Add keyword results (complementary)
            for result in keyword_results:
                article_id = result['id']
                if article_id in all_results:
                    # Boost existing results that also match keywords
                    all_results[article_id]['final_score'] += result['relevance_score'] * 0.2
                    all_results[article_id]['retrieval_method'] = 'semantic+keyword'
                else:
                    result['final_score'] = result['relevance_score'] * 0.5  # 50% weight for keyword-only
                    all_results[article_id] = result

            # Add recent results (for time-sensitive queries)
            if query_info.get('time_sensitive'):
                for result in recent_results:
                    article_id = result['id']
                    if article_id in all_results:
                        # Boost recent articles for time-sensitive queries
                        all_results[article_id]['final_score'] += 0.2
                        all_results[article_id]['retrieval_method'] += '+recent'
                    else:
                        result['final_score'] = result['relevance_score'] * 0.4
                        all_results[article_id] = result

            # Sort by final score and return top results
            ranked_results = list(all_results.values())
            ranked_results.sort(key=lambda x: x['final_score'], reverse=True)

            return ranked_results[:max_articles]

        except Exception as e:
            logger.error(f"Error merging and ranking results: {e}")
            return []

    def get_retrieval_stats(self) -> Dict:
        """Get statistics about the retrieval system"""
        try:
            embedding_stats = self.embedding_service.get_embedding_stats()

            import sqlite3
            with sqlite3.connect(self.db.db_path, timeout=30.0) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM articles")
                total_articles = cursor.fetchone()[0]

                # Get articles by category
                cursor = conn.execute("""
                    SELECT category, COUNT(*) as count
                    FROM articles
                    GROUP BY category
                """)
                category_counts = dict(cursor.fetchall())

            return {
                'total_articles': total_articles,
                'articles_with_embeddings': embedding_stats.get('unique_articles', 0),
                'embedding_coverage': embedding_stats.get('unique_articles', 0) / max(total_articles, 1),
                'category_counts': category_counts,
                'embedding_model': embedding_stats.get('model_name', 'unknown')
            }

        except Exception as e:
            logger.error(f"Error getting retrieval stats: {e}")
            return {'error': str(e)}