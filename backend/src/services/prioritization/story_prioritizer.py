"""
Core story prioritization engine for intelligent news ranking.

This module implements the main algorithm for prioritizing news stories based on
breaking news indicators, cross-source coverage, and content quality.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from .prioritization_models import (
    PrioritizedStory, StoryMetrics, PrioritizationConfig, SourceStats
)

logger = logging.getLogger(__name__)

class StoryPrioritizationEngine:
    """
    Prioritizes news stories using a multi-factor scoring system:
    - Breaking news score (40%): recency, urgency, velocity
    - Coverage score (35%): source diversity, similarity confidence
    - Quality score (25%): content depth, classification confidence
    """

    def __init__(self, config: Optional[PrioritizationConfig] = None):
        """
        Initialize the story prioritization engine.

        Args:
            config: Prioritization configuration settings
        """
        self.config = config or PrioritizationConfig()
        logger.info(f"Initialized StoryPrioritizationEngine with weights: "
                   f"breaking={self.config.breaking_news_weight}, "
                   f"coverage={self.config.coverage_weight}, "
                   f"quality={self.config.quality_weight}")

    def calculate_breaking_news_score(self, article_cluster: Dict) -> Tuple[float, Dict]:
        """
        Calculate breaking news score based on recency and urgency indicators.

        Args:
            article_cluster: Cluster of similar articles

        Returns:
            Tuple of (score, details_dict)
        """
        # Get timing information
        latest_time = self._get_latest_publish_time(article_cluster)
        publish_times = self._get_all_publish_times(article_cluster)

        # 1. Time urgency score (0-1.0)
        time_urgency = self._calculate_time_urgency(latest_time)

        # 2. Source velocity score (0-1.0) - how quickly multiple sources picked up story
        source_velocity = self._calculate_source_velocity(publish_times)

        # 3. Urgency keywords bonus (0-0.3)
        urgency_keywords, urgency_bonus = self._detect_urgency_keywords(article_cluster)

        # Combined breaking news score with bonus
        base_score = (time_urgency * 0.6 + source_velocity * 0.4)
        final_score = min(1.0, base_score + urgency_bonus)

        details = {
            'time_urgency': time_urgency,
            'source_velocity': source_velocity,
            'urgency_keywords_found': urgency_keywords,
            'urgency_bonus': urgency_bonus,
            'latest_publish_time': latest_time
        }

        return final_score, details

    def calculate_coverage_score(self, article_cluster: Dict) -> Tuple[float, Dict]:
        """
        Calculate coverage score based on source diversity and similarity confidence.

        Args:
            article_cluster: Cluster of similar articles

        Returns:
            Tuple of (score, details_dict)
        """
        # 1. Source diversity score (0-1.0)
        sources = self._get_unique_sources(article_cluster)
        source_count_score = min(1.0, len(sources) / self.config.max_sources)

        # 2. Similarity confidence score (0-1.0)
        similarity_confidence = article_cluster.get('cluster_score', 0.0)

        # 3. Geographic scope score (0-1.0)
        scope_score = self._calculate_geographic_scope(article_cluster)

        # Combined coverage score
        coverage_score = (
            source_count_score * 0.5 +
            similarity_confidence * 0.3 +
            scope_score * 0.2
        )

        details = {
            'source_count': len(sources),
            'sources': sources,
            'similarity_confidence': similarity_confidence,
            'geographic_scope': self._determine_geographic_scope(article_cluster),
            'scope_score': scope_score
        }

        return coverage_score, details

    def calculate_quality_score(self, article_cluster: Dict) -> Tuple[float, Dict]:
        """
        Calculate content quality score based on depth and classification confidence.

        Args:
            article_cluster: Cluster of similar articles

        Returns:
            Tuple of (score, details_dict)
        """
        articles = article_cluster.get('similar_articles', [])
        if not articles:
            return 0.0, {}

        # 1. Content depth score (0-1.0)
        content_scores = []
        total_classification_confidence = 0.0
        valid_articles = 0

        for article in articles:
            # Content length scoring
            content_length = len(article.get('content', ''))
            if content_length >= self.config.min_content_length:
                # Score based on content length (normalize between min and max)
                normalized_length = min(1.0, (content_length - self.config.min_content_length) /
                                      (self.config.max_content_length - self.config.min_content_length))
                content_scores.append(normalized_length)

            # Classification confidence
            classification_conf = article.get('classification_confidence', 0.0)
            if classification_conf > 0:
                total_classification_confidence += classification_conf
                valid_articles += 1

        # Average content depth
        avg_content_depth = sum(content_scores) / len(content_scores) if content_scores else 0.0

        # Average classification confidence
        avg_classification_conf = (total_classification_confidence / valid_articles
                                 if valid_articles > 0 else 0.0)

        # Source credibility score (placeholder - can be enhanced later)
        credibility_score = self._calculate_source_credibility(
            self._get_unique_sources(article_cluster)
        )

        # Combined quality score
        quality_score = (
            avg_content_depth * 0.4 +
            avg_classification_conf * 0.4 +
            credibility_score * 0.2
        )

        details = {
            'content_depth_score': avg_content_depth,
            'classification_confidence': avg_classification_conf,
            'credibility_score': credibility_score,
            'articles_analyzed': len(articles)
        }

        return quality_score, details

    def prioritize_stories(self, article_clusters: List[Dict]) -> List[PrioritizedStory]:
        """
        Prioritize a list of article clusters and return ranked stories.

        Args:
            article_clusters: List of article clusters to prioritize

        Returns:
            List of prioritized stories sorted by priority score (descending)
        """
        prioritized_stories = []

        for i, cluster in enumerate(article_clusters):
            try:
                # Calculate individual scores
                breaking_score, breaking_details = self.calculate_breaking_news_score(cluster)
                coverage_score, coverage_details = self.calculate_coverage_score(cluster)
                quality_score, quality_details = self.calculate_quality_score(cluster)

                # Calculate weighted overall score
                overall_score = (
                    breaking_score * self.config.breaking_news_weight +
                    coverage_score * self.config.coverage_weight +
                    quality_score * self.config.quality_weight
                )

                # Create story metrics
                metrics = StoryMetrics(
                    breaking_news_score=breaking_score,
                    coverage_score=coverage_score,
                    quality_score=quality_score,
                    overall_priority_score=overall_score,
                    time_urgency=breaking_details.get('time_urgency', 0.0),
                    source_velocity=breaking_details.get('source_velocity', 0.0),
                    urgency_keywords_found=breaking_details.get('urgency_keywords_found', []),
                    source_count=coverage_details.get('source_count', 0),
                    similarity_confidence=coverage_details.get('similarity_confidence', 0.0),
                    geographic_scope=coverage_details.get('geographic_scope', 'local'),
                    content_depth_score=quality_details.get('content_depth_score', 0.0),
                    classification_confidence=quality_details.get('classification_confidence', 0.0)
                )

                # Get representative article (highest quality or most recent)
                representative_article = self._select_representative_article(cluster)

                # Create prioritized story
                story = PrioritizedStory(
                    story_id=cluster.get('cluster_id', f'story_{i}'),
                    main_article_id=cluster.get('main_article_id', 0),
                    title=representative_article.get('title', 'Unknown Title'),
                    summary=representative_article.get('summary', ''),
                    category=representative_article.get('category', 'general'),
                    sources=coverage_details.get('sources', []),
                    article_count=len(cluster.get('similar_articles', [])),
                    latest_published=breaking_details.get('latest_publish_time', datetime.now()),
                    first_published=self._get_earliest_publish_time(cluster),
                    metrics=metrics,
                    similar_articles=cluster.get('similar_articles', []),
                    representative_article=representative_article
                )

                prioritized_stories.append(story)

            except Exception as e:
                logger.error(f"Error prioritizing story cluster {i}: {e}")
                continue

        # Sort by priority score (descending)
        prioritized_stories.sort(key=lambda x: x.metrics.overall_priority_score, reverse=True)

        top_score = prioritized_stories[0].metrics.overall_priority_score if prioritized_stories else 0
        logger.info(f"Prioritized {len(prioritized_stories)} stories, top score: {top_score:.3f}")

        return prioritized_stories

    def get_top_stories(self, article_clusters: List[Dict], limit: int = 10) -> List[PrioritizedStory]:
        """
        Get the top N prioritized stories.

        Args:
            article_clusters: List of article clusters
            limit: Number of top stories to return

        Returns:
            List of top prioritized stories
        """
        all_prioritized = self.prioritize_stories(article_clusters)
        return all_prioritized[:limit]

    def generate_source_stats(self, prioritized_stories: List[PrioritizedStory]) -> List[SourceStats]:
        """
        Generate statistics about source performance in prioritized stories.

        Args:
            prioritized_stories: List of prioritized stories

        Returns:
            List of source statistics
        """
        source_data = defaultdict(lambda: {
            'articles': 0,
            'clusters': 0,
            'quality_scores': [],
            'breaking_count': 0
        })

        for story in prioritized_stories:
            for source in story.sources:
                source_data[source]['articles'] += story.article_count
                source_data[source]['clusters'] += 1
                source_data[source]['quality_scores'].append(story.metrics.quality_score)

                if story.is_breaking:
                    source_data[source]['breaking_count'] += 1

        # Convert to SourceStats objects
        stats = []
        for source, data in source_data.items():
            avg_quality = (sum(data['quality_scores']) / len(data['quality_scores'])
                          if data['quality_scores'] else 0.0)

            stats.append(SourceStats(
                source_name=source,
                articles_contributed=data['articles'],
                clusters_participated=data['clusters'],
                average_quality_score=avg_quality,
                breaking_news_count=data['breaking_count']
            ))

        return sorted(stats, key=lambda x: x.clusters_participated, reverse=True)

    # Helper methods

    def _get_latest_publish_time(self, cluster: Dict) -> datetime:
        """Get the latest publication time from cluster articles."""
        articles = cluster.get('similar_articles', [])
        if not articles:
            return datetime.now()

        latest = datetime.min
        for article in articles:
            try:
                pub_date = self._parse_date(article.get('published_date', ''))
                if pub_date and pub_date > latest:
                    latest = pub_date
            except:
                continue

        return latest if latest != datetime.min else datetime.now()

    def _get_earliest_publish_time(self, cluster: Dict) -> datetime:
        """Get the earliest publication time from cluster articles."""
        articles = cluster.get('similar_articles', [])
        if not articles:
            return datetime.now()

        earliest = datetime.max
        for article in articles:
            try:
                pub_date = self._parse_date(article.get('published_date', ''))
                if pub_date and pub_date < earliest:
                    earliest = pub_date
            except:
                continue

        return earliest if earliest != datetime.max else datetime.now()

    def _get_all_publish_times(self, cluster: Dict) -> List[datetime]:
        """Get all publication times from cluster articles."""
        times = []
        articles = cluster.get('similar_articles', [])

        for article in articles:
            try:
                pub_date = self._parse_date(article.get('published_date', ''))
                if pub_date:
                    times.append(pub_date)
            except:
                continue

        return sorted(times)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None

        try:
            from dateutil import parser as date_parser
            return date_parser.parse(date_str)
        except:
            return None

    def _calculate_time_urgency(self, latest_time: datetime) -> float:
        """Calculate urgency score based on how recent the latest article is."""
        time_diff = datetime.now() - latest_time
        hours_ago = time_diff.total_seconds() / 3600

        if hours_ago <= 0.5:  # 30 minutes
            return 1.0
        elif hours_ago <= 1.0:  # 1 hour
            return 0.9
        elif hours_ago <= 2.0:  # 2 hours (breaking threshold)
            return 0.8
        elif hours_ago <= 6.0:  # 6 hours
            return 0.6
        elif hours_ago <= 24.0:  # 1 day
            return 0.3
        else:
            return 0.1

    def _calculate_source_velocity(self, publish_times: List[datetime]) -> float:
        """Calculate how quickly multiple sources picked up the story."""
        if len(publish_times) < 2:
            return 0.5  # Neutral score for single source

        earliest = publish_times[0]
        latest = publish_times[-1]
        time_span_minutes = (latest - earliest).total_seconds() / 60

        # Faster pickup = higher velocity score
        if time_span_minutes <= self.config.high_velocity_threshold_minutes:
            return 1.0
        elif time_span_minutes <= 60:  # 1 hour
            return 0.8
        elif time_span_minutes <= 180:  # 3 hours
            return 0.6
        elif time_span_minutes <= 360:  # 6 hours
            return 0.4
        else:
            return 0.2

    def _detect_urgency_keywords(self, cluster: Dict) -> Tuple[List[str], float]:
        """Detect urgency keywords in article titles and content."""
        found_keywords = set()
        articles = cluster.get('similar_articles', [])

        for article in articles:
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            text = f"{title} {summary}"

            for keyword in self.config.urgency_keywords:
                if keyword.lower() in text:
                    found_keywords.add(keyword)

        # Calculate bonus based on number of urgency keywords found
        keyword_count = len(found_keywords)
        if keyword_count >= 3:
            bonus = 0.3
        elif keyword_count >= 2:
            bonus = 0.2
        elif keyword_count >= 1:
            bonus = 0.1
        else:
            bonus = 0.0

        return list(found_keywords), bonus

    def _get_unique_sources(self, cluster: Dict) -> List[str]:
        """Get unique source names from cluster articles."""
        sources = set()
        articles = cluster.get('similar_articles', [])

        for article in articles:
            source = article.get('source', '')
            if source:
                sources.add(source)

        return list(sources)

    def _calculate_geographic_scope(self, cluster: Dict) -> float:
        """Calculate geographic scope of the story."""
        scope = self._determine_geographic_scope(cluster)

        scope_scores = {
            'international': 1.0,
            'national': 0.8,
            'state': 0.6,
            'local': 0.4
        }

        return scope_scores.get(scope, 0.4)

    def _determine_geographic_scope(self, cluster: Dict) -> str:
        """Determine the geographic scope based on content analysis."""
        articles = cluster.get('similar_articles', [])
        all_text = ""

        for article in articles:
            title = article.get('title', '')
            summary = article.get('summary', '')
            all_text += f" {title} {summary}"

        text_lower = all_text.lower()

        # International indicators
        international_keywords = [
            'international', 'global', 'world', 'overseas', 'foreign',
            'usa', 'china', 'europe', 'asia', 'america', 'uk', 'us '
        ]

        # National indicators
        national_keywords = [
            'australia', 'australian', 'national', 'federal', 'commonwealth',
            'parliament', 'government', 'prime minister', 'rba', 'asx'
        ]

        # State indicators
        state_keywords = [
            'nsw', 'victoria', 'queensland', 'western australia', 'south australia',
            'tasmania', 'northern territory', 'act', 'state government'
        ]

        if any(keyword in text_lower for keyword in international_keywords):
            return 'international'
        elif any(keyword in text_lower for keyword in national_keywords):
            return 'national'
        elif any(keyword in text_lower for keyword in state_keywords):
            return 'state'
        else:
            return 'local'

    def _calculate_source_credibility(self, sources: List[str]) -> float:
        """Calculate credibility score based on source reputation."""
        # Source credibility mapping (can be enhanced with external data)
        credibility_scores = {
            'ABC News': 0.95,
            'The Guardian AU': 0.90,
            'Sydney Morning Herald': 0.85,
            'News.com.au': 0.75
        }

        if not sources:
            return 0.5

        total_credibility = sum(credibility_scores.get(source, 0.6) for source in sources)
        return total_credibility / len(sources)

    def _select_representative_article(self, cluster: Dict) -> Dict:
        """Select the best representative article from the cluster."""
        articles = cluster.get('similar_articles', [])
        if not articles:
            return {}

        # Score articles based on content quality and recency
        best_article = articles[0]
        best_score = 0.0

        for article in articles:
            score = 0.0

            # Content length bonus
            content_length = len(article.get('content', ''))
            if content_length > 500:
                score += 0.3

            # Classification confidence bonus
            classification_conf = article.get('classification_confidence', 0.0)
            score += classification_conf * 0.3

            # Recency bonus
            try:
                pub_date = self._parse_date(article.get('published_date', ''))
                if pub_date:
                    hours_ago = (datetime.now() - pub_date).total_seconds() / 3600
                    if hours_ago < 2:
                        score += 0.4
                    elif hours_ago < 6:
                        score += 0.2
            except:
                pass

            if score > best_score:
                best_score = score
                best_article = article

        return best_article