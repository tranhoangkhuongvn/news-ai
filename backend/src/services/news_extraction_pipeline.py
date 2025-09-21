from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import aiohttp
import asyncio


from src.scrapers.aussie_news_extractor import ExtractorFactory
from src.db.database_conn import NewsDatabase
from src.services.categorization.hybrid_classifier import HybridClassifier


logger = logging.getLogger(__name__)

class NewsExtractionPipeline:
    """Updated main pipeline orchestrator using the extractor factory"""
    
    def __init__(self):
        self.database = NewsDatabase()
        self.extractors = {}
        self.supported_categories = ["sports", "lifestyle", "music", "finance"]
        self.classifier = HybridClassifier()
        logger.info("Initialized NewsExtractionPipeline with intelligent categorization")
    
    async def initialize(self):
        """Initialize the pipeline with async components"""
        # Create aiohttp session with optimized settings and better headers
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)

        # Enhanced headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-AU,en;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=headers
        )
        
        # Initialize extractors for all available sources
        for source in ExtractorFactory.get_available_sources():
            try:
                self.extractors[source] = ExtractorFactory.create_extractor(source, self.session)
                logger.info(f"Initialized extractor for: {source}")
            except Exception as e:
                logger.error(f"Failed to initialize extractor for {source}: {e}")
    
    async def extract_news(self, 
                          sources: List[str] = None, 
                          categories: List[str] = None,
                          max_articles_per_category: int = 20) -> Dict[str, Any]:
        """Main extraction method supporting multiple sources"""
        
        if sources is None:
            sources = ['abc', 'guardian', 'smh', 'news_com_au']  # Use all available sources
        if categories is None:
            categories = self.supported_categories
        
        # Validate inputs
        available_sources = ExtractorFactory.get_available_sources()
        valid_sources = [s for s in sources if s in available_sources]
        valid_categories = [c for c in categories if c in self.supported_categories]
        
        if not valid_sources:
            raise ValueError(f"No valid sources specified. Available: {available_sources}")
        if not valid_categories:
            raise ValueError(f"No valid categories specified. Available: {self.supported_categories}")
        
        logger.info(f"Starting extraction for sources: {valid_sources}, categories: {valid_categories}")
        
        extraction_results = {
            'total_articles': 0,
            'successful_saves': 0,
            'failed_saves': 0,
            'by_category': {},
            'by_source': {},
            'extraction_time': None,
            'errors': []
        }
        
        import time
        start_time = time.time()
        
        try:
            # Create extraction tasks for each source-category combination
            tasks = []
            for source in valid_sources:
                if source not in self.extractors:
                    logger.warning(f"Extractor not initialized for source: {source}")
                    continue
                
                extractor = self.extractors[source]
                
                # Check which categories are supported by this source
                supported_cats = [cat for cat in valid_categories if cat in extractor.category_urls]
                
                for category in supported_cats:
                    task = extractor.extract_category_articles(category, max_articles_per_category)
                    tasks.append((source, category, task))
            
            if not tasks:
                raise ValueError("No valid source-category combinations found")
            
            logger.info(f"Created {len(tasks)} extraction tasks")
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True)
            
            # Process results
            for (source, category, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    error_msg = f"Error extracting {category} from {source}: {result}"
                    logger.error(error_msg)
                    extraction_results['errors'].append(error_msg)
                    continue
                
                articles = result
                extraction_results['total_articles'] += len(articles)
                
                # Initialize counters
                if category not in extraction_results['by_category']:
                    extraction_results['by_category'][category] = 0
                if source not in extraction_results['by_source']:
                    extraction_results['by_source'][source] = 0
                
                # Process and save articles with intelligent categorization
                for article in articles:
                    try:
                        # Classify the article using intelligent categorization
                        classification_result = self.classifier.classify(article)

                        # Log classification details
                        logger.debug(f"Article '{article.title[:50]}...' classified as '{classification_result.category}' "
                                   f"with confidence {classification_result.confidence:.3f}")

                        # Use intelligent classification if confident enough
                        if classification_result.confidence >= self.classifier.confidence_threshold:
                            # Update article category with intelligent classification
                            article.category = classification_result.category

                            # Save with classification data
                            if self.database.save_article_with_classification(article, classification_result):
                                extraction_results['successful_saves'] += 1
                                extraction_results['by_category'][classification_result.category] += 1
                                extraction_results['by_source'][source] += 1
                            else:
                                extraction_results['failed_saves'] += 1
                        else:
                            # Keep original category if classification not confident enough
                            logger.info(f"Low confidence classification ({classification_result.confidence:.3f}) "
                                       f"for article '{article.title[:50]}...', keeping original category '{article.category}'")

                            # Save with original category but include classification attempt
                            if self.database.save_article_with_classification(article, classification_result):
                                extraction_results['successful_saves'] += 1
                                extraction_results['by_category'][article.category] += 1
                                extraction_results['by_source'][source] += 1
                            else:
                                extraction_results['failed_saves'] += 1

                    except Exception as e:
                        logger.error(f"Error classifying article '{article.title[:50]}...': {e}")
                        # Fallback to original save method
                        if self.database.save_article(article):
                            extraction_results['successful_saves'] += 1
                            extraction_results['by_category'][article.category] += 1
                            extraction_results['by_source'][source] += 1
                        else:
                            extraction_results['failed_saves'] += 1
            
            extraction_results['extraction_time'] = time.time() - start_time
            
            logger.info(f"Extraction completed: {extraction_results['total_articles']} articles extracted, "
                       f"{extraction_results['successful_saves']} saved successfully")
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            extraction_results['errors'].append(str(e))
        
        return extraction_results
    
    async def close(self):
        """Clean up resources"""
        if hasattr(self, 'session'):
            await self.session.close()

# Updated user interface functions
async def run_extraction_pipeline(sources: List[str] = None, 
                                categories: List[str] = None,
                                max_articles: int = 20) -> Dict[str, Any]:
    """User-friendly function to trigger the extraction pipeline with multiple sources"""
    pipeline = NewsExtractionPipeline()
    
    try:
        await pipeline.initialize()
        results = await pipeline.extract_news(sources, categories, max_articles)
        return results
    finally:
        await pipeline.close()

# Example usage with multiple sources
if __name__ == "__main__":
    async def example_multi_source_extraction():
        print("Available sources:", ExtractorFactory.get_available_sources())
        
        # Example 1: Extract from multiple sources
        print("\n1. Multi-source extraction...")
        results = await run_extraction_pipeline(
            sources=['abc', 'guardian'],  # Multiple sources
            categories=['sports', 'finance', 'music', 'lifestyle'],
            max_articles=10
        )
        print(f"Results: {results}")
        
        # Example 2: ABC News only
        print("\n2. ABC News only...")
        results = await run_extraction_pipeline(
            sources=['abc'],
            categories=['sports', 'lifestyle', 'music', 'lifestyle'],
            max_articles=15
        )
        print(f"ABC Results: {results}")
        
        # Example 3: All sources, all categories
        print("\n3. All sources, all categories...")
        results = await run_extraction_pipeline(
            sources=ExtractorFactory.get_available_sources(),
            categories=['sports', 'finance', 'lifestyle', 'music'],
            max_articles=5  # Smaller number for all sources
        )
        print(f"All sources results: {results}")
    
    # Run the example
    asyncio.run(example_multi_source_extraction())