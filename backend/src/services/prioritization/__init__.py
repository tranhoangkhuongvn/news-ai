"""
Story prioritization module for intelligent news ranking.

This module provides functionality to prioritize news stories based on:
- Breaking news indicators (recency, urgency keywords)
- Cross-source coverage (how many outlets cover the story)
- Content quality (depth, classification confidence)
"""

from .story_prioritizer import StoryPrioritizationEngine, PrioritizedStory
from .prioritization_models import StoryMetrics, PrioritizationConfig

__all__ = [
    'StoryPrioritizationEngine',
    'PrioritizedStory',
    'StoryMetrics',
    'PrioritizationConfig'
]