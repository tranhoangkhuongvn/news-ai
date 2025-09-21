"""
Base classification framework for news article categorization.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Optional
import logging

from src.models.news_model import NewsArticle

logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    """Result of article classification with confidence and explanation."""

    category: str
    confidence: float  # 0.0 to 1.0
    method_used: str
    explanation: str
    alternatives: List[Tuple[str, float]]  # [(category, confidence), ...]
    features_used: List[str]  # Which features contributed to classification

    def __post_init__(self):
        """Validate classification result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

        # Sort alternatives by confidence (descending)
        self.alternatives.sort(key=lambda x: x[1], reverse=True)

class BaseClassifier(ABC):
    """Abstract base class for news article classifiers."""

    SUPPORTED_CATEGORIES = ['sports', 'lifestyle', 'music', 'finance']
    MIN_CONFIDENCE_THRESHOLD = 0.5

    def __init__(self, confidence_threshold: float = None):
        """
        Initialize classifier.

        Args:
            confidence_threshold: Minimum confidence required for classification
        """
        self.confidence_threshold = confidence_threshold or self.MIN_CONFIDENCE_THRESHOLD
        logger.info(f"Initialized {self.__class__.__name__} with confidence threshold {self.confidence_threshold}")

    @abstractmethod
    def classify(self, article: NewsArticle) -> ClassificationResult:
        """
        Classify an article into one of the supported categories.

        Args:
            article: NewsArticle to classify

        Returns:
            ClassificationResult with category, confidence, and explanation
        """
        pass

    def is_classification_confident(self, result: ClassificationResult) -> bool:
        """Check if classification meets confidence threshold."""
        return result.confidence >= self.confidence_threshold

    def get_category_scores(self, article: NewsArticle) -> dict:
        """
        Get confidence scores for all categories.

        Args:
            article: NewsArticle to analyze

        Returns:
            Dict mapping category names to confidence scores
        """
        # Default implementation - subclasses should override for efficiency
        scores = {}
        for category in self.SUPPORTED_CATEGORIES:
            # This is inefficient but works as fallback
            try:
                result = self.classify(article)
                if result.category == category:
                    scores[category] = result.confidence
                else:
                    # Look in alternatives
                    for alt_cat, alt_conf in result.alternatives:
                        if alt_cat == category:
                            scores[category] = alt_conf
                            break
                    else:
                        scores[category] = 0.0
            except Exception as e:
                logger.warning(f"Error getting score for category {category}: {e}")
                scores[category] = 0.0

        return scores

    def validate_article(self, article: NewsArticle) -> bool:
        """
        Validate that article has sufficient content for classification.

        Args:
            article: NewsArticle to validate

        Returns:
            True if article is suitable for classification
        """
        if not article.title or len(article.title.strip()) < 3:
            logger.debug("Article title too short for classification")
            return False

        if not article.content or len(article.content.strip()) < 50:
            logger.debug("Article content too short for classification")
            return False

        return True

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for classification.

        Args:
            text: Raw text to preprocess

        Returns:
            Preprocessed text
        """
        if not text:
            return ""

        # Basic preprocessing
        text = text.lower()
        text = text.strip()

        # Remove extra whitespace
        import re
        text = re.sub(r'\s+', ' ', text)

        return text

    def extract_features(self, article: NewsArticle) -> dict:
        """
        Extract features from article for classification.

        Args:
            article: NewsArticle to extract features from

        Returns:
            Dict of feature names to values
        """
        features = {
            'title': self.preprocess_text(article.title),
            'summary': self.preprocess_text(article.summary),
            'content': self.preprocess_text(article.content),
            'url': article.url.lower() if article.url else "",
            'tags': [tag.lower() for tag in article.tags] if article.tags else [],
            'source': article.source.lower() if article.source else "",
            'word_count': len(article.content.split()) if article.content else 0,
            'title_word_count': len(article.title.split()) if article.title else 0
        }

        return features