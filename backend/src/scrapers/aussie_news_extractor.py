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
                '[data-component="Text"] p',
                '[data-component="Text"]',
                '.ArticleBody_container p',
                '.ArticleBody_container',
                '.RichText p',
                '.RichText',
                'article p',
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

                    # Enhanced filtering for actual articles only
                    if (self._is_valid_abc_article_url(full_url)):
                        article_links.add(full_url)

        return list(article_links)

    def _is_valid_abc_article_url(self, url: str) -> bool:
        """Enhanced URL validation for ABC News articles"""
        import re

        # Skip non-article pages
        excluded_patterns = [
            '/news/emergency', '/news/sport/', '/news/business/', '/news/health/',
            '/news/music/', '/news/tok-pisin', '/news/rural', '/news/analysis-and-opinion',
            '/news/corrections', '/news/contact', '/news/about', '/news/for-you',
            '/news/weather', '/news/radio', '/news/tv', '/topic/', '/categories/',
            '/news/entertainment/', '/news/politics/', '/news/science/', '/news/arts/',
            '/news/religion/', '/news/environment/'
        ]

        # Check if URL contains any excluded patterns
        for pattern in excluded_patterns:
            if pattern in url:
                return False

        # Skip anchor links and query parameters
        if '#' in url or '?' in url:
            return False

        # ABC article URLs typically have date patterns or numeric IDs
        # Pattern: /news/YYYY-MM-DD/article-title/NNNNNNNN or similar
        abc_article_pattern = r'/news/\d{4}-\d{2}-\d{2}/[^/]+/\d+$'

        if re.search(abc_article_pattern, url):
            return True

        # Alternative pattern: URLs with substantive content slug and numeric ID
        # Must have a meaningful slug (more than just category) and end with numbers
        url_parts = url.split('/')
        if len(url_parts) >= 5 and url_parts[-1].isdigit() and len(url_parts[-1]) >= 6:
            # Check that the URL has date and title components
            for part in url_parts:
                if re.match(r'\d{4}-\d{2}-\d{2}', part):
                    return True

        return False

    def validate_article_url(self, url: str) -> bool:
        """ABC-specific URL validation"""
        url_slug = url.split('/')[-1]

        # Exclude known non-article patterns
        excluded_patterns = [
            'tok-pisin', 'analysis-and-opinion', 'sport', 'business', 'health', 'music',
            'lifestyle', 'entertainment', 'politics', 'rural', 'science', 'arts', 'religion',
            'corrections', 'contact', 'about', 'editorial', 'weather', 'radio', 'tv', 'for-you',
            'ashes', 'rugby-league', 'environment', 'rugby-union-world-cup', 'nrl'
        ]

        # ABC News uses numeric article IDs or descriptive slugs
        return (
            'abc.net.au' in url and
            '/news/' in url and
            '/topic/' not in url and
            '#' not in url and
            url_slug not in excluded_patterns and
            (
                # Either numeric article ID (at least 8 digits)
                (url_slug.isdigit() and len(url_slug) >= 8) or
                # Or descriptive slug with dashes (at least 2 dashes for specificity)
                ('-' in url_slug and url_slug.count('-') >= 2 and len(url_slug) > 8)
            )
        )

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
                '.content__article-body p',
                '.content__article-body',
                '[data-component="text-block"]',
                'article .content__main',
                '.article-body-commercial-selector',
                '.content__main-column p'
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
                    if ('/australia-news/' in full_url or '/music' in full_url or '/sport' in full_url or '/lifeandstyle' in full_url or '/business' in full_url) and len(full_url) > 50:
                        article_links.add(full_url)

        return list(article_links)
    
    def validate_article_url(self, url: str) -> bool:
        """Guardian-specific URL validation"""
        return (
            'theguardian.com' in url and
            any(path in url for path in ['/australia-news/', '/music/', '/sport/', '/lifeandstyle/', '/business/']) and
            '/live/' not in url and  # Exclude live blogs
            '/gallery/' not in url and  # Exclude photo galleries
            '/series/' not in url and  # Exclude series pages
            len(url.split('/')[-1]) > 10  # Ensure URL has a substantial article slug
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
                'meta[name="description"]',
                'meta[property="og:description"]',
                '.story-subtitle',
                '.article-subtitle'
            ],
            'published_date': [
                'time[datetime]',
                '.timestamp',
                '.story-info time'
            ],
            'author': [
                '[data-module="Byline"] a',
                '.byline a',
                '.story-byline a',
                '.author-name',
                '[rel="author"]'
            ],
            'content': [
                'div[class*="story"] p',  # News.com.au uses div with story-related classes
                'article p',             # Article paragraphs as fallback
                'div[class*="content"] p', # Content div paragraphs
                '.story-body',           # Legacy selector
                '.article-content',      # Legacy selector
                '.story-content'         # Legacy selector
            ],
            'tags': [
                '.topics a',
                '.story-topics a',
                '.article-tags a'
            ]
        }
    
    def get_article_links_from_category_page(self, soup: BeautifulSoup, category_url: str) -> List[str]:
        """News.com.au specific method to extract article links"""
        article_links = set()

        # Updated selectors for current News.com.au structure
        selectors = [
            'a[href*="/news-story/"]',  # Current URL pattern
            'a[href*="/story/"]',       # Legacy pattern
            '.story-block a',
            '.module-story a',
            '.story-headline-link',
            'h3 a',                     # Headline links
            '.headline a'               # Alternative headline links
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if ('/news-story/' in full_url or '/story/' in full_url):
                        article_links.add(full_url)

        return list(article_links)
    
    def validate_article_url(self, url: str) -> bool:
        """News.com.au specific URL validation"""
        return (
            'news.com.au' in url and
            ('/news-story/' in url or '/story/' in url) and
            len(url) > 50 and
            any(path in url for path in ['/sport/', '/lifestyle/', '/entertainment/', '/finance/', '/business/']) and
            not url.endswith('/')  # Avoid category pages
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
                '.article-body',
                '.story-body',
                '.content-body',
                'div[class*="story"] p',
                'article p',
                '.story-content p'
            ],
            'tags': [
                '.topics a',
                '.article-tags a'
            ]
        }
    
    def get_article_links_from_category_page(self, soup: BeautifulSoup, category_url: str) -> List[str]:
        """SMH specific method to extract article links"""
        article_links = set()

        # Updated selectors for current SMH website structure
        selectors = [
            'a[href*="/2025/"]',  # Current year articles
            'a[href*="/2024/"]',  # Recent articles
            'a[href*="-p5"]',     # SMH article ID pattern
            'h3 a',               # Headline links
            '.story-link',        # Legacy selector
            '[data-component="Link"]'  # Component-based links
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    # Enhanced filtering for SMH URL patterns
                    if self._is_valid_smh_article_url(full_url):
                        article_links.add(full_url)

        return list(article_links)

    def _is_valid_smh_article_url(self, url: str) -> bool:
        """Enhanced URL validation for SMH articles"""
        import re

        # Skip non-article pages
        excluded_patterns = [
            '/sport/', '/lifestyle/', '/culture/', '/business/',  # Category pages themselves
            '/politics/', '/national/', '/world/', '/technology/',
            '/property/', '/environment/', '/entertainment/',
            '/subscribe', '/premium', '/plus', '/account',
            '/newsletters', '/contact', '/about'
        ]

        # Check if URL is a category page (exact match)
        for pattern in excluded_patterns:
            if url.endswith(pattern) or url.endswith(pattern.rstrip('/')):
                return False

        # Skip URLs with query parameters or fragments
        if '?' in url or '#' in url:
            return False

        # SMH article URLs should contain category and have proper article structure
        valid_categories = ['/sport/', '/lifestyle/', '/culture/', '/business/']
        has_valid_category = any(cat in url for cat in valid_categories)

        if not has_valid_category:
            return False

        # SMH article URLs typically have specific patterns:
        # 1. /category/YYYY/MM/DD/article-title-p5XXXXXXX.html
        # 2. /category/article-title-p5XXXXXXX-h2YYYYYY.html
        # 3. /category/YYYYMMDD/article-title-p5XXXXXXX.html

        smh_patterns = [
            r'/\d{4}/\d{2}/\d{2}/[^/]+-p5[a-z0-9]+\.html$',  # Standard date pattern
            r'/[^/]+-p5[a-z0-9]+-h2[a-z0-9]+\.html$',        # Article with hash
            r'/\d{8}/[^/]+-p5[a-z0-9]+\.html$',              # Compact date format
            r'/[^/]+-p5[a-z0-9]+\.html$'                     # Simple article pattern
        ]

        for pattern in smh_patterns:
            if re.search(pattern, url):
                return True

        # Alternative: check for recent articles with date indicators
        if re.search(r'/(202[4-5]|2025)/', url) and len(url) > 50:
            return True

        return False

    def validate_article_url(self, url: str) -> bool:
        """SMH-specific URL validation"""
        return (
            'smh.com.au' in url and
            ('-p5' in url or '/20' in url) and  # SMH article patterns
            any(path in url for path in ['/sport/', '/lifestyle/', '/culture/', '/business/']) and
            len(url) > 50 and
            not url.endswith('/') and  # Avoid category pages
            'live-updates' not in url  # Skip live blog pages for now
        )
    

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