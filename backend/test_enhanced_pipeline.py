"""
Test script for Enhanced News Pipeline Service.

This script tests the integration between extraction, similarity detection,
and intelligent prioritization components.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.enhanced_news_pipeline import EnhancedNewsPipelineService
from services.prioritization import PrioritizationConfig

async def test_enhanced_pipeline():
    """Test the enhanced news pipeline with a small dataset."""
    print("🧪 Testing Enhanced News Pipeline Service")
    print("=" * 60)

    # Initialize the service
    pipeline_service = EnhancedNewsPipelineService()

    # Test 1: Check pipeline status
    print("\n📊 Test 1: Pipeline Status Check")
    status = await pipeline_service.get_pipeline_status()
    print(f"Pipeline Ready: {status['pipeline_ready']}")
    print(f"Total Articles in DB: {status['database'].get('total_articles', 0)}")
    print(f"Recent Similarities: {status['similarity'].get('recent_similarities', 0)}")

    # Test 2: Run small-scale enhanced extraction
    print("\n🚀 Test 2: Small-Scale Enhanced Extraction")
    print("Running extraction from 2 sources, 2 categories, 3 articles each (12 total)")

    # Custom configuration for testing
    test_config = PrioritizationConfig(
        breaking_news_weight=0.5,
        coverage_weight=0.3,
        quality_weight=0.2,
        breaking_time_threshold_hours=6.0,  # More lenient for testing
        max_sources=2
    )

    results = await pipeline_service.run_enhanced_extraction(
        sources=['abc', 'guardian'],
        categories=['sports', 'finance'],
        articles_per_category=3,
        prioritization_config=test_config
    )

    print(f"✅ Pipeline Success: {results['success']}")
    print(f"⏱️  Processing Time: {results['processing_time']}s")
    print(f"📰 Articles Extracted: {results['metrics']['total_articles_extracted']}")
    print(f"🔗 Similar Pairs Found: {results['metrics']['similar_pairs_found']}")
    print(f"📊 Clusters Created: {results['metrics']['clusters_created']}")
    print(f"⭐ Stories Prioritized: {results['metrics']['stories_prioritized']}")
    print(f"🏆 Top Stories Selected: {results['metrics']['top_stories_count']}")

    # Test 3: Display top prioritized stories
    if results['success'] and results['top_stories']:
        print(f"\n🏆 Test 3: Top {len(results['top_stories'])} Prioritized Stories")
        print("-" * 60)

        for i, story in enumerate(results['top_stories'][:5], 1):
            print(f"\n{i}. [{story['priority_level']}] {story['title'][:80]}...")
            print(f"   📊 Priority Score: {story['priority_score']} "
                  f"(Breaking: {story['breaking_news_score']}, "
                  f"Coverage: {story['coverage_score']}, "
                  f"Quality: {story['quality_score']})")
            print(f"   📰 Sources: {', '.join(story['sources'])} ({story['article_count']} articles)")
            print(f"   ⏰ {story['time_description']} | 📍 {story['geographic_scope']}")
            if story['urgency_keywords']:
                print(f"   🚨 Urgency Keywords: {', '.join(story['urgency_keywords'])}")

    # Test 4: Verify pipeline phases worked correctly
    print(f"\n🔍 Test 4: Pipeline Phase Analysis")
    print("-" * 40)

    extraction = results.get('extraction', {})
    similarity = results.get('similarity', {})
    prioritization = results.get('prioritization', {})

    print(f"📥 Extraction Phase:")
    print(f"   Expected Articles: {extraction.get('expected_articles', 0)}")
    print(f"   Extraction Rate: {extraction.get('extraction_rate', 0)}%")
    print(f"   Sources Processed: {extraction.get('sources_processed', 0)}")

    print(f"🔗 Similarity Phase:")
    print(f"   Total Comparisons: {similarity.get('total_comparisons', 0)}")
    print(f"   Similarity Rate: {similarity.get('similarity_rate', 0)}%")
    print(f"   Average Score: {similarity.get('average_similarity_score', 0)}")

    print(f"⭐ Prioritization Phase:")
    print(f"   Stories Analyzed: {prioritization.get('total_stories_analyzed', 0)}")
    print(f"   Average Priority: {prioritization.get('average_priority_score', 0)}")

    priority_dist = prioritization.get('priority_distribution', {})
    if priority_dist:
        print(f"   Priority Distribution: "
              f"Breaking: {priority_dist.get('BREAKING', 0)}, "
              f"High: {priority_dist.get('HIGH', 0)}, "
              f"Medium: {priority_dist.get('MEDIUM', 0)}, "
              f"Low: {priority_dist.get('LOW', 0)}")

    print(f"\n🎯 Enhanced Pipeline Test Completed!")
    print(f"Overall Status: {'✅ SUCCESS' if results['success'] else '❌ FAILED'}")

    return results

async def test_full_scale_pipeline():
    """Test the full-scale enhanced pipeline (320 articles)."""
    print("\n" + "=" * 80)
    print("🚀 FULL-SCALE ENHANCED PIPELINE TEST")
    print("=" * 80)
    print("⚠️  This will extract 320 articles (4 sources × 4 categories × 20 articles)")
    print("⏱️  Expected processing time: 3-5 minutes")

    response = input("\nProceed with full-scale test? (y/n): ")
    if response.lower() != 'y':
        print("Full-scale test skipped.")
        return None

    pipeline_service = EnhancedNewsPipelineService()

    # Run full-scale extraction with default parameters
    print("\n🚀 Starting full-scale enhanced extraction...")
    start_time = asyncio.get_event_loop().time()

    results = await pipeline_service.run_enhanced_extraction()

    end_time = asyncio.get_event_loop().time()
    total_time = end_time - start_time

    print(f"\n📈 Full-Scale Results:")
    print(f"✅ Success: {results['success']}")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    print(f"📰 Articles: {results['metrics']['total_articles_extracted']}/320 expected")
    print(f"🔗 Similar Pairs: {results['metrics']['similar_pairs_found']}")
    print(f"📊 Clusters: {results['metrics']['clusters_created']}")
    print(f"⭐ Prioritized: {results['metrics']['stories_prioritized']}")
    print(f"🏆 Top Stories: {results['metrics']['top_stories_count']}")

    if results['success'] and results['top_stories']:
        print(f"\n🏆 Top 3 Full-Scale Stories:")
        for i, story in enumerate(results['top_stories'][:3], 1):
            print(f"{i}. [{story['priority_level']}] {story['title']}")
            print(f"   Score: {story['priority_score']} | Sources: {len(story['sources'])}")

    return results

if __name__ == "__main__":
    # Run the tests
    print("🧪 Enhanced News Pipeline Integration Tests")
    print("=" * 80)

    # Run small-scale test first
    small_results = asyncio.run(test_enhanced_pipeline())

    # Optionally run full-scale test
    if small_results and small_results.get('success'):
        full_results = asyncio.run(test_full_scale_pipeline())
    else:
        print("\n❌ Small-scale test failed. Skipping full-scale test.")