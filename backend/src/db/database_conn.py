import sqlite3
import logging
from src.models.news_model import NewsArticle
import json
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_connection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsDatabase:
    """SQLite database handler for storing extracted news"""
    
    def __init__(self, db_path: str = "news_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    summary TEXT,
                    published_date TEXT,
                    author TEXT,
                    content TEXT,
                    source TEXT NOT NULL,
                    tags TEXT,
                    extracted_at TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category ON articles(category);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source ON articles(source);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_published_date ON articles(published_date);
            """)
    
    def save_article(self, article: NewsArticle) -> bool:
        """Save an article to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO articles 
                    (title, url, category, summary, published_date, author, content, source, tags, extracted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.title, article.url, article.category, article.summary,
                    article.published_date, article.author, article.content,
                    article.source, json.dumps(article.tags), article.extracted_at
                ))
            return True
        except Exception as e:
            logger.error(f"Error saving article to database: {e}")
            return False
    
    def get_articles(self, category: str = None, limit: int = 100) -> List[Dict]:
        """Retrieve articles from the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if category:
                cursor = conn.execute("""
                    SELECT * FROM articles WHERE category = ? 
                    ORDER BY created_at DESC LIMIT ?
                """, (category, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM articles ORDER BY created_at DESC LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
