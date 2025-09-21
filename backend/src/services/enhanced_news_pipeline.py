"""
Enhanced News Pipeline Service for intelligent news extraction and prioritization.

This service orchestrates the complete workflow:
1. Extract articles from multiple sources (320 total articles)
2. Classify articles using AI classification pipeline
3. Detect similarities and cluster related articles
4. Apply intelligent prioritization to select top stories
5. Return top 10 prioritized articles with metadata
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import traceback

from services.news_extraction_pipeline import run_extraction_pipeline
from services.similarity import SimilarityService
from services.prioritization import StoryPrioritizationEngine, PrioritizationConfig
from db.database_conn import NewsDatabase

logger = logging.getLogger(__name__)

class EnhancedNewsPipelineService:
    """Enhanced news pipeline with intelligent prioritization."""

    def __init__(self, db: Optional[NewsDatabase] = None):
        self.db = db if db else NewsDatabase()
        self.similarity_service = SimilarityService(self.db)
        self.prioritization_engine = StoryPrioritizationEngine()

        # Default configuration for enhanced extraction
        self.default_sources = ['abc', 'guardian', 'smh', 'news_com_au']
        self.default_categories = ['sports', 'finance', 'lifestyle', 'music']
        self.articles_per_category = 20

    async def run_enhanced_extraction(
        self,
        sources: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        articles_per_category: Optional[int] = None,
        prioritization_config: Optional[PrioritizationConfig] = None
    ) -> Dict[str, Any]:
        """
        Run the complete enhanced news extraction pipeline.

        Args:
            sources: List of news sources to extract from
            categories: List of categories to extract
            articles_per_category: Number of articles per category per source
            prioritization_config: Custom prioritization configuration

        Returns:
            Dictionary with extraction results and top prioritized stories
        """
        start_time = datetime.now()

        # Use defaults if not provided
        if sources is None:
            sources = self.default_sources
        if categories is None:
            categories = self.default_categories
        if articles_per_category is None:
            articles_per_category = self.articles_per_category

        logger.info(f"Starting enhanced extraction pipeline: {len(sources)} sources, "
                   f"{len(categories)} categories, {articles_per_category} articles per category")

        try:
            # Phase 1: Extract articles from all sources
            extraction_results = await self._extract_articles_phase(
                sources, categories, articles_per_category
            )

            # Phase 2: Run similarity detection and clustering
            similarity_results = await self._similarity_detection_phase()

            # Phase 3: Apply intelligent prioritization
            prioritization_results = await self._prioritization_phase(prioritization_config)

            # Calculate total processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Compile comprehensive results
            results = {
                "success": True,
                "processing_time": round(processing_time, 2),
                "extraction": extraction_results,
                "similarity": similarity_results,
                "prioritization": prioritization_results,
                "top_stories": prioritization_results.get("top_stories", []),
                "metrics": {
                    "total_articles_extracted": extraction_results.get("total_articles", 0),
                    "similar_pairs_found": similarity_results.get("similar_pairs_found", 0),
                    "clusters_created": similarity_results.get("clusters_created", 0),
                    "stories_prioritized": len(prioritization_results.get("prioritized_stories", [])),
                    "top_stories_count": len(prioritization_results.get("top_stories", []))
                }
            }

            logger.info(f"Enhanced pipeline completed successfully in {processing_time:.2f}s: "
                       f"{results['metrics']['total_articles_extracted']} articles extracted, "
                       f"{results['metrics']['stories_prioritized']} stories prioritized, "
                       f"{results['metrics']['top_stories_count']} top stories selected")

            return results

        except Exception as e:
            logger.error(f"Enhanced pipeline failed: {e}")
            logger.error(traceback.format_exc())

            return {
                "success": False,
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "extraction": {},
                "similarity": {},
                "prioritization": {},
                "top_stories": [],
                "metrics": {
                    "total_articles_extracted": 0,
                    "similar_pairs_found": 0,
                    "clusters_created": 0,
                    "stories_prioritized": 0,
                    "top_stories_count": 0
                }
            }

    async def _extract_articles_phase(
        self,
        sources: List[str],
        categories: List[str],
        articles_per_category: int
    ) -> Dict[str, Any]:
        """Phase 1: Extract articles from all news sources."""
        logger.info("Phase 1: Starting article extraction")

        try:
            # Run the existing extraction pipeline with enhanced parameters
            extraction_results = await run_extraction_pipeline(
                sources=sources,
                categories=categories,
                max_articles=articles_per_category
            )

            # Calculate expected vs actual extraction counts
            expected_total = len(sources) * len(categories) * articles_per_category
            actual_total = extraction_results.get('total_articles', 0)

            logger.info(f"Phase 1 completed: {actual_total}/{expected_total} articles extracted")

            # Add enhancement metrics
            extraction_results.update({
                "expected_articles": expected_total,
                "extraction_rate": round((actual_total / expected_total) * 100, 1) if expected_total > 0 else 0,
                "sources_processed": len(sources),
                "categories_processed": len(categories)
            })

            return extraction_results

        except Exception as e:
            logger.error(f"Phase 1 extraction failed: {e}")
            raise

    async def _similarity_detection_phase(self) -> Dict[str, Any]:
        """Phase 2: Detect similarities and create article clusters."""
        logger.info("Phase 2: Starting similarity detection and clustering")

        try:
            # Run similarity detection on recent articles (last 2 hours to catch fresh content)
            similarity_metrics = self.similarity_service.detect_all_similarities(hours_back=2)

            # Get article clusters for prioritization
            clusters = self.similarity_service.get_article_clusters(limit=50)

            logger.info(f"Phase 2 completed: {similarity_metrics.similar_pairs_found} similar pairs, "
                       f"{similarity_metrics.clusters_created} clusters created")

            return {
                "similar_pairs_found": similarity_metrics.similar_pairs_found,
                "clusters_created": similarity_metrics.clusters_created,
                "average_similarity_score": round(similarity_metrics.average_similarity_score, 3),
                "processing_time": round(similarity_metrics.processing_time, 2),
                "clusters": clusters,
                "total_comparisons": similarity_metrics.total_comparisons,
                "similarity_rate": round(similarity_metrics.similarity_rate, 1)
            }

        except Exception as e:
            logger.error(f"Phase 2 similarity detection failed: {e}")
            # Continue pipeline even if similarity detection fails
            return {
                "similar_pairs_found": 0,
                "clusters_created": 0,
                "average_similarity_score": 0.0,
                "processing_time": 0.0,
                "clusters": [],
                "total_comparisons": 0,
                "similarity_rate": 0.0,
                "error": str(e)
            }

    async def _prioritization_phase(
        self,
        config: Optional[PrioritizationConfig] = None
    ) -> Dict[str, Any]:
        """Phase 3: Apply intelligent prioritization to select top stories."""
        logger.info("Phase 3: Starting intelligent story prioritization")

        try:
            # Get recent articles for prioritization (last 4 hours for comprehensive coverage)
            recent_articles = self.db.get_articles(limit=500)

            if not recent_articles:
                logger.warning("No articles found for prioritization")
                return {
                    "prioritized_stories": [],
                    "top_stories": [],
                    "processing_time": 0.0,
                    "total_stories_analyzed": 0
                }

            # Get article clusters to understand story relationships
            clusters = self.similarity_service.get_article_clusters(limit=100)

            # If no clusters exist, create individual article clusters
            if not clusters:
                logger.info("No clusters found, creating individual article clusters for prioritization")
                clusters = self._create_individual_clusters(recent_articles)

            # Run prioritization engine
            prioritized_stories = self.prioritization_engine.prioritize_stories(clusters)

            # Select top 10 stories for the enhanced feature
            top_stories = prioritized_stories[:10]

            # Calculate priority distribution
            priority_distribution = {}
            for story in prioritized_stories:
                level = story.metrics.priority_level
                priority_distribution[level] = priority_distribution.get(level, 0) + 1

            logger.info(f"Phase 3 completed: {len(prioritized_stories)} stories prioritized, "
                       f"top 10 selected (Breaking: {priority_distribution.get('BREAKING', 0)}, "
                       f"High: {priority_distribution.get('HIGH', 0)})")

            return {
                "prioritized_stories": [self._story_to_dict(story) for story in prioritized_stories],
                "top_stories": [self._story_to_dict(story) for story in top_stories],
                "processing_time": 0.5,  # Estimated processing time
                "total_stories_analyzed": len(prioritized_stories),
                "priority_distribution": priority_distribution,
                "average_priority_score": round(
                    sum(story.metrics.overall_priority_score for story in prioritized_stories) / len(prioritized_stories), 3
                ) if prioritized_stories else 0.0
            }

        except Exception as e:
            logger.error(f"Phase 3 prioritization failed: {e}")
            raise

    def _create_individual_clusters(self, articles: List[Dict]) -> List[Dict]:
        """
        Create individual article clusters for prioritization when no similarity clusters exist.

        Args:
            articles: List of article dictionaries from database

        Returns:
            List of cluster dictionaries compatible with prioritization engine
        """
        clusters = []

        for article in articles[:50]:  # Limit to 50 most recent articles for performance
            # Convert database article to cluster format
            cluster = {
                'cluster_id': f"single_{article['id']}",
                'main_article_id': article['id'],
                'cluster_score': 1.0,  # Single article clusters have perfect score
                'summary': article.get('summary', ''),
                'sources_covered': [article.get('source', 'Unknown')],
                'similar_articles': [article],  # Only contains the single article
                'main_title': article.get('title', ''),
                'main_source': article.get('source', 'Unknown')
            }
            clusters.append(cluster)

        logger.info(f"Created {len(clusters)} individual article clusters for prioritization")
        return clusters

    def _story_to_dict(self, story) -> Dict[str, Any]:
        """Convert a PrioritizedStory to dictionary format for API response."""
        return {
            "story_id": story.story_id,
            "main_article_id": story.main_article_id,
            "title": story.title,
            "summary": story.summary,
            "category": story.category,
            "sources": story.sources,
            "article_count": story.article_count,
            "latest_published": story.latest_published.isoformat() if isinstance(story.latest_published, datetime) else story.latest_published,
            "first_published": story.first_published.isoformat() if isinstance(story.first_published, datetime) else story.first_published,
            "priority_level": story.metrics.priority_level,
            "priority_score": round(story.metrics.overall_priority_score, 3),
            "breaking_news_score": round(story.metrics.breaking_news_score, 3),
            "coverage_score": round(story.metrics.coverage_score, 3),
            "quality_score": round(story.metrics.quality_score, 3),
            "time_description": story.time_description,
            "coverage_description": story.coverage_description,
            "is_breaking": story.is_breaking,
            "similar_articles": story.similar_articles,
            "representative_article": story.representative_article,
            "urgency_keywords": story.metrics.urgency_keywords_found,
            "geographic_scope": story.metrics.geographic_scope
        }

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current status and statistics of the enhanced pipeline."""
        try:
            # Get database statistics
            classification_stats = self.db.get_classification_stats()
            similarity_stats = self.db.get_recent_similarities(limit=100)

            return {
                "database": {
                    "total_articles": classification_stats.get("total_articles", 0),
                    "classified_articles": classification_stats.get("classified_articles", 0),
                    "by_category": classification_stats.get("by_category", {}),
                    "by_source": classification_stats.get("by_method", {})
                },
                "similarity": {
                    "recent_similarities": len(similarity_stats),
                    "average_score": round(
                        sum(s['similarity_score'] for s in similarity_stats) / len(similarity_stats), 3
                    ) if similarity_stats else 0.0
                },
                "pipeline_ready": True,
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            return {
                "database": {},
                "similarity": {},
                "pipeline_ready": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }