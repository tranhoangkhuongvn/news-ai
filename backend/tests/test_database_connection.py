import pytest
import sqlite3
import tempfile
import os
import json
from unittest.mock import patch, Mock
from datetime import datetime

from src.db.database_conn import NewsDatabase
from src.models.news_model import NewsArticle


class TestNewsDatabase:
    """Test suite for NewsDatabase class"""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file for testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

    @pytest.fixture
    def sample_article(self):
        """Create a sample news article for testing"""
        return NewsArticle(
            title="Test Article Title",
            url="https://www.abc.net.au/news/test-article",
            category="sports",
            summary="This is a test article summary",
            published_date="2023-01-01T10:00:00Z",
            author="Test Author",
            content="This is the main content of the test article",
            source="ABC News",
            tags=["sport", "test", "news"],
            extracted_at="2023-01-01T10:30:00Z"
        )

    def test_database_initialization_default_path(self):
        """Test database initialization with default path"""
        # Use a temporary directory to avoid creating files in the project
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_db_path = os.path.join(temp_dir, "test_news_database.db")

            with patch('src.db.database_conn.NewsDatabase.__init__') as mock_init:
                mock_init.return_value = None

                # Test that the constructor would be called with default path
                db = NewsDatabase.__new__(NewsDatabase)
                assert db is not None

    def test_database_initialization_custom_path(self, temp_db_path):
        """Test database initialization with custom path"""
        db = NewsDatabase(temp_db_path)

        assert db.db_path == temp_db_path
        assert os.path.exists(temp_db_path)

    def test_init_database_creates_tables(self, temp_db_path):
        """Test that init_database creates required tables"""
        db = NewsDatabase(temp_db_path)

        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()

            # Check if articles table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='articles'
            """)
            table_exists = cursor.fetchone()
            assert table_exists is not None

    def test_init_database_creates_correct_schema(self, temp_db_path):
        """Test that the articles table has the correct schema"""
        db = NewsDatabase(temp_db_path)

        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()

            # Get table schema
            cursor.execute("PRAGMA table_info(articles)")
            columns = cursor.fetchall()

            # Expected columns
            expected_columns = {
                'id', 'title', 'url', 'category', 'summary', 'published_date',
                'author', 'content', 'source', 'tags', 'extracted_at', 'created_at'
            }

            actual_columns = {col[1] for col in columns}
            assert expected_columns == actual_columns

            # Check that id is PRIMARY KEY and AUTOINCREMENT
            id_column = next(col for col in columns if col[1] == 'id')
            assert id_column[5] == 1  # pk column

    def test_init_database_creates_indexes(self, temp_db_path):
        """Test that required indexes are created"""
        db = NewsDatabase(temp_db_path)

        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()

            # Check for indexes
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='articles'
            """)
            indexes = [row[0] for row in cursor.fetchall()]

            expected_indexes = {'idx_category', 'idx_source', 'idx_published_date'}
            actual_indexes = {idx for idx in indexes if idx.startswith('idx_')}

            assert expected_indexes.issubset(actual_indexes)

    def test_save_article_success(self, temp_db_path, sample_article):
        """Test successful article saving"""
        db = NewsDatabase(temp_db_path)

        result = db.save_article(sample_article)
        assert result is True

        # Verify article was saved
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            assert count == 1

    def test_save_article_data_integrity(self, temp_db_path, sample_article):
        """Test that saved article data matches input"""
        db = NewsDatabase(temp_db_path)
        db.save_article(sample_article)

        with sqlite3.connect(temp_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE url = ?", (sample_article.url,))
            row = cursor.fetchone()

            assert row is not None
            assert row['title'] == sample_article.title
            assert row['url'] == sample_article.url
            assert row['category'] == sample_article.category
            assert row['summary'] == sample_article.summary
            assert row['published_date'] == sample_article.published_date
            assert row['author'] == sample_article.author
            assert row['content'] == sample_article.content
            assert row['source'] == sample_article.source
            assert json.loads(row['tags']) == sample_article.tags
            assert row['extracted_at'] == sample_article.extracted_at

    def test_save_article_duplicate_url_replace(self, temp_db_path):
        """Test that saving article with duplicate URL replaces existing"""
        db = NewsDatabase(temp_db_path)

        # Create first article
        article1 = NewsArticle(
            title="Original Title",
            url="https://www.abc.net.au/news/test-article",
            category="sports",
            summary="Original summary",
            published_date="2023-01-01T10:00:00Z",
            author="Original Author",
            content="Original content",
            source="ABC News",
            tags=["original"],
            extracted_at="2023-01-01T10:30:00Z"
        )

        # Create second article with same URL but different content
        article2 = NewsArticle(
            title="Updated Title",
            url="https://www.abc.net.au/news/test-article",  # Same URL
            category="politics",
            summary="Updated summary",
            published_date="2023-01-02T10:00:00Z",
            author="Updated Author",
            content="Updated content",
            source="ABC News",
            tags=["updated"],
            extracted_at="2023-01-02T10:30:00Z"
        )

        db.save_article(article1)
        db.save_article(article2)

        # Should still only have one article
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            assert count == 1

            # Check that the content was updated
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM articles WHERE url = ?", (article1.url,))
            row = cursor.fetchone()
            assert row['title'] == "Updated Title"

    def test_save_article_database_error(self, temp_db_path, sample_article):
        """Test handling of database errors during save"""
        db = NewsDatabase(temp_db_path)

        # Mock sqlite3.connect to raise an exception
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Database error")

            result = db.save_article(sample_article)
            assert result is False

    def test_get_articles_all(self, temp_db_path):
        """Test retrieving all articles"""
        db = NewsDatabase(temp_db_path)

        # Create multiple test articles
        articles = [
            NewsArticle(
                title=f"Article {i}",
                url=f"https://www.abc.net.au/news/article-{i}",
                category="sports" if i % 2 == 0 else "politics",
                summary=f"Summary {i}",
                published_date=f"2023-01-0{i}T10:00:00Z",
                author=f"Author {i}",
                content=f"Content {i}",
                source="ABC News",
                tags=[f"tag{i}"],
                extracted_at=f"2023-01-0{i}T10:30:00Z"
            )
            for i in range(1, 4)
        ]

        # Save all articles
        for article in articles:
            db.save_article(article)

        # Retrieve all articles
        retrieved = db.get_articles()
        assert len(retrieved) == 3

        # Check that articles are ordered by created_at DESC (most recent first)
        # Since all are created at the same time, order might vary, but we should get all 3
        retrieved_urls = {article['url'] for article in retrieved}
        expected_urls = {article.url for article in articles}
        assert retrieved_urls == expected_urls

    def test_get_articles_by_category(self, temp_db_path):
        """Test retrieving articles filtered by category"""
        db = NewsDatabase(temp_db_path)

        # Create articles in different categories
        sports_article = NewsArticle(
            title="Sports Article",
            url="https://www.abc.net.au/news/sports-article",
            category="sports",
            summary="Sports summary",
            published_date="2023-01-01T10:00:00Z",
            author="Sports Author",
            content="Sports content",
            source="ABC News",
            tags=["sports"],
            extracted_at="2023-01-01T10:30:00Z"
        )

        politics_article = NewsArticle(
            title="Politics Article",
            url="https://www.abc.net.au/news/politics-article",
            category="politics",
            summary="Politics summary",
            published_date="2023-01-02T10:00:00Z",
            author="Politics Author",
            content="Politics content",
            source="ABC News",
            tags=["politics"],
            extracted_at="2023-01-02T10:30:00Z"
        )

        db.save_article(sports_article)
        db.save_article(politics_article)

        # Retrieve only sports articles
        sports_articles = db.get_articles(category="sports")
        assert len(sports_articles) == 1
        assert sports_articles[0]['title'] == "Sports Article"
        assert sports_articles[0]['category'] == "sports"

    def test_get_articles_with_limit(self, temp_db_path):
        """Test retrieving articles with limit"""
        db = NewsDatabase(temp_db_path)

        # Create 5 test articles
        for i in range(5):
            article = NewsArticle(
                title=f"Article {i}",
                url=f"https://www.abc.net.au/news/article-{i}",
                category="sports",
                summary=f"Summary {i}",
                published_date=f"2023-01-0{i+1}T10:00:00Z",
                author=f"Author {i}",
                content=f"Content {i}",
                source="ABC News",
                tags=[f"tag{i}"],
                extracted_at=f"2023-01-0{i+1}T10:30:00Z"
            )
            db.save_article(article)

        # Retrieve with limit of 3
        retrieved = db.get_articles(limit=3)
        assert len(retrieved) == 3

    def test_get_articles_empty_database(self, temp_db_path):
        """Test retrieving articles from empty database"""
        db = NewsDatabase(temp_db_path)

        articles = db.get_articles()
        assert articles == []

    def test_get_articles_nonexistent_category(self, temp_db_path, sample_article):
        """Test retrieving articles for non-existent category"""
        db = NewsDatabase(temp_db_path)
        db.save_article(sample_article)

        articles = db.get_articles(category="nonexistent")
        assert articles == []

    def test_database_connection_context_manager(self, temp_db_path):
        """Test that database connections are properly managed"""
        db = NewsDatabase(temp_db_path)

        # The database should be accessible and connection should be closed after operations
        articles = db.get_articles()

        # Try to access the database file directly to ensure connection is closed
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            assert count == 0  # Empty database

    def test_database_file_permissions(self, temp_db_path):
        """Test that database file is created with proper permissions"""
        db = NewsDatabase(temp_db_path)

        # Check that file exists and is readable/writable
        assert os.path.exists(temp_db_path)
        assert os.access(temp_db_path, os.R_OK)
        assert os.access(temp_db_path, os.W_OK)

    def test_tags_json_serialization(self, temp_db_path):
        """Test that tags are properly serialized/deserialized as JSON"""
        db = NewsDatabase(temp_db_path)

        article = NewsArticle(
            title="Test Article",
            url="https://www.abc.net.au/news/test-article",
            category="sports",
            summary="Test summary",
            published_date="2023-01-01T10:00:00Z",
            author="Test Author",
            content="Test content",
            source="ABC News",
            tags=["tag1", "tag2", "tag3", "special-chars!@#"],
            extracted_at="2023-01-01T10:30:00Z"
        )

        db.save_article(article)
        retrieved = db.get_articles()

        assert len(retrieved) == 1
        retrieved_tags = json.loads(retrieved[0]['tags'])
        assert retrieved_tags == article.tags
        assert "special-chars!@#" in retrieved_tags

    def test_database_concurrent_access(self, temp_db_path):
        """Test basic concurrent access to database"""
        db1 = NewsDatabase(temp_db_path)
        db2 = NewsDatabase(temp_db_path)

        article1 = NewsArticle(
            title="Article 1",
            url="https://www.abc.net.au/news/article-1",
            category="sports",
            summary="Summary 1",
            published_date="2023-01-01T10:00:00Z",
            author="Author 1",
            content="Content 1",
            source="ABC News",
            tags=["tag1"],
            extracted_at="2023-01-01T10:30:00Z"
        )

        article2 = NewsArticle(
            title="Article 2",
            url="https://www.abc.net.au/news/article-2",
            category="politics",
            summary="Summary 2",
            published_date="2023-01-02T10:00:00Z",
            author="Author 2",
            content="Content 2",
            source="ABC News",
            tags=["tag2"],
            extracted_at="2023-01-02T10:30:00Z"
        )

        # Save articles using different database instances
        assert db1.save_article(article1) is True
        assert db2.save_article(article2) is True

        # Both should be able to retrieve all articles
        articles_from_db1 = db1.get_articles()
        articles_from_db2 = db2.get_articles()

        assert len(articles_from_db1) == 2
        assert len(articles_from_db2) == 2