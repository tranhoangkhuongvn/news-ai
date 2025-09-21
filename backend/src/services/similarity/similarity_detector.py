"""
Core similarity detection engine for news articles.

This module implements the main algorithm for detecting similar news articles
across different sources using title similarity, keyword overlap, and time proximity.
"""

import logging
from difflib import SequenceMatcher
from typing import List, Dict, Set, Tuple
from datetime import datetime

from src.models.news_model import NewsArticle
from .text_utils import clean_title, extract_keywords, calculate_time_similarity
from .similarity_models import SimilarityResult

logger = logging.getLogger(__name__)

class SimilarityDetector:
    """
    Detects similar news articles using a hybrid approach combining:
    - Title similarity (60% weight)
    - Keyword overlap (25% weight)
    - Time proximity (15% weight)
    """

    def __init__(self,
                 similarity_threshold: float = 0.7,
                 title_weight: float = 0.6,
                 keyword_weight: float = 0.25,
                 time_weight: float = 0.15):
        """
        Initialize the similarity detector.

        Args:
            similarity_threshold: Minimum score to consider articles similar
            title_weight: Weight for title similarity in final score
            keyword_weight: Weight for keyword overlap in final score
            time_weight: Weight for time proximity in final score
        """
        self.similarity_threshold = similarity_threshold
        self.title_weight = title_weight
        self.keyword_weight = keyword_weight
        self.time_weight = time_weight

        # Ensure weights sum to 1.0
        total_weight = title_weight + keyword_weight + time_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Similarity weights don't sum to 1.0 (sum={total_weight}), normalizing...")
            self.title_weight = title_weight / total_weight
            self.keyword_weight = keyword_weight / total_weight
            self.time_weight = time_weight / total_weight

        logger.info(f"Initialized SimilarityDetector with threshold={similarity_threshold}")

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two article titles.

        Args:
            title1: First article title
            title2: Second article title

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not title1 or not title2:
            return 0.0

        # Clean and normalize titles
        clean1 = clean_title(title1)
        clean2 = clean_title(title2)

        if not clean1 or not clean2:
            return 0.0

        # Use fuzzy string matching
        similarity = SequenceMatcher(None, clean1, clean2).ratio()

        # Boost score if titles share significant words
        words1 = set(clean1.split())
        words2 = set(clean2.split())

        if len(words1) > 0 and len(words2) > 0:
            overlap = len(words1 & words2)
            max_words = max(len(words1), len(words2))
            word_overlap_bonus = (overlap / max_words) * 0.2  # Up to 20% bonus

            similarity = min(1.0, similarity + word_overlap_bonus)

        return similarity

    def calculate_keyword_similarity(self, article1: NewsArticle, article2: NewsArticle) -> float:
        """
        Calculate keyword-based similarity between two articles.

        Args:
            article1: First news article
            article2: Second news article

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Extract keywords from title, summary, and tags
        text1 = f"{article1.title} {article1.summary} {' '.join(article1.tags)}"
        text2 = f"{article2.title} {article2.summary} {' '.join(article2.tags)}"

        keywords1 = extract_keywords(text1)
        keywords2 = extract_keywords(text2)

        if not keywords1 or not keywords2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)

        jaccard_similarity = intersection / union if union > 0 else 0.0

        # Boost score for category match
        category_bonus = 0.0
        if article1.category == article2.category:
            category_bonus = 0.1  # 10% bonus for same category

        return min(1.0, jaccard_similarity + category_bonus)

    def calculate_overall_similarity(self, article1: NewsArticle, article2: NewsArticle) -> SimilarityResult:
        """
        Calculate overall similarity between two articles using all factors.

        Args:
            article1: First news article
            article2: Second news article

        Returns:
            SimilarityResult with detailed scoring breakdown
        """
        # Calculate individual similarity components
        title_sim = self.calculate_title_similarity(article1.title, article2.title)
        keyword_sim = self.calculate_keyword_similarity(article1, article2)
        time_sim = calculate_time_similarity(article1.published_date, article2.published_date)

        # Calculate weighted overall similarity
        overall_similarity = (
            title_sim * self.title_weight +
            keyword_sim * self.keyword_weight +
            time_sim * self.time_weight
        )

        # Generate explanation
        explanation = self._generate_explanation(title_sim, keyword_sim, time_sim, overall_similarity)

        return SimilarityResult(
            article_id_1=getattr(article1, 'id', 0),
            article_id_2=getattr(article2, 'id', 0),
            similarity_score=overall_similarity,
            title_similarity=title_sim,
            keyword_similarity=keyword_sim,
            time_similarity=time_sim,
            method_used="hybrid_weighted",
            explanation=explanation
        )

    def find_similar_articles(self, target_article: NewsArticle,
                            candidate_articles: List[NewsArticle],
                            max_results: int = 10) -> List[SimilarityResult]:
        """
        Find articles similar to the target article from a list of candidates.

        Args:
            target_article: Article to find similarities for
            candidate_articles: List of articles to compare against
            max_results: Maximum number of similar articles to return

        Returns:
            List of similarity results, sorted by similarity score (descending)
        """
        similarities = []

        for candidate in candidate_articles:
            # Skip self-comparison
            if (hasattr(target_article, 'id') and hasattr(candidate, 'id') and
                target_article.id == candidate.id):
                continue

            # Skip articles from the same source (different perspective on same story)
            if target_article.source == candidate.source:
                continue

            similarity = self.calculate_overall_similarity(target_article, candidate)

            # Only include articles above threshold
            if similarity.similarity_score >= self.similarity_threshold:
                similarities.append(similarity)

        # Sort by similarity score (descending) and limit results
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities[:max_results]

    def batch_similarity_detection(self, articles: List[NewsArticle]) -> List[SimilarityResult]:
        """
        Detect all similar article pairs in a batch of articles.

        Args:
            articles: List of articles to analyze

        Returns:
            List of all similarity results above threshold
        """
        similarities = []
        total_comparisons = 0

        logger.info(f"Starting batch similarity detection for {len(articles)} articles")

        for i, article1 in enumerate(articles):
            # Compare with articles that come after in the list (avoid duplicates)
            for j, article2 in enumerate(articles[i+1:], i+1):
                total_comparisons += 1

                # Skip same source comparisons
                if article1.source == article2.source:
                    continue

                similarity = self.calculate_overall_similarity(article1, article2)

                if similarity.similarity_score >= self.similarity_threshold:
                    similarities.append(similarity)

        logger.info(f"Completed {total_comparisons} comparisons, found {len(similarities)} similar pairs")
        return similarities

    def _generate_explanation(self, title_sim: float, keyword_sim: float,
                            time_sim: float, overall_sim: float) -> str:
        """
        Generate human-readable explanation of similarity scoring.

        Args:
            title_sim: Title similarity score
            keyword_sim: Keyword similarity score
            time_sim: Time similarity score
            overall_sim: Overall similarity score

        Returns:
            Explanation string
        """
        explanations = []

        # Title similarity explanation
        if title_sim > 0.8:
            explanations.append("very similar headlines")
        elif title_sim > 0.6:
            explanations.append("similar headlines")
        elif title_sim > 0.4:
            explanations.append("somewhat similar headlines")

        # Keyword overlap explanation
        if keyword_sim > 0.7:
            explanations.append("high keyword overlap")
        elif keyword_sim > 0.4:
            explanations.append("moderate keyword overlap")

        # Time proximity explanation
        if time_sim > 0.8:
            explanations.append("published around the same time")
        elif time_sim > 0.4:
            explanations.append("published within a similar timeframe")

        if not explanations:
            explanations.append("low overall similarity")

        base_explanation = ", ".join(explanations)

        if overall_sim > 0.8:
            return f"High similarity due to {base_explanation}"
        elif overall_sim > 0.6:
            return f"Moderate similarity due to {base_explanation}"
        else:
            return f"Low similarity based on {base_explanation}"