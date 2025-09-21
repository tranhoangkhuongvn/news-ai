"""
Similarity detection module for identifying related news articles across sources.

This module provides functionality to detect similar news articles from different
sources by analyzing title similarity, keyword overlap, and temporal proximity.
"""

from .similarity_detector import SimilarityDetector
from .similarity_service import SimilarityService
from .similarity_models import SimilarityResult, ArticleCluster

__all__ = [
    'SimilarityDetector',
    'SimilarityService',
    'SimilarityResult',
    'ArticleCluster'
]