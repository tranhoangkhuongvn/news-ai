import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from bs4 import BeautifulSoup
import aiohttp
from datetime import datetime

from src.scrapers.aussie_news_extractor import ABCNewsExtractor
from src.models.news_model import NewsArticle


class TestABCNewsExtractor:
    """Test suite for ABCNewsExtractor class"""

    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp session"""
        session = Mock(spec=aiohttp.ClientSession)
        return session

    @pytest.fixture
    def extractor(self, mock_session):
        """Create an ABCNewsExtractor instance with mock session"""
        return ABCNewsExtractor(mock_session)

    def test_get_source_name(self, extractor):
        """Test that get_source_name returns correct source name"""
        assert extractor.get_source_name() == "ABC News"

    def test_get_base_url(self, extractor):
        """Test that get_base_url returns correct base URL"""
        assert extractor.get_base_url() == "https://www.abc.net.au"

    def test_get_category_urls(self, extractor):
        """Test that get_category_urls returns expected categories"""
        categories = extractor.get_category_urls()

        expected_categories = {
            "sports": "/news/sport",
            "lifestyle": "/news/health",
            "music": "/news/music",
            "finance": "/news/business"
        }

        assert categories == expected_categories
        assert isinstance(categories, dict)
        assert len(categories) == 4

    def test_get_selectors(self, extractor):
        """Test that get_selectors returns expected CSS selectors"""
        selectors = extractor.get_selectors()

        # Check that all required selector types are present
        required_selector_types = ['title', 'summary', 'published_date', 'author', 'content', 'tags']
        for selector_type in required_selector_types:
            assert selector_type in selectors
            assert isinstance(selectors[selector_type], list)
            assert len(selectors[selector_type]) > 0

        # Check specific selectors
        assert 'h1' in selectors['title']
        assert '.ArticleHeader_title' in selectors['title']
        assert '[data-component="Headline"]' in selectors['title']

    def test_initialization(self, mock_session):
        """Test that extractor initializes correctly"""
        extractor = ABCNewsExtractor(mock_session)

        assert extractor.session == mock_session
        assert extractor.source == "ABC News"
        assert extractor.base_url == "https://www.abc.net.au"
        assert isinstance(extractor.category_urls, dict)
        assert isinstance(extractor.selectors, dict)

    def test_get_article_links_from_category_page_with_valid_links(self, extractor):
        """Test article link extraction with valid HTML"""
        html_content = """
        <html>
            <body>
                <a href="/news/sport/article-1">Sport Article 1</a>
                <a href="/news/health/article-2">Health Article 2</a>
                <div class="ContentHub_articles">
                    <a href="/news/politics/article-3">Politics Article</a>
                </div>
                <div class="FeaturedContent_item">
                    <a href="/news/business/article-4">Business Article</a>
                </div>
                <a href="/other/page">Non-news link</a>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        category_url = "https://www.abc.net.au/news/sport"

        links = extractor.get_article_links_from_category_page(soup, category_url)

        # Should return full URLs for news articles
        expected_links = [
            "https://www.abc.net.au/news/sport/article-1",
            "https://www.abc.net.au/news/health/article-2",
            "https://www.abc.net.au/news/politics/article-3",
            "https://www.abc.net.au/news/business/article-4"
        ]

        assert len(links) == 4
        for expected_link in expected_links:
            assert expected_link in links

    def test_get_article_links_from_category_page_no_links(self, extractor):
        """Test article link extraction with no valid links"""
        html_content = """
        <html>
            <body>
                <a href="/other/page">Non-news link</a>
                <a href="/about">About page</a>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        category_url = "https://www.abc.net.au/news/sport"

        links = extractor.get_article_links_from_category_page(soup, category_url)

        assert links == []

    def test_get_article_links_from_category_page_duplicate_removal(self, extractor):
        """Test that duplicate links are removed"""
        html_content = """
        <html>
            <body>
                <a href="/news/sport/article-1">Sport Article 1</a>
                <a href="/news/sport/article-1">Sport Article 1 Duplicate</a>
                <div class="ContentHub_articles">
                    <a href="/news/sport/article-1">Sport Article 1 Again</a>
                </div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        category_url = "https://www.abc.net.au/news/sport"

        links = extractor.get_article_links_from_category_page(soup, category_url)

        assert len(links) == 1
        assert "https://www.abc.net.au/news/sport/article-1" in links

    def test_validate_article_url_valid_urls(self, extractor):
        """Test URL validation with valid ABC News URLs"""
        valid_urls = [
            "https://www.abc.net.au/news/sport/article-123",
            "https://www.abc.net.au/news/health/some-article",
            "https://www.abc.net.au/news/business/long-article-title-that-meets-length-requirement"
        ]

        for url in valid_urls:
            assert extractor.validate_article_url(url)

    def test_validate_article_url_invalid_urls(self, extractor):
        """Test URL validation with invalid URLs"""
        invalid_urls = [
            "https://www.cnn.com/news/article",  # Wrong domain
            "https://www.abc.net.au/other/page",  # No /news/
            "http://short.url",  # Too short
            "https://abc.net.au/news/business/article"  # Missing www subdomain
        ]

        for url in invalid_urls:
            assert not extractor.validate_article_url(url)

    @pytest.mark.asyncio
    async def test_extract_category_articles_success(self, extractor, mock_session):
        """Test successful category article extraction"""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="""
            <html>
                <body>
                    <a href="/news/sport/article-1">Article 1</a>
                    <a href="/news/sport/article-2">Article 2</a>
                </body>
            </html>
        """)

        # Mock the context manager
        mock_session.get.return_value = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        # Mock extract_single_article to return NewsArticle objects
        mock_article_1 = NewsArticle(
            title="Test Article 1",
            url="https://www.abc.net.au/news/sport/article-1",
            category="sports",
            summary="Test summary 1",
            published_date="2023-01-01",
            author="Test Author",
            content="Test content 1",
            source="ABC News",
            tags=["sport"],
            extracted_at="2023-01-01T00:00:00"
        )

        mock_article_2 = NewsArticle(
            title="Test Article 2",
            url="https://www.abc.net.au/news/sport/article-2",
            category="sports",
            summary="Test summary 2",
            published_date="2023-01-02",
            author="Test Author 2",
            content="Test content 2",
            source="ABC News",
            tags=["sport"],
            extracted_at="2023-01-02T00:00:00"
        )

        with patch.object(extractor, 'extract_single_article', new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = [mock_article_1, mock_article_2]

            articles = await extractor.extract_category_articles("sports", max_articles=5)

            assert len(articles) == 2
            assert all(isinstance(article, NewsArticle) for article in articles)
            assert articles[0].title == "Test Article 1"
            assert articles[1].title == "Test Article 2"

    @pytest.mark.asyncio
    async def test_extract_category_articles_invalid_category(self, extractor):
        """Test extraction with invalid category"""
        articles = await extractor.extract_category_articles("invalid_category")
        assert articles == []

    @pytest.mark.asyncio
    async def test_extract_category_articles_http_error(self, extractor, mock_session):
        """Test extraction with HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 404

        # Mock the context manager
        mock_session.get.return_value = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        articles = await extractor.extract_category_articles("sports")
        assert articles == []

    @pytest.mark.asyncio
    async def test_extract_single_article_success(self, extractor, mock_session):
        """Test successful single article extraction"""
        article_html = """
        <html>
            <head>
                <meta name="description" content="Test article summary">
            </head>
            <body>
                <h1>Test Article Title</h1>
                <time datetime="2023-01-01T10:00:00Z">January 1, 2023</time>
                <div data-component="Byline">Test Author</div>
                <article>This is the main article content with enough text to be considered substantial.</article>
            </body>
        </html>
        """

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=article_html)

        # Mock the context manager
        mock_session.get.return_value = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        url = "https://www.abc.net.au/news/sport/test-article"
        article = await extractor.extract_single_article(url, "sports")

        assert article is not None
        assert isinstance(article, NewsArticle)
        assert article.title == "Test Article Title"
        assert article.url == url
        assert article.category == "sports"
        assert article.source == "ABC News"
        assert "Test article summary" in article.summary
        assert article.author == "Test Author"
        assert "main article content" in article.content

    @pytest.mark.asyncio
    async def test_extract_single_article_http_error(self, extractor, mock_session):
        """Test single article extraction with HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 404

        # Mock the context manager
        mock_session.get.return_value = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        url = "https://www.abc.net.au/news/sport/test-article"
        article = await extractor.extract_single_article(url, "sports")

        assert article is None

    @pytest.mark.asyncio
    async def test_extract_single_article_insufficient_title(self, extractor, mock_session):
        """Test single article extraction with insufficient title"""
        article_html = """
        <html>
            <body>
                <h1>Bad</h1>
                <article>Some content</article>
            </body>
        </html>
        """

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=article_html)

        # Mock the context manager
        mock_session.get.return_value = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        url = "https://www.abc.net.au/news/sport/test-article"
        article = await extractor.extract_single_article(url, "sports")

        # Should return None due to insufficient title length (< 5 chars)
        assert article is None

    def test_preprocess_content(self, extractor):
        """Test content preprocessing"""
        raw_content = """
        This is some content with    extra spaces.

        ADVERTISEMENT

        More content here.    Subscribe to our newsletter!

        Related Articles: Some links here
        """

        processed = extractor.preprocess_content(raw_content)

        # Should remove extra whitespace and unwanted patterns
        assert "ADVERTISEMENT" not in processed
        assert "Subscribe" not in processed
        assert "Related Articles" not in processed
        assert "extra spaces" in processed
        assert "More content here" in processed

    def test_extract_date_from_text(self, extractor):
        """Test date extraction and normalization"""
        # Test valid date
        date_text = "2023-01-01T10:00:00Z"
        result = extractor.extract_date_from_text(date_text)
        assert "2023-01-01" in result

        # Test empty date
        assert extractor.extract_date_from_text("") == ""

        # Test None date
        assert extractor.extract_date_from_text(None) == ""

    def test_get_article_links_handles_relative_urls(self, extractor):
        """Test that relative URLs are converted to absolute URLs"""
        html_content = """
        <html>
            <body>
                <a href="/news/sport/relative-article">Relative Article</a>
                <a href="https://www.abc.net.au/news/sport/absolute-article">Absolute Article</a>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        category_url = "https://www.abc.net.au/news/sport"

        links = extractor.get_article_links_from_category_page(soup, category_url)

        # Both should be absolute URLs
        assert "https://www.abc.net.au/news/sport/relative-article" in links
        assert "https://www.abc.net.au/news/sport/absolute-article" in links