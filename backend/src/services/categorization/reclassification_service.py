"""
Re-classification service for updating existing articles with intelligent categorization.
"""

import logging
from typing import List, Dict
import time

from .hybrid_classifier import HybridClassifier
from src.db.database_conn import NewsDatabase
from src.models.news_model import NewsArticle

logger = logging.getLogger(__name__)

class ReclassificationService:
    """Service for re-classifying existing articles with intelligent categorization."""

    def __init__(self):
        """Initialize re-classification service."""
        self.classifier = HybridClassifier()
        self.db = NewsDatabase()
        logger.info("Initialized ReclassificationService")

    def reclassify_all_articles(self, limit: int = None, force: bool = False) -> Dict:
        """
        Re-classify all articles in the database.

        Args:
            limit: Maximum number of articles to process
            force: If True, re-classify even articles that already have classification data

        Returns:
            Dict with re-classification results
        """
        print(f"\n🔄 Re-classifying Articles (limit: {limit}, force: {force})")
        print("=" * 60)

        # Get articles to re-classify
        if force:
            articles = self.db.get_articles(limit=limit or 1000)
        else:
            articles = self.db.get_articles_for_reclassification(limit=limit or 100)

        if not articles:
            return {'error': 'No articles found for re-classification'}

        results = {
            'total_processed': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'category_changes': {},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'processing_time': 0
        }

        start_time = time.time()

        for i, article_data in enumerate(articles, 1):
            article = self._dict_to_article(article_data)
            if not article:
                continue

            results['total_processed'] += 1

            try:
                # Classify the article
                classification_result = self.classifier.classify(article)

                # Track category changes
                original_category = article_data.get('category', '')
                new_category = classification_result.category

                if original_category != new_category:
                    if original_category not in results['category_changes']:
                        results['category_changes'][original_category] = {}
                    if new_category not in results['category_changes'][original_category]:
                        results['category_changes'][original_category][new_category] = 0
                    results['category_changes'][original_category][new_category] += 1

                # Track confidence distribution
                if classification_result.confidence >= 0.8:
                    results['confidence_distribution']['high'] += 1
                elif classification_result.confidence >= 0.5:
                    results['confidence_distribution']['medium'] += 1
                else:
                    results['confidence_distribution']['low'] += 1

                # Update database
                if self.db.update_article_classification(
                    article_data['id'],
                    classification_result,
                    manual_override=False
                ):
                    results['successful_updates'] += 1
                else:
                    results['failed_updates'] += 1

                # Progress logging
                if i % 10 == 0:
                    print(f"   Processed {i}/{len(articles)} articles...")

            except Exception as e:
                logger.error(f"Error re-classifying article ID {article_data.get('id')}: {e}")
                results['failed_updates'] += 1

        results['processing_time'] = time.time() - start_time

        self._print_reclassification_results(results)
        return results

    def reclassify_category(self, category: str, limit: int = None) -> Dict:
        """
        Re-classify articles from a specific category.

        Args:
            category: Category to re-classify
            limit: Maximum number of articles to process

        Returns:
            Dict with re-classification results
        """
        print(f"\n🎯 Re-classifying '{category}' Articles")
        print("=" * 50)

        articles = self.db.get_articles(category=category, limit=limit or 100)

        if not articles:
            return {'error': f'No articles found in category: {category}'}

        results = {
            'original_category': category,
            'total_processed': 0,
            'confirmed_correct': 0,
            'reclassified': 0,
            'new_categories': {},
            'avg_confidence': 0
        }

        total_confidence = 0

        for article_data in articles:
            article = self._dict_to_article(article_data)
            if not article:
                continue

            results['total_processed'] += 1

            try:
                classification_result = self.classifier.classify(article)
                total_confidence += classification_result.confidence

                if classification_result.category == category:
                    results['confirmed_correct'] += 1
                else:
                    results['reclassified'] += 1
                    new_cat = classification_result.category
                    if new_cat not in results['new_categories']:
                        results['new_categories'][new_cat] = 0
                    results['new_categories'][new_cat] += 1

                    print(f"   📰 '{article.title[:50]}...' -> {new_cat} "
                          f"(confidence: {classification_result.confidence:.3f})")

                # Update database
                self.db.update_article_classification(
                    article_data['id'],
                    classification_result
                )

            except Exception as e:
                logger.error(f"Error re-classifying article: {e}")

        if results['total_processed'] > 0:
            results['avg_confidence'] = total_confidence / results['total_processed']

        self._print_category_results(results)
        return results

    def get_misclassified_articles(self, confidence_threshold: float = 0.5) -> List[Dict]:
        """
        Find articles that might be misclassified based on intelligent analysis.

        Args:
            confidence_threshold: Minimum confidence for current classification

        Returns:
            List of potentially misclassified articles
        """
        print(f"\n🕵️ Finding Potentially Misclassified Articles")
        print("=" * 50)

        articles = self.db.get_articles(limit=200)
        misclassified = []

        for article_data in articles:
            article = self._dict_to_article(article_data)
            if not article:
                continue

            try:
                classification_result = self.classifier.classify(article)
                current_category = article_data.get('category', '')

                # Check if classification suggests different category with high confidence
                if (classification_result.category != current_category and
                    classification_result.confidence >= confidence_threshold):

                    misclassified.append({
                        'id': article_data['id'],
                        'title': article.title,
                        'current_category': current_category,
                        'suggested_category': classification_result.category,
                        'confidence': classification_result.confidence,
                        'explanation': classification_result.explanation,
                        'url': article.url
                    })

            except Exception as e:
                logger.error(f"Error analyzing article: {e}")

        print(f"Found {len(misclassified)} potentially misclassified articles:")
        for item in misclassified[:10]:  # Show first 10
            print(f"   📰 {item['title'][:50]}...")
            print(f"      Current: {item['current_category']} -> Suggested: {item['suggested_category']} "
                  f"(confidence: {item['confidence']:.3f})")

        return misclassified

    def _dict_to_article(self, article_data: Dict) -> NewsArticle:
        """Convert database dict to NewsArticle object."""
        try:
            import json
            tags = json.loads(article_data.get('tags', '[]')) if article_data.get('tags') else []

            return NewsArticle(
                title=article_data.get('title', ''),
                url=article_data.get('url', ''),
                category=article_data.get('category', ''),
                summary=article_data.get('summary', ''),
                published_date=article_data.get('published_date', ''),
                author=article_data.get('author', ''),
                content=article_data.get('content', ''),
                source=article_data.get('source', ''),
                tags=tags,
                extracted_at=article_data.get('extracted_at', '')
            )
        except Exception as e:
            logger.error(f"Error converting dict to article: {e}")
            return None

    def _print_reclassification_results(self, results: Dict):
        """Print re-classification results summary."""
        print(f"\n📊 Re-classification Results Summary")
        print("=" * 40)

        print(f"📈 Processed: {results['total_processed']} articles")
        print(f"✅ Updated: {results['successful_updates']}")
        print(f"❌ Failed: {results['failed_updates']}")
        print(f"⏱️  Time: {results['processing_time']:.2f}s")

        if results['category_changes']:
            print(f"\n🔄 Category Changes:")
            for orig_cat, changes in results['category_changes'].items():
                for new_cat, count in changes.items():
                    print(f"   {orig_cat} -> {new_cat}: {count} articles")

        conf_dist = results['confidence_distribution']
        print(f"\n📊 Confidence Distribution:")
        print(f"   High (≥0.8): {conf_dist['high']} articles")
        print(f"   Medium (0.5-0.8): {conf_dist['medium']} articles")
        print(f"   Low (<0.5): {conf_dist['low']} articles")

    def _print_category_results(self, results: Dict):
        """Print category-specific results."""
        print(f"\n📊 Category Analysis Results")
        print("=" * 40)

        total = results['total_processed']
        confirmed = results['confirmed_correct']
        reclassified = results['reclassified']

        print(f"📈 Processed: {total} '{results['original_category']}' articles")
        print(f"✅ Confirmed Correct: {confirmed} ({confirmed/total:.1%})")
        print(f"🔄 Reclassified: {reclassified} ({reclassified/total:.1%})")
        print(f"📊 Average Confidence: {results['avg_confidence']:.3f}")

        if results['new_categories']:
            print(f"\n🎯 Reclassified to:")
            for new_cat, count in results['new_categories'].items():
                print(f"   {new_cat}: {count} articles")


def run_reclassification():
    """Run re-classification on existing articles."""
    service = ReclassificationService()

    # Re-classify articles without classification data
    service.reclassify_all_articles(limit=20)

    # Find potentially misclassified articles
    service.get_misclassified_articles()


if __name__ == "__main__":
    run_reclassification()