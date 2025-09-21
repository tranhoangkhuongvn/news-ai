"""
Data models for similarity detection functionality.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class SimilarityResult:
    """Result of similarity comparison between two articles."""
    article_id_1: int
    article_id_2: int
    similarity_score: float
    title_similarity: float
    keyword_similarity: float
    time_similarity: float
    method_used: str
    explanation: str

    @property
    def is_similar(self) -> bool:
        """Check if articles are considered similar (threshold: 0.7)"""
        return self.similarity_score >= 0.7

@dataclass
class ArticleCluster:
    """A cluster of similar articles from different sources."""
    cluster_id: str
    main_article_id: int
    similar_articles: List[int]
    cluster_score: float
    created_at: datetime
    summary: str
    sources_covered: List[str]

    @property
    def article_count(self) -> int:
        """Total number of articles in the cluster."""
        return len(self.similar_articles) + 1  # +1 for main article

    @property
    def source_count(self) -> int:
        """Number of different sources in the cluster."""
        return len(self.sources_covered)

@dataclass
class SimilarityMetrics:
    """Metrics for similarity detection performance."""
    total_comparisons: int
    similar_pairs_found: int
    clusters_created: int
    average_similarity_score: float
    processing_time: float

    @property
    def similarity_rate(self) -> float:
        """Percentage of comparisons that resulted in similarities."""
        if self.total_comparisons == 0:
            return 0.0
        return (self.similar_pairs_found / self.total_comparisons) * 100