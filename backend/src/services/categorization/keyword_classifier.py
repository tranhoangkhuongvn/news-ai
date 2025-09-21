"""
Keyword-based article classifier using weighted term matching.

This classifier analyzes article content, title, and metadata to classify articles
based on predefined keyword dictionaries with confidence scoring.
"""

import logging
import re
from typing import Dict, List, Tuple
from collections import defaultdict

from .base_classifier import BaseClassifier, ClassificationResult
from .category_config import (
    CATEGORY_CONFIG,
    KEYWORD_WEIGHTS,
    TEXT_SECTION_WEIGHTS,
    URL_PATTERN_WEIGHTS,
    CONFIDENCE_THRESHOLDS
)
from src.models.news_model import NewsArticle

logger = logging.getLogger(__name__)

class KeywordClassifier(BaseClassifier):
    """
    Keyword-based classifier that uses weighted keyword matching
    to categorize news articles.
    """

    def __init__(self, confidence_threshold: float = None):
        """Initialize keyword classifier."""
        super().__init__(confidence_threshold or CONFIDENCE_THRESHOLDS['keyword'])
        self.category_config = CATEGORY_CONFIG
        logger.info("Initialized KeywordClassifier")

    def classify(self, article: NewsArticle) -> ClassificationResult:
        """
        Classify article using keyword-based analysis.

        Args:
            article: NewsArticle to classify

        Returns:
            ClassificationResult with category, confidence, and explanation
        """
        if not self.validate_article(article):
            return ClassificationResult(
                category='unknown',
                confidence=0.0,
                method_used='keyword',
                explanation='Article content insufficient for classification',
                alternatives=[],
                features_used=[]
            )

        # Extract features for analysis
        features = self.extract_features(article)

        # Calculate scores for each category
        category_scores = self._calculate_category_scores(features)

        # Get best category and alternatives
        sorted_scores = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

        if not sorted_scores or sorted_scores[0][1] == 0:
            return ClassificationResult(
                category='unknown',
                confidence=0.0,
                method_used='keyword',
                explanation='No matching keywords found',
                alternatives=[],
                features_used=[]
            )

        best_category, best_score = sorted_scores[0]

        # Normalize confidence score (0-1 range)
        max_possible_score = self._calculate_max_possible_score(features)
        confidence = min(best_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0

        # Generate explanation
        explanation = self._generate_explanation(best_category, features)

        # Get alternatives (exclude the best category)
        alternatives = [(cat, min(score / max_possible_score, 1.0))
                       for cat, score in sorted_scores[1:] if score > 0]

        # Determine features used
        features_used = self._get_features_used(best_category, features)

        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            method_used='keyword',
            explanation=explanation,
            alternatives=alternatives,
            features_used=features_used
        )

    def _calculate_category_scores(self, features: Dict) -> Dict[str, float]:
        """Calculate weighted scores for each category."""
        scores = defaultdict(float)

        for category in self.SUPPORTED_CATEGORIES:
            category_score = 0.0

            # Text-based scoring
            category_score += self._score_text_content(category, features)

            # URL pattern scoring
            category_score += self._score_url_patterns(category, features)

            # Tag-based scoring
            category_score += self._score_tags(category, features)

            # Apply exclusion rules
            if self._has_exclusion_keywords(category, features):
                category_score *= 0.1  # Heavily penalize excluded content

            scores[category] = category_score

        return dict(scores)

    def _score_text_content(self, category: str, features: Dict) -> float:
        """Score text content (title, summary, content) for category."""
        if category not in self.category_config:
            return 0.0

        total_score = 0.0
        keywords_config = self.category_config[category]['keywords']

        # Score different text sections with weights
        text_sections = {
            'title': features.get('title', ''),
            'summary': features.get('summary', ''),
            'content': features.get('content', '')
        }

        for section, text in text_sections.items():
            if not text:
                continue

            section_weight = TEXT_SECTION_WEIGHTS.get(section, 1.0)
            section_score = 0.0

            # Score keywords by weight category
            for weight_category, keywords in keywords_config.items():
                keyword_weight = KEYWORD_WEIGHTS.get(weight_category, 1.0)

                for keyword in keywords:
                    count = self._count_keyword_occurrences(keyword, text)
                    if count > 0:
                        # Logarithmic scaling to avoid over-weighting repeated terms
                        import math
                        section_score += keyword_weight * (1 + math.log(count))

            total_score += section_score * section_weight

        return total_score

    def _score_url_patterns(self, category: str, features: Dict) -> float:
        """Score URL patterns for category."""
        url = features.get('url', '')
        if not url or category not in self.category_config:
            return 0.0

        url_patterns = self.category_config[category].get('url_patterns', [])

        for pattern in url_patterns:
            if pattern in url:
                return URL_PATTERN_WEIGHTS['high'] * 5.0  # Strong URL signal

        return 0.0

    def _score_tags(self, category: str, features: Dict) -> float:
        """Score article tags for category."""
        tags = features.get('tags', [])
        if not tags or category not in self.category_config:
            return 0.0

        total_score = 0.0
        keywords_config = self.category_config[category]['keywords']
        tag_weight = TEXT_SECTION_WEIGHTS.get('tags', 1.5)

        for tag in tags:
            tag_lower = tag.lower()

            # Check against all keyword categories
            for weight_category, keywords in keywords_config.items():
                keyword_weight = KEYWORD_WEIGHTS.get(weight_category, 1.0)

                for keyword in keywords:
                    if keyword in tag_lower or tag_lower in keyword:
                        total_score += keyword_weight * tag_weight

        return total_score

    def _has_exclusion_keywords(self, category: str, features: Dict) -> bool:
        """Check if content has exclusion keywords for this category."""
        if category not in self.category_config:
            return False

        exclude_keywords = self.category_config[category].get('exclude_keywords', set())
        if not exclude_keywords:
            return False

        # Check title and content for exclusion keywords
        text_to_check = f"{features.get('title', '')} {features.get('content', '')}"
        text_lower = text_to_check.lower()

        for exclude_keyword in exclude_keywords:
            if exclude_keyword in text_lower:
                return True

        return False

    def _count_keyword_occurrences(self, keyword: str, text: str) -> int:
        """Count keyword occurrences with word boundary awareness."""
        if not keyword or not text:
            return 0

        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        matches = re.findall(pattern, text.lower())
        return len(matches)

    def _calculate_max_possible_score(self, features: Dict) -> float:
        """Calculate theoretical maximum score for normalization."""
        # Estimate based on content length and section weights
        title_words = len(features.get('title', '').split())
        content_words = features.get('word_count', 0)

        # Rough estimate of max possible score
        max_score = (
            title_words * TEXT_SECTION_WEIGHTS['title'] * KEYWORD_WEIGHTS['high_weight'] +
            content_words * TEXT_SECTION_WEIGHTS['content'] * KEYWORD_WEIGHTS['medium_weight'] * 0.1 +
            URL_PATTERN_WEIGHTS['high'] * 5.0 +  # Max URL score
            TEXT_SECTION_WEIGHTS['tags'] * KEYWORD_WEIGHTS['high_weight'] * 3  # Max tag score
        )

        return max(max_score, 10.0)  # Minimum threshold

    def _generate_explanation(self, category: str, features: Dict) -> str:
        """Generate human-readable explanation for classification."""
        explanations = []

        # Check for strong URL indicators
        url = features.get('url', '')
        if category in self.category_config:
            url_patterns = self.category_config[category].get('url_patterns', [])
            for pattern in url_patterns:
                if pattern in url:
                    explanations.append(f"URL contains '{pattern}'")
                    break

        # Check for high-weight keywords in title
        title = features.get('title', '')
        if title and category in self.category_config:
            high_weight_keywords = self.category_config[category]['keywords'].get('high_weight', set())
            found_keywords = []

            for keyword in high_weight_keywords:
                if self._count_keyword_occurrences(keyword, title) > 0:
                    found_keywords.append(keyword)
                    if len(found_keywords) >= 3:  # Limit to first 3
                        break

            if found_keywords:
                explanations.append(f"Title contains key terms: {', '.join(found_keywords)}")

        # Check for tags
        tags = features.get('tags', [])
        if tags:
            relevant_tags = [tag for tag in tags if any(
                keyword in tag.lower()
                for keyword_set in self.category_config.get(category, {}).get('keywords', {}).values()
                for keyword in keyword_set
            )]
            if relevant_tags:
                explanations.append(f"Relevant tags: {', '.join(relevant_tags[:2])}")

        if not explanations:
            explanations.append(f"Content analysis indicates {category} category")

        return "; ".join(explanations)

    def _get_features_used(self, category: str, features: Dict) -> List[str]:
        """Get list of features that contributed to classification."""
        features_used = []

        # Check which sections had matching keywords
        if features.get('title'):
            features_used.append('title')
        if features.get('summary'):
            features_used.append('summary')
        if features.get('content'):
            features_used.append('content')
        if features.get('url'):
            features_used.append('url')
        if features.get('tags'):
            features_used.append('tags')

        return features_used

    def get_category_scores(self, article: NewsArticle) -> Dict[str, float]:
        """
        Get confidence scores for all categories efficiently.

        Args:
            article: NewsArticle to analyze

        Returns:
            Dict mapping category names to confidence scores
        """
        if not self.validate_article(article):
            return {category: 0.0 for category in self.SUPPORTED_CATEGORIES}

        features = self.extract_features(article)
        category_scores = self._calculate_category_scores(features)
        max_possible_score = self._calculate_max_possible_score(features)

        # Normalize scores to 0-1 range
        normalized_scores = {}
        for category in self.SUPPORTED_CATEGORIES:
            raw_score = category_scores.get(category, 0.0)
            normalized_scores[category] = min(raw_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0

        return normalized_scores