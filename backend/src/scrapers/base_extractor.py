from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re


from src.models.news_model import NewsArticle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaseNewsExtractor(ABC):
    """
    Abstract base class for news extractors.
    Provides common functionality and enforces interface for specific extractors.
    """
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.source = self.get_source_name()
        self.base_url = self.get_base_url()
        self.category_urls = self.get_category_urls()
        self.selectors = self.get_selectors()
        self.headers = self.get_default_headers()

    def get_default_headers(self) -> Dict[str, str]:
        """Return default headers for requests"""
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of the news source"""
        pass
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL of the news source"""
        pass
    
    @abstractmethod
    def get_category_urls(self) -> Dict[str, str]:
        """Return mapping of categories to their URL paths"""
        pass
    
    @abstractmethod
    def get_selectors(self) -> Dict[str, Any]:
        """Return CSS selectors for extracting different elements"""
        pass
    
    @abstractmethod
    def get_article_links_from_category_page(self, soup: BeautifulSoup, category_url: str) -> List[str]:
        """Extract article links from category page - source-specific implementation"""
        pass
    
    def validate_article_url(self, url: str) -> bool:
        """Validate if URL is a valid article URL for this source"""
        # Default implementation - can be overridden
        parsed_url = urlparse(url)
        url_slug = url.split('/')[-1]

        return (
            parsed_url.netloc.endswith(urlparse(self.base_url).netloc) and
            len(url) > 30 and  # Reasonable URL length
            len(url_slug) > 5 and  # Article slug should be substantial
            '-' in url_slug and  # Most article URLs have dashes in slugs
            not url.endswith('/') and  # Avoid category/section pages
            '/category/' not in url.lower() and
            '/section/' not in url.lower() and
            '/tag/' not in url.lower()
        )
    
    def preprocess_content(self, content: str) -> str:
        """Preprocess extracted content - can be overridden for source-specific cleaning"""
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'(ADVERTISEMENT|Advertisement)',
            r'(Related Articles?|Related Stories)',
            r'(Subscribe|Sign up|Newsletter)',
            r'(Share this|Follow us)',
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content.strip()
    
    def extract_date_from_text(self, date_text: str) -> str:
        """Extract and normalize date from text - can be overridden"""
        if not date_text:
            return ""
        
        # Try to parse common date formats
        import dateutil.parser
        try:
            parsed_date = dateutil.parser.parse(date_text, fuzzy=True)
            return parsed_date.isoformat()
        except:
            return date_text.strip()
    
    async def extract_category_articles(self, category: str, max_articles: int = 20) -> List[NewsArticle]:
        """Extract articles from a specific category"""
        if category not in self.category_urls:
            logger.warning(f"Category '{category}' not supported for {self.source}")
            return []
        
        category_url = self.base_url + self.category_urls[category]
        articles = []
        
        try:
            # Get the category page
            timeout = aiohttp.ClientTimeout(total=30)
            async with self.session.get(category_url, headers=self.headers, timeout=timeout) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {category_url}: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Get article links using source-specific method
                article_links = self.get_article_links_from_category_page(soup, category_url)
                
                # Validate and limit articles
                valid_links = []
                for link in article_links:
                    if self.validate_article_url(link) and len(valid_links) < max_articles:
                        valid_links.append(link)
                
                logger.info(f"Found {len(valid_links)} valid article links for {category} from {self.source}")
                
                # Extract each article
                tasks = [self.extract_single_article(url, category) for url in valid_links]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, NewsArticle):
                        articles.append(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Error extracting article: {result}")
                
                logger.info(f"Successfully extracted {len(articles)} articles from {category} ({self.source})")
                
        except Exception as e:
            logger.error(f"Error extracting {category} articles from {self.source}: {e}")
        
        return articles
    
    async def extract_single_article(self, url: str, category: str) -> Optional[NewsArticle]:
        """Extract a single article from its URL"""
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with self.session.get(url, headers=self.headers, timeout=timeout) as response:
                if response.status != 200:
                    logger.debug(f"Failed to fetch article {url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract article data using selectors
                title = self._extract_title(soup)
                summary = self._extract_summary(soup)
                published_date = self._extract_published_date(soup)
                author = self._extract_author(soup)
                content = self._extract_content(soup)
                tags = self._extract_tags(soup)
                
                if not title or len(title.strip()) < 5:  # Skip if we can't get basic info
                    logger.debug(f"Skipping article with insufficient title: {url}")
                    return None

                if not content or len(content.strip()) < 200:  # Skip if content is too short
                    logger.debug(f"Skipping article with insufficient content: {url}")
                    return None
                
                # Preprocess content
                content = self.preprocess_content(content)
                summary = self.preprocess_content(summary)
                
                return NewsArticle(
                    title=title.strip(),
                    url=url,
                    category=category,
                    summary=summary,
                    published_date=self.extract_date_from_text(published_date),
                    author=author.strip() if author else "",
                    content=content,
                    source=self.source,
                    tags=tags,
                    extracted_at=datetime.now().isoformat()
                )
                
        except Exception as e:
            logger.error(f"Error extracting article from {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title using configured selectors"""
        selectors = self.selectors.get('title', ['h1'])
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """Extract article summary using configured selectors"""
        selectors = self.selectors.get('summary', [
            'meta[name="description"]',
            'meta[property="og:description"]'
        ])
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_published_date(self, soup: BeautifulSoup) -> str:
        """Extract published date using configured selectors"""
        selectors = self.selectors.get('published_date', ['time[datetime]'])
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    return datetime_attr
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author using configured selectors"""
        selectors = self.selectors.get('author', ['[rel="author"]'])
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content using configured selectors"""
        selectors = self.selectors.get('content', ['article', 'main'])
        
        content_parts = []
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                # Remove script and style elements
                for script in element(["script", "style", "nav", "aside", "footer"]):
                    script.decompose()
                
                text = element.get_text(strip=True)
                if len(text) > 50:  # Only include substantial text blocks
                    content_parts.append(text)
        
        return ' '.join(content_parts)
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags using configured selectors"""
        tags = []
        selectors = self.selectors.get('tags', [])
        
        # Try meta keywords first
        meta_keywords = soup.select_one('meta[name="keywords"]')
        if meta_keywords:
            keywords = meta_keywords.get('content', '')
            tags.extend([tag.strip() for tag in keywords.split(',') if tag.strip()])
        
        # Try configured tag selectors
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                tag = element.get_text(strip=True)
                if tag and len(tag) < 50:  # Reasonable tag length
                    tags.append(tag)
        
        return list(set(tags))  # Remove duplicates