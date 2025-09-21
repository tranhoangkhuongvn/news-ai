"""
Testing utilities for article classification system.

Provides tools for testing classification accuracy, performance benchmarking,
and validation of classification results.
"""

import logging
import time
from typing import List, Dict, Tuple
from collections import defaultdict

from .hybrid_classifier import HybridClassifier
from .keyword_classifier import KeywordClassifier
from src.models.news_model import NewsArticle
from src.db.database_conn import NewsDatabase

logger = logging.getLogger(__name__)

class ClassificationTester:
    """Test and validate article classification system."""

    def __init__(self):
        """Initialize classification tester."""
        self.hybrid_classifier = HybridClassifier()
        self.keyword_classifier = KeywordClassifier()
        self.db = NewsDatabase()

    def test_sample_articles(self, limit: int = 10) -> Dict:
        """Test classification on sample articles from database."""
        print(f"\n🧪 Testing Classification on {limit} Sample Articles")
        print("=" * 60)

        articles = self.db.get_articles(limit=limit)
        if not articles:
            return {'error': 'No articles found in database'}

        results = {
            'total_tested': 0,
            'keyword_results': [],
            'hybrid_results': [],
            'performance': {},
            'accuracy': {}
        }

        for article_data in articles:
            article = self._dict_to_article(article_data)
            if not article:
                continue

            results['total_tested'] += 1

            print(f"\n📰 Article {results['total_tested']}: {article.title[:60]}...")
            print(f"   Original Category: {article_data.get('category', 'unknown')}")
            print(f"   URL: {article.url[:80]}...")

            # Test keyword classifier
            start_time = time.time()
            keyword_result = self.keyword_classifier.classify(article)
            keyword_time = time.time() - start_time

            # Test hybrid classifier
            start_time = time.time()
            hybrid_result = self.hybrid_classifier.classify(article)
            hybrid_time = time.time() - start_time

            # Store results
            results['keyword_results'].append({
                'article_id': article_data.get('id'),
                'original_category': article_data.get('category'),
                'classified_category': keyword_result.category,
                'confidence': keyword_result.confidence,
                'explanation': keyword_result.explanation,
                'processing_time': keyword_time
            })

            results['hybrid_results'].append({
                'article_id': article_data.get('id'),
                'original_category': article_data.get('category'),
                'classified_category': hybrid_result.category,
                'confidence': hybrid_result.confidence,
                'explanation': hybrid_result.explanation,
                'processing_time': hybrid_time
            })

            # Display results
            print(f"   ┌─ Keyword Classifier:")
            print(f"   │  Category: {keyword_result.category} (confidence: {keyword_result.confidence:.3f})")
            print(f"   │  Explanation: {keyword_result.explanation[:80]}...")
            print(f"   │  Time: {keyword_time:.3f}s")
            print(f"   └─ Hybrid Classifier:")
            print(f"      Category: {hybrid_result.category} (confidence: {hybrid_result.confidence:.3f})")
            print(f"      Explanation: {hybrid_result.explanation[:80]}...")
            print(f"      Time: {hybrid_time:.3f}s")

        # Calculate performance metrics
        results['performance'] = self._calculate_performance_metrics(results)
        results['accuracy'] = self._calculate_accuracy_metrics(results)

        self._print_summary(results)
        return results

    def test_specific_article(self, article_id: int) -> Dict:
        """Test classification on a specific article by ID."""
        print(f"\n🔍 Testing Classification on Article ID: {article_id}")
        print("=" * 50)

        # Get article from database
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            article_data = cursor.fetchone()

        if not article_data:
            return {'error': f'Article with ID {article_id} not found'}

        article_data = dict(article_data)
        article = self._dict_to_article(article_data)

        # Test both classifiers
        keyword_result = self.keyword_classifier.classify(article)
        hybrid_result = self.hybrid_classifier.classify(article)

        # Get category scores for detailed analysis
        keyword_scores = self.keyword_classifier.get_category_scores(article)
        hybrid_scores = self.hybrid_classifier.get_category_scores(article)

        print(f"📰 Title: {article.title}")
        print(f"🏷️  Original Category: {article_data.get('category', 'unknown')}")
        print(f"🔗 URL: {article.url}")
        print(f"📊 Content Length: {len(article.content)} characters")

        print(f"\n🤖 Keyword Classifier Results:")
        print(f"   Category: {keyword_result.category}")
        print(f"   Confidence: {keyword_result.confidence:.3f}")
        print(f"   Explanation: {keyword_result.explanation}")
        print(f"   Features Used: {', '.join(keyword_result.features_used)}")

        print(f"\n🧠 Hybrid Classifier Results:")
        print(f"   Category: {hybrid_result.category}")
        print(f"   Confidence: {hybrid_result.confidence:.3f}")
        print(f"   Explanation: {hybrid_result.explanation}")
        print(f"   Features Used: {', '.join(hybrid_result.features_used)}")

        print(f"\n📈 All Category Scores (Keyword):")
        for category, score in sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {score:.3f}")

        print(f"\n📈 All Category Scores (Hybrid):")
        for category, score in sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {score:.3f}")

        return {
            'article': article_data,
            'keyword_result': keyword_result,
            'hybrid_result': hybrid_result,
            'keyword_scores': keyword_scores,
            'hybrid_scores': hybrid_scores
        }

    def benchmark_performance(self, num_articles: int = 50) -> Dict:
        """Benchmark classification performance."""
        print(f"\n⚡ Benchmarking Classification Performance ({num_articles} articles)")
        print("=" * 60)

        articles = self.db.get_articles(limit=num_articles)
        if not articles:
            return {'error': 'No articles found for benchmarking'}

        benchmark_results = {
            'total_articles': len(articles),
            'keyword_times': [],
            'hybrid_times': [],
            'keyword_successful': 0,
            'hybrid_successful': 0
        }

        for i, article_data in enumerate(articles, 1):
            article = self._dict_to_article(article_data)
            if not article:
                continue

            if i % 10 == 0:
                print(f"   Processed {i}/{len(articles)} articles...")

            # Benchmark keyword classifier
            start_time = time.time()
            try:
                keyword_result = self.keyword_classifier.classify(article)
                keyword_time = time.time() - start_time
                benchmark_results['keyword_times'].append(keyword_time)
                if keyword_result.category != 'unknown':
                    benchmark_results['keyword_successful'] += 1
            except Exception as e:
                logger.error(f"Error in keyword classification: {e}")

            # Benchmark hybrid classifier
            start_time = time.time()
            try:
                hybrid_result = self.hybrid_classifier.classify(article)
                hybrid_time = time.time() - start_time
                benchmark_results['hybrid_times'].append(hybrid_time)
                if hybrid_result.category != 'unknown':
                    benchmark_results['hybrid_successful'] += 1
            except Exception as e:
                logger.error(f"Error in hybrid classification: {e}")

        # Calculate statistics
        if benchmark_results['keyword_times']:
            keyword_times = benchmark_results['keyword_times']
            benchmark_results['keyword_stats'] = {
                'avg_time': sum(keyword_times) / len(keyword_times),
                'min_time': min(keyword_times),
                'max_time': max(keyword_times),
                'success_rate': benchmark_results['keyword_successful'] / len(keyword_times)
            }

        if benchmark_results['hybrid_times']:
            hybrid_times = benchmark_results['hybrid_times']
            benchmark_results['hybrid_stats'] = {
                'avg_time': sum(hybrid_times) / len(hybrid_times),
                'min_time': min(hybrid_times),
                'max_time': max(hybrid_times),
                'success_rate': benchmark_results['hybrid_successful'] / len(hybrid_times)
            }

        self._print_benchmark_results(benchmark_results)
        return benchmark_results

    def validate_keywords(self) -> Dict:
        """Validate keyword configuration against actual articles."""
        print(f"\n🔧 Validating Keyword Configuration")
        print("=" * 40)

        from .category_config import CATEGORY_CONFIG

        articles = self.db.get_articles(limit=100)
        validation_results = {
            'keyword_hits': defaultdict(lambda: defaultdict(int)),
            'category_coverage': defaultdict(set),
            'missing_keywords': defaultdict(set)
        }

        for article_data in articles:
            article = self._dict_to_article(article_data)
            if not article:
                continue

            original_category = article_data.get('category', '').lower()
            if original_category not in CATEGORY_CONFIG:
                continue

            text_content = f"{article.title} {article.summary} {article.content}".lower()

            # Check keyword hits for each category
            for category, config in CATEGORY_CONFIG.items():
                for weight_level, keywords in config['keywords'].items():
                    for keyword in keywords:
                        if keyword in text_content:
                            validation_results['keyword_hits'][category][keyword] += 1
                            if category == original_category:
                                validation_results['category_coverage'][category].add(keyword)

        self._print_keyword_validation(validation_results)
        return validation_results

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

    def _calculate_performance_metrics(self, results: Dict) -> Dict:
        """Calculate performance metrics from test results."""
        metrics = {}

        if results['keyword_results']:
            keyword_times = [r['processing_time'] for r in results['keyword_results']]
            metrics['keyword'] = {
                'avg_time': sum(keyword_times) / len(keyword_times),
                'total_time': sum(keyword_times)
            }

        if results['hybrid_results']:
            hybrid_times = [r['processing_time'] for r in results['hybrid_results']]
            metrics['hybrid'] = {
                'avg_time': sum(hybrid_times) / len(hybrid_times),
                'total_time': sum(hybrid_times)
            }

        return metrics

    def _calculate_accuracy_metrics(self, results: Dict) -> Dict:
        """Calculate accuracy metrics by comparing with original categories."""
        metrics = {
            'keyword': {'correct': 0, 'total': 0, 'by_category': defaultdict(lambda: {'correct': 0, 'total': 0})},
            'hybrid': {'correct': 0, 'total': 0, 'by_category': defaultdict(lambda: {'correct': 0, 'total': 0})}
        }

        for result in results['keyword_results']:
            original = result['original_category']
            classified = result['classified_category']
            metrics['keyword']['total'] += 1
            metrics['keyword']['by_category'][original]['total'] += 1

            if original == classified:
                metrics['keyword']['correct'] += 1
                metrics['keyword']['by_category'][original]['correct'] += 1

        for result in results['hybrid_results']:
            original = result['original_category']
            classified = result['classified_category']
            metrics['hybrid']['total'] += 1
            metrics['hybrid']['by_category'][original]['total'] += 1

            if original == classified:
                metrics['hybrid']['correct'] += 1
                metrics['hybrid']['by_category'][original]['correct'] += 1

        # Calculate accuracy percentages
        for method in ['keyword', 'hybrid']:
            if metrics[method]['total'] > 0:
                metrics[method]['accuracy'] = metrics[method]['correct'] / metrics[method]['total']

            for category in metrics[method]['by_category']:
                cat_data = metrics[method]['by_category'][category]
                if cat_data['total'] > 0:
                    cat_data['accuracy'] = cat_data['correct'] / cat_data['total']

        return metrics

    def _print_summary(self, results: Dict):
        """Print test summary."""
        print(f"\n📊 Classification Test Summary")
        print("=" * 40)

        if 'performance' in results:
            perf = results['performance']
            if 'keyword' in perf:
                print(f"⏱️  Keyword Classifier: {perf['keyword']['avg_time']:.4f}s avg")
            if 'hybrid' in perf:
                print(f"⏱️  Hybrid Classifier: {perf['hybrid']['avg_time']:.4f}s avg")

        if 'accuracy' in results:
            acc = results['accuracy']
            if 'keyword' in acc and 'accuracy' in acc['keyword']:
                print(f"🎯 Keyword Accuracy: {acc['keyword']['accuracy']:.1%}")
            if 'hybrid' in acc and 'accuracy' in acc['hybrid']:
                print(f"🎯 Hybrid Accuracy: {acc['hybrid']['accuracy']:.1%}")

    def _print_benchmark_results(self, results: Dict):
        """Print benchmark results."""
        print(f"\n📊 Performance Benchmark Results")
        print("=" * 40)

        if 'keyword_stats' in results:
            stats = results['keyword_stats']
            print(f"🤖 Keyword Classifier:")
            print(f"   Average time: {stats['avg_time']:.4f}s")
            print(f"   Range: {stats['min_time']:.4f}s - {stats['max_time']:.4f}s")
            print(f"   Success rate: {stats['success_rate']:.1%}")

        if 'hybrid_stats' in results:
            stats = results['hybrid_stats']
            print(f"🧠 Hybrid Classifier:")
            print(f"   Average time: {stats['avg_time']:.4f}s")
            print(f"   Range: {stats['min_time']:.4f}s - {stats['max_time']:.4f}s")
            print(f"   Success rate: {stats['success_rate']:.1%}")

    def _print_keyword_validation(self, results: Dict):
        """Print keyword validation results."""
        print(f"\n📋 Top Keywords by Category:")
        for category, keywords in results['keyword_hits'].items():
            print(f"\n{category.upper()}:")
            top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            for keyword, count in top_keywords:
                print(f"   {keyword}: {count} hits")


def run_classification_tests():
    """Run comprehensive classification tests."""
    tester = ClassificationTester()

    print("🧪 Running Comprehensive Classification Tests")
    print("=" * 50)

    # Test on sample articles
    tester.test_sample_articles(limit=10)

    # Run performance benchmark
    tester.benchmark_performance(num_articles=30)

    # Validate keywords
    tester.validate_keywords()

    print(f"\n✅ Classification testing completed!")


if __name__ == "__main__":
    run_classification_tests()