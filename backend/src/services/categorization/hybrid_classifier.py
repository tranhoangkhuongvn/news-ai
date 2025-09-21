"""
Hybrid classifier that combines multiple classification methods.

This classifier combines keyword-based analysis with URL pattern matching
and provides fallback mechanisms for improved accuracy.
"""

import logging
from typing import Dict, List

from .base_classifier import BaseClassifier, ClassificationResult
from .keyword_classifier import KeywordClassifier
from .category_config import CONFIDENCE_THRESHOLDS
from src.models.news_model import NewsArticle

logger = logging.getLogger(__name__)

class HybridClassifier(BaseClassifier):
    """
    Hybrid classifier combining multiple classification approaches.

    Uses keyword analysis as primary method with URL pattern fallback
    and confidence-based decision making.
    """

    def __init__(self, confidence_threshold: float = None):
        """Initialize hybrid classifier."""
        super().__init__(confidence_threshold or CONFIDENCE_THRESHOLDS['hybrid'])

        # Initialize component classifiers
        self.keyword_classifier = KeywordClassifier()

        logger.info("Initialized HybridClassifier")

    def classify(self, article: NewsArticle) -> ClassificationResult:
        """
        Classify article using hybrid approach.

        Args:
            article: NewsArticle to classify

        Returns:
            ClassificationResult with best available classification
        """
        if not self.validate_article(article):
            return ClassificationResult(
                category='unknown',
                confidence=0.0,
                method_used='hybrid',
                explanation='Article content insufficient for classification',
                alternatives=[],
                features_used=[]
            )

        # Primary: Keyword-based classification
        keyword_result = self.keyword_classifier.classify(article)

        # If keyword classification is confident, use it
        if keyword_result.confidence >= self.confidence_threshold:
            # Update method used to indicate hybrid approach
            keyword_result.method_used = 'hybrid'
            keyword_result.explanation = f"Keyword analysis: {keyword_result.explanation}"
            return keyword_result

        # Secondary: Enhanced URL-based classification
        url_result = self._classify_by_url_enhanced(article)

        # Tertiary: Source-based heuristics
        source_result = self._classify_by_source_patterns(article)

        # Combine results using confidence weighting
        combined_result = self._combine_classifications([
            keyword_result,
            url_result,
            source_result
        ])

        # If still not confident enough, try fallback to original category
        if combined_result.confidence < self.confidence_threshold:
            fallback_result = self._fallback_classification(article)
            if fallback_result.confidence > combined_result.confidence:
                combined_result = fallback_result

        combined_result.method_used = 'hybrid'
        return combined_result

    def _classify_by_url_enhanced(self, article: NewsArticle) -> ClassificationResult:
        """Enhanced URL-based classification with pattern matching."""
        url = article.url.lower() if article.url else ""

        if not url:
            return ClassificationResult(
                category='unknown',
                confidence=0.0,
                method_used='url',
                explanation='No URL available',
                alternatives=[],
                features_used=[]
            )

        # Enhanced URL patterns with confidence scores
        url_patterns = {
            'sports': {
                'patterns': ['/sport/', '/sports/', '/afl/', '/nrl/', '/cricket/', '/tennis/', '/golf/', '/rugby/'],
                'confidence': 0.9
            },
            'finance': {
                'patterns': ['/business/', '/finance/', '/economy/', '/market/', '/asx/', '/shares/'],
                'confidence': 0.9
            },
            'lifestyle': {
                'patterns': ['/lifestyle/', '/health/', '/food/', '/travel/', '/fashion/', '/wellness/'],
                'confidence': 0.8
            },
            'music': {
                'patterns': ['/music/', '/entertainment/music/', '/arts/music/', '/concerts/'],
                'confidence': 0.8
            }
        }

        # Check for pattern matches
        for category, config in url_patterns.items():
            for pattern in config['patterns']:
                if pattern in url:
                    return ClassificationResult(
                        category=category,
                        confidence=config['confidence'],
                        method_used='url',
                        explanation=f"URL pattern match: '{pattern}'",
                        alternatives=[],
                        features_used=['url']
                    )

        # Check for partial matches (lower confidence)
        partial_patterns = {
            'sports': ['football', 'soccer', 'basketball', 'swimming'],
            'finance': ['money', 'banking', 'investment', 'trading'],
            'lifestyle': ['home', 'garden', 'family', 'relationships'],
            'music': ['band', 'artist', 'album', 'concert']
        }

        for category, patterns in partial_patterns.items():
            for pattern in patterns:
                if pattern in url:
                    return ClassificationResult(
                        category=category,
                        confidence=0.6,
                        method_used='url',
                        explanation=f"URL contains '{pattern}'",
                        alternatives=[],
                        features_used=['url']
                    )

        return ClassificationResult(
            category='unknown',
            confidence=0.0,
            method_used='url',
            explanation='No matching URL patterns',
            alternatives=[],
            features_used=[]
        )

    def _classify_by_source_patterns(self, article: NewsArticle) -> ClassificationResult:
        """Classification based on source publication patterns."""
        source = article.source.lower() if article.source else ""

        if not source:
            return ClassificationResult(
                category='unknown',
                confidence=0.0,
                method_used='source',
                explanation='No source information',
                alternatives=[],
                features_used=[]
            )

        # Source-specific category preferences (based on observed patterns)
        source_preferences = {
            'abc news': {
                'sports': 0.7,  # ABC has strong sports coverage
                'finance': 0.6,
                'lifestyle': 0.5,
                'music': 0.4
            },
            'the guardian au': {
                'lifestyle': 0.7,  # Guardian AU has strong lifestyle content
                'finance': 0.6,
                'music': 0.6,
                'sports': 0.5
            }
        }

        if source in source_preferences:
            preferences = source_preferences[source]
            best_category = max(preferences.items(), key=lambda x: x[1])

            return ClassificationResult(
                category=best_category[0],
                confidence=best_category[1] * 0.5,  # Reduce confidence for source-only classification
                method_used='source',
                explanation=f"Source pattern: {source} typically publishes {best_category[0]} content",
                alternatives=[(cat, conf * 0.5) for cat, conf in sorted(preferences.items(), key=lambda x: x[1], reverse=True)[1:]],
                features_used=['source']
            )

        return ClassificationResult(
            category='unknown',
            confidence=0.0,
            method_used='source',
            explanation='Unknown source pattern',
            alternatives=[],
            features_used=[]
        )

    def _combine_classifications(self, results: List[ClassificationResult]) -> ClassificationResult:
        """Combine multiple classification results using weighted voting."""
        if not results:
            return ClassificationResult(
                category='unknown',
                confidence=0.0,
                method_used='hybrid',
                explanation='No classification results to combine',
                alternatives=[],
                features_used=[]
            )

        # Filter out unknown results
        valid_results = [r for r in results if r.category != 'unknown' and r.confidence > 0]

        if not valid_results:
            return results[0]  # Return first result if none are valid

        # Weight the results based on method reliability
        method_weights = {
            'keyword': 1.0,
            'url': 0.8,
            'source': 0.3
        }

        # Calculate weighted scores for each category
        category_scores = {}
        total_weight = 0
        explanations = []
        all_features_used = set()

        for result in valid_results:
            weight = method_weights.get(result.method_used, 0.5)
            weighted_score = result.confidence * weight

            if result.category not in category_scores:
                category_scores[result.category] = 0

            category_scores[result.category] += weighted_score
            total_weight += weight

            if result.explanation:
                explanations.append(f"{result.method_used}: {result.explanation}")

            all_features_used.update(result.features_used)

        if not category_scores:
            return results[0]

        # Find best category
        best_category = max(category_scores.items(), key=lambda x: x[1])

        # Normalize confidence
        final_confidence = min(best_category[1] / total_weight, 1.0) if total_weight > 0 else 0.0

        # Generate alternatives
        alternatives = [
            (cat, min(score / total_weight, 1.0))
            for cat, score in sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[1:]
            if score > 0
        ]

        return ClassificationResult(
            category=best_category[0],
            confidence=final_confidence,
            method_used='hybrid',
            explanation='; '.join(explanations) if explanations else 'Combined analysis',
            alternatives=alternatives,
            features_used=list(all_features_used)
        )

    def _fallback_classification(self, article: NewsArticle) -> ClassificationResult:
        """Fallback classification for edge cases."""
        # Use the original category if available (from URL-based extraction)
        original_category = article.category.lower() if article.category else ""

        if original_category in self.SUPPORTED_CATEGORIES:
            return ClassificationResult(
                category=original_category,
                confidence=0.4,  # Low confidence for fallback
                method_used='fallback',
                explanation=f"Fallback to original category: {original_category}",
                alternatives=[],
                features_used=['original_category']
            )

        # Default to most common category based on current data
        return ClassificationResult(
            category='lifestyle',  # Most general category
            confidence=0.2,
            method_used='default',
            explanation='Default categorization - insufficient signals',
            alternatives=[],
            features_used=[]
        )

    def get_category_scores(self, article: NewsArticle) -> Dict[str, float]:
        """
        Get confidence scores for all categories using hybrid approach.

        Args:
            article: NewsArticle to analyze

        Returns:
            Dict mapping category names to confidence scores
        """
        if not self.validate_article(article):
            return {category: 0.0 for category in self.SUPPORTED_CATEGORIES}

        # Get scores from keyword classifier (most comprehensive)
        keyword_scores = self.keyword_classifier.get_category_scores(article)

        # Enhance with URL-based signals
        url_result = self._classify_by_url_enhanced(article)
        if url_result.category in keyword_scores and url_result.confidence > 0.7:
            # Boost score for URL-indicated category
            keyword_scores[url_result.category] = min(
                keyword_scores[url_result.category] + 0.2,
                1.0
            )

        return keyword_scores