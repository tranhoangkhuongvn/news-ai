from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import aiohttp

from src.scrapers.base_extractor import BaseNewsExtractor

# Configure logging
logger = logging.getLogger(__name__)
MAX_ARTICLES = 30

class ABCNewsExtractor(BaseNewsExtractor):
    """ABC News specific extractor"""
    
    def get_source_name(self) -> str:
        return "ABC News"
    
    def get_base_url(self) -> str:
        return "https://www.abc.net.au"
    
    def get_category_urls(self) -> Dict[str, str]:
        return {
            "sports": "/news/sport",
            "lifestyle": "/news/health",  # ABC combines health/lifestyle
            "music": "/news/music",
            "finance": "/news/business"
        }
    
    def get_selectors(self) -> Dict[str, List[str]]:
        return {
            'title': [
                'h1',
                '.ArticleHeader_title',
                '[data-component="Headline"]'
            ],
            'summary': [
                '[data-component="Abstract"]',
                '.ArticleHeader_abstract',
                'meta[name="description"]',
                'meta[property="og:description"]'
            ],
            'published_date': [
                'time[datetime]',
                '[data-component="Timestamp"]',
                '.ArticleHeader_timestamp'
            ],
            'author': [
                '[data-component="Byline"]',
                '.ArticleHeader_byline',
                '[rel="author"]'
            ],
            'content': [
                '[data-component="Text"]',
                '.ArticleBody_container',
                '.RichText',
                'article'
            ],
            'tags': [
                '.TopicTags_link',
                '.ArticleTags_tag'
            ]
        }
    
    def get_article_links_from_category_page(self, soup: BeautifulSoup, category_url: str) -> List[str]:
        """ABC News specific method to extract article links from category pages"""
        article_links = set()
        
        # Multiple selectors to catch different article types on ABC News
        selectors = [
            'a[href*="/news/"]',
            '.ContentHub_articles a',
            '.FeaturedContent_item a',
            '.Card_link',
            '.Article_link',
            '.Story_link'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and '/news/' in href:
                    full_url = urljoin(self.base_url, href)
                    article_links.add(full_url)
        
        return list(article_links)

class GuardianAUExtractor(BaseNewsExtractor):
    """The Guardian Australia specific extractor"""
    
    def get_source_name(self) -> str:
        return "The Guardian AU"
    
    def get_base_url(self) -> str:
        return "https://www.theguardian.com"
    
    def get_category_urls(self) -> Dict[str, str]:
        return {
            "sports": "/au/sport",
            "lifestyle": "/au/lifeandstyle",
            "music": "/music/australian-music",
            "finance": "/au/business"
        }
    
    def get_selectors(self) -> Dict[str, List[str]]:
        return {
            'title': [
                'h1',
                '[data-component="headline"]',
                '.content__headline'
            ],
            'summary': [
                '[data-component="standfirst"]',
                '.content__standfirst',
                'meta[name="description"]',
                'meta[property="og:description"]'
            ],
            'published_date': [
                'time[datetime]',
                '.content__dateline time',
                '[data-component="timestamp"]'
            ],
            'author': [
                '[rel="author"]',
                '.byline a',
                '[data-component="contributor-link"]'
            ],
            'content': [
                '.content__article-body',
                '[data-component="text-block"]',
                'article .content__main'
            ],
            'tags': [
                '.submeta__keywords a',
                '[data-component="tag"]'
            ]
        }
    
    def get_article_links_from_category_page(self, soup: BeautifulSoup, category_url: str) -> List[str]:
        """Guardian AU specific method to extract article links"""
        article_links = set()
        
        selectors = [
            '.fc-item__link',
            '.u-faux-block-link__overlay',
            'a[data-link-name="article"]',
            '.headline-link'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    # Guardian uses relative URLs
                    if href.startswith('/'):
                        full_url = urljoin(self.base_url, href)
                    else:
                        full_url = href
                    
                    # Filter for Australian content and valid articles
                    if ('/australia-news/' in full_url or '/music' in full_url) and len(full_url) > MAX_ARTICLES:
                        article_links.add(full_url)
        
        return list(article_links)
    
    def validate_article_url(self, url: str) -> bool:
        """Guardian-specific URL validation"""
        return (
            'theguardian.com' in url and
            any(path in url for path in ['/australia-news/', '/music/', '/sport/']) and
            '/live/' not in url and  # Exclude live blogs
            '/gallery/' not in url  # Exclude photo galleries
        )

class NewsComAUExtractor(BaseNewsExtractor):
    """News.com.au specific extractor"""
    
    def get_source_name(self) -> str:
        return "News.com.au"
    
    def get_base_url(self) -> str:
        return "https://www.news.com.au"
    
    def get_category_urls(self) -> Dict[str, str]:
        return {
            "sports": "/sport",
            "lifestyle": "/lifestyle",
            "music": "/entertainment/music",
            "finance": "/finance"
        }
    
    def get_selectors(self) -> Dict[str, List[str]]:
        return {
            'title': [
                'h1',
                '.story-headline',
                '.article-title'
            ],
            'summary': [
                '.story-subtitle',
                '.article-subtitle',
                'meta[name="description"]',
                'meta[property="og:description"]'
            ],
            'published_date': [
                'time[datetime]',
                '.timestamp',
                '.story-info time'
            ],
            'author': [
                '.story-byline a',
                '.author-name',
                '[rel="author"]'
            ],
            'content': [
                '.story-body',
                '.article-content',
                '.story-content'
            ],
            'tags': [
                '.story-topics a',
                '.article-tags a'
            ]
        }
    
    def get_article_links_from_category_page(self, soup: BeautifulSoup, category_url: str) -> List[str]:
        """News.com.au specific method to extract article links"""
        article_links = set()
        
        selectors = [
            '.story-block a',
            '.module-story a',
            '.story-headline-link',
            'a[href*="/story/"]'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if '/story/' in full_url:
                        article_links.add(full_url)
        
        return list(article_links)
    
    def validate_article_url(self, url: str) -> bool:
        """News.com.au specific URL validation"""
        return (
            'news.com.au' in url and
            '/story/' in url and
            len(url) > 25
        )

class SMHExtractor(BaseNewsExtractor):
    """Sydney Morning Herald specific extractor"""
    
    def get_source_name(self) -> str:
        return "Sydney Morning Herald"
    
    def get_base_url(self) -> str:
        return "https://www.smh.com.au"
    
    def get_category_urls(self) -> Dict[str, str]:
        return {
            "sports": "/sport",
            "lifestyle": "/lifestyle",
            "music": "/culture/music",
            "finance": "/business"
        }
    
    def get_selectors(self) -> Dict[str, List[str]]:
        return {
            'title': [
                'h1',
                '[data-component="Headline"]',
                '.article-header h1'
            ],
            'summary': [
                '[data-component="Standfirst"]',
                '.article-intro',
                'meta[name="description"]'
            ],
            'published_date': [
                'time[datetime]',
                '[data-component="Timestamp"]'
            ],
            'author': [
                '[data-component="Byline"] a',
                '.author-name'
            ],
            'content': [
                '[data-component="TextBlock"]',
                '.article-body'
            ],
            'tags': [
                '.topics a',
                '.article-tags a'
            ]
        }
    
    def get_article_links_from_category_page(self, soup: BeautifulSoup, category_url: str) -> List[str]:
        """SMH specific method to extract article links"""
        article_links = set()
        
        selectors = [
            'a[href*="/story/"]',
            '.story-link',
            '[data-component="Link"]'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if any(path in full_url for path in ['/sport/', '/lifestyle/', '/culture/', '/business/']):
                        article_links.add(full_url)
        
        return list(article_links)
    

class ExtractorFactory:
    """Factory class for creating news extractors"""
    
    _extractors = {
        'abc': ABCNewsExtractor,
        'guardian': GuardianAUExtractor,
        'news_com_au': NewsComAUExtractor,
        'smh': SMHExtractor
    }
    
    @classmethod
    def create_extractor(cls, source: str, session: aiohttp.ClientSession) -> BaseNewsExtractor:
        """Create an extractor instance for the specified source"""
        if source not in cls._extractors:
            raise ValueError(f"Unknown news source: {source}. Available sources: {list(cls._extractors.keys())}")
        
        extractor_class = cls._extractors[source]
        return extractor_class(session)
    
    @classmethod
    def get_available_sources(cls) -> List[str]:
        """Get list of available news sources"""
        return list(cls._extractors.keys())
    
    @classmethod
    def register_extractor(cls, source: str, extractor_class: type):
        """Register a new extractor class"""
        if not issubclass(extractor_class, BaseNewsExtractor):
            raise ValueError("Extractor class must inherit from BaseNewsExtractor")
        
        cls._extractors[source] = extractor_class
        logger.info(f"Registered new extractor: {source}")