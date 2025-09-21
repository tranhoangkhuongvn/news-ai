"""
Article Categorization Services

This module provides intelligent categorization of news articles based on content analysis,
keywords, and metadata. It supports multiple classification methods with confidence scoring.
"""

from .base_classifier import BaseClassifier, ClassificationResult
from .keyword_classifier import KeywordClassifier
from .hybrid_classifier import HybridClassifier
from .category_config import CATEGORY_CONFIG

__all__ = [
    'BaseClassifier',
    'ClassificationResult',
    'KeywordClassifier',
    'HybridClassifier',
    'CATEGORY_CONFIG'
]