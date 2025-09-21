"""
Data models for story prioritization functionality.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class StoryMetrics:
    """Metrics used for story prioritization scoring."""
    breaking_news_score: float
    coverage_score: float
    quality_score: float
    overall_priority_score: float

    # Detailed breakdown
    time_urgency: float
    source_velocity: float
    urgency_keywords_found: List[str]
    source_count: int
    similarity_confidence: float
    geographic_scope: str
    content_depth_score: float
    classification_confidence: float

    @property
    def priority_level(self) -> str:
        """Get priority level based on overall score."""
        if self.overall_priority_score >= 0.8:
            return "BREAKING"
        elif self.overall_priority_score >= 0.6:
            return "HIGH"
        elif self.overall_priority_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

@dataclass
class PrioritizedStory:
    """A news story with prioritization scoring and metadata."""
    story_id: str
    main_article_id: int
    title: str
    summary: str
    category: str
    sources: List[str]
    article_count: int
    latest_published: datetime
    first_published: datetime

    # Prioritization data
    metrics: StoryMetrics

    # Article cluster data
    similar_articles: List[Dict]
    representative_article: Dict

    @property
    def is_breaking(self) -> bool:
        """Check if this story qualifies as breaking news."""
        return self.metrics.priority_level == "BREAKING"

    @property
    def coverage_description(self) -> str:
        """Get description of source coverage."""
        source_count = len(self.sources)
        if source_count >= 4:
            return f"All {source_count} major sources"
        elif source_count >= 3:
            return f"{source_count} major sources"
        elif source_count >= 2:
            return f"{source_count} sources"
        else:
            return "Single source"

    @property
    def time_description(self) -> str:
        """Get human-readable time description."""
        time_diff = datetime.now() - self.latest_published

        if time_diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(time_diff.total_seconds() / 60)
            return f"{minutes} minutes ago"
        elif time_diff.total_seconds() < 86400:  # Less than 1 day
            hours = int(time_diff.total_seconds() / 3600)
            return f"{hours} hours ago"
        else:
            days = int(time_diff.total_seconds() / 86400)
            return f"{days} days ago"

@dataclass
class PrioritizationConfig:
    """Configuration for story prioritization algorithm."""

    # Weight distribution (must sum to 1.0)
    breaking_news_weight: float = 0.4
    coverage_weight: float = 0.35
    quality_weight: float = 0.25

    # Breaking news scoring thresholds
    breaking_time_threshold_hours: float = 2.0
    high_velocity_threshold_minutes: float = 30.0

    # Coverage scoring parameters
    max_sources: int = 4
    min_similarity_threshold: float = 0.6

    # Quality scoring parameters
    min_content_length: int = 200
    max_content_length: int = 2000
    min_classification_confidence: float = 0.5

    # Urgency keywords for breaking news detection
    urgency_keywords: List[str] = None

    def __post_init__(self):
        """Initialize default urgency keywords if not provided."""
        if self.urgency_keywords is None:
            self.urgency_keywords = [
                # General urgency
                'breaking', 'urgent', 'emergency', 'alert', 'crisis',
                'developing', 'live', 'now', 'just in', 'update',

                # Financial urgency
                'crash', 'plunge', 'surge', 'record', 'emergency rate',
                'market shock', 'trading halt',

                # Sports urgency
                'injury', 'suspended', 'banned', 'controversy', 'shock',
                'upset', 'record', 'winner', 'champion',

                # General news urgency
                'announces', 'confirms', 'reveals', 'admits', 'denies',
                'resigns', 'appointed', 'arrested', 'charged'
            ]

        # Validate weight distribution
        total_weight = (self.breaking_news_weight +
                       self.coverage_weight +
                       self.quality_weight)

        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Prioritization weights must sum to 1.0 (current sum: {total_weight})")

@dataclass
class SourceStats:
    """Statistics about source coverage in prioritization."""
    source_name: str
    articles_contributed: int
    clusters_participated: int
    average_quality_score: float
    breaking_news_count: int