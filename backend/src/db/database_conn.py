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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    classification_method TEXT,
                    classification_confidence REAL,
                    classification_explanation TEXT,
                    manual_override BOOLEAN DEFAULT FALSE
                )
            """)

            # Add new columns to existing tables if they don't exist
            self._add_classification_columns(conn)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category ON articles(category);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source ON articles(source);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_published_date ON articles(published_date);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_classification_confidence ON articles(classification_confidence);
            """)

    def _add_classification_columns(self, conn):
        """Add classification columns to existing tables if they don't exist."""
        try:
            # Check if columns exist by trying to select them
            conn.execute("SELECT classification_method FROM articles LIMIT 1")
        except sqlite3.OperationalError:
            # Columns don't exist, add them
            logger.info("Adding classification columns to existing articles table")
            conn.execute("ALTER TABLE articles ADD COLUMN classification_method TEXT")
            conn.execute("ALTER TABLE articles ADD COLUMN classification_confidence REAL")
            conn.execute("ALTER TABLE articles ADD COLUMN classification_explanation TEXT")
            conn.execute("ALTER TABLE articles ADD COLUMN manual_override BOOLEAN DEFAULT FALSE")

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

    def save_article_with_classification(self, article: NewsArticle,
                                       classification_result=None) -> bool:
        """Save an article with classification information to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if classification_result:
                    conn.execute("""
                        INSERT OR REPLACE INTO articles
                        (title, url, category, summary, published_date, author, content, source, tags, extracted_at,
                         classification_method, classification_confidence, classification_explanation)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article.title, article.url, classification_result.category, article.summary,
                        article.published_date, article.author, article.content,
                        article.source, json.dumps(article.tags), article.extracted_at,
                        classification_result.method_used, classification_result.confidence,
                        classification_result.explanation
                    ))
                else:
                    # Fallback to original save method
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
            logger.error(f"Error saving article with classification to database: {e}")
            return False

    def update_article_classification(self, article_id: int, classification_result,
                                    manual_override: bool = False) -> bool:
        """Update classification information for an existing article"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE articles
                    SET category = ?, classification_method = ?, classification_confidence = ?,
                        classification_explanation = ?, manual_override = ?
                    WHERE id = ?
                """, (
                    classification_result.category, classification_result.method_used,
                    classification_result.confidence, classification_result.explanation,
                    manual_override, article_id
                ))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating article classification: {e}")
            return False

    def get_articles_for_reclassification(self, limit: int = 100) -> List[Dict]:
        """Get articles that need reclassification (no classification data)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM articles
                WHERE classification_method IS NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_classification_stats(self) -> Dict:
        """Get statistics about article classifications"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}

            # Total articles
            cursor = conn.execute("SELECT COUNT(*) FROM articles")
            stats['total_articles'] = cursor.fetchone()[0]

            # Articles with classification data
            cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE classification_method IS NOT NULL")
            stats['classified_articles'] = cursor.fetchone()[0]

            # By category
            cursor = conn.execute("""
                SELECT category, COUNT(*)
                FROM articles
                GROUP BY category
                ORDER BY COUNT(*) DESC
            """)
            stats['by_category'] = dict(cursor.fetchall())

            # By classification method
            cursor = conn.execute("""
                SELECT classification_method, COUNT(*)
                FROM articles
                WHERE classification_method IS NOT NULL
                GROUP BY classification_method
            """)
            stats['by_method'] = dict(cursor.fetchall())

            # Average confidence by category
            cursor = conn.execute("""
                SELECT category, AVG(classification_confidence)
                FROM articles
                WHERE classification_confidence IS NOT NULL
                GROUP BY category
            """)
            stats['avg_confidence_by_category'] = {
                cat: round(conf, 3) for cat, conf in cursor.fetchall()
            }

            return stats
