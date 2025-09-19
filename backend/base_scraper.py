# backend/app/scrapers/base_scraper.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from newspaper import Article, Config
import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, source_name: str, base_url: str, rate_limit: float = 1.0):
        self.source_name = source_name
        self.base_url = base_url
        self.rate_limit = rate_limit
        
        # Configure session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Configure newspaper3k
        self.config = Config()
        self.config.browser_user_agent = self.session.headers['User-Agent']
        self.config.request_timeout = 30
        self.config.number_threads = 1
        self.config.thread_timeout_seconds = 30
    
    @abstractmethod
    def get_article_urls(self) -> List[str]:
        """Get list of article URLs from the news source"""
        pass
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is proper and belongs to the expected domain"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.scheme in ['http', 'https'])
        except Exception:
            return False
    
    def clean_url(self, url: str) -> str:
        """Clean and normalize URL"""
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return urljoin(self.base_url, url)
        return url
    
    def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape a single article with enhanced error handling and data extraction"""
        try:
            if not self.validate_url(url):
                logger.warning(f"Invalid URL: {url}")
                return None
                
            # Use newspaper3k for article extraction
            article = Article(url, config=self.config)
            article.download()
            
            # Check if download was successful
            if not article.html:
                logger.warning(f"No HTML content downloaded for: {url}")
                return None
                
            article.parse()
            article.nlp()  # Extract keywords and summary
            
            # Validate essential content
            if not article.title or len(article.text.strip()) < 100:
                logger.warning(f"Article too short or missing title: {url}")
                return None
            
            # Clean and process the content
            title = article.title.strip()
            content = article.text.strip()
            
            # Extract additional metadata
            meta_description = article.meta_description or ""
            keywords = list(article.keywords) if article.keywords else []
            
            # Handle publish date
            published_date = article.publish_date
            if published_date is None:
                # Try to extract date from meta tags or content
                published_date = self._extract_publish_date(article.html)
            
            # Build article data
            article_data = {
                'title': title,
                'content': content,
                'url': url,
                'source': self.source_name,
                'published_date': published_date or datetime.now(),
                'authors': list(article.authors) if article.authors else [],
                'meta_description': meta_description,
                'keywords': keywords,
                'top_image': article.top_image,
                'word_count': len(content.split()),
                'language': self._detect_language(content),
                'scraped_at': datetime.now()
            }
            
            return article_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None
    
    def _extract_publish_date(self, html: str) -> Optional[datetime]:
        """Extract publish date from HTML meta tags"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Common meta tag selectors for publish date
            date_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="pubdate"]',
                'meta[name="publish-date"]',
                'meta[name="date"]',
                'time[datetime]',
                '.published-date',
                '.article-date'
            ]
            
            for selector in date_selectors:
                element = soup.select_one(selector)
                if element:
                    date_str = element.get('content') or element.get('datetime') or element.get_text()
                    if date_str:
                        # Try to parse the date
                        from dateutil.parser import parse
                        return parse(date_str.strip())
                        
        except Exception as e:
            logger.debug(f"Error extracting publish date: {e}")
        
        return None
    
    def _detect_language(self, content: str) -> str:
        """Simple language detection (defaults to English for Australian news)"""
        # For Australian news sources, we can assume English
        # In a more robust implementation, you might use langdetect library
        return 'en'
    
    def scrape_all(self, max_articles: int = 50) -> List[Dict]:
        """Scrape all articles with improved error handling and logging"""
        logger.info(f"Starting to scrape articles from {self.source_name}")
        
        try:
            urls = self.get_article_urls()
            logger.info(f"Found {len(urls)} article URLs from {self.source_name}")
            
            # Limit the number of articles to scrape
            urls = urls[:max_articles]
            
            articles = []
            failed_count = 0
            
            for i, url in enumerate(urls, 1):
                logger.debug(f"Scraping article {i}/{len(urls)}: {url}")
                
                article = self.scrape_article(url)
                if article:
                    articles.append(article)
                    logger.debug(f"Successfully scraped: {article['title'][:50]}...")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to scrape: {url}")
                
                # Rate limiting
                if i < len(urls):  # Don't sleep after the last article
                    time.sleep(self.rate_limit)
            
            success_rate = (len(articles) / len(urls)) * 100 if urls else 0
            logger.info(f"Scraping completed for {self.source_name}. "
                       f"Success: {len(articles)}, Failed: {failed_count}, "
                       f"Success rate: {success_rate:.1f}%")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error in scrape_all for {self.source_name}: {e}")
            return []
    
    def test_scraping(self, num_articles: int = 3) -> List[Dict]:
        """Test scraping with a small number of articles"""
        logger.info(f"Testing scraping for {self.source_name} with {num_articles} articles")
        return self.scrape_all(max_articles=num_articles)