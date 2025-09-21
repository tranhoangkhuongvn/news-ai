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
            self._add_similarity_tables(conn)

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

    def _add_similarity_tables(self, conn):
        """Add similarity tables for article similarity detection."""
        try:
            # Create article_similarities table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS article_similarities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id_1 INTEGER NOT NULL,
                    article_id_2 INTEGER NOT NULL,
                    similarity_score REAL NOT NULL,
                    title_similarity REAL NOT NULL,
                    keyword_similarity REAL NOT NULL,
                    time_similarity REAL NOT NULL,
                    similarity_method TEXT NOT NULL,
                    explanation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id_1) REFERENCES articles(id),
                    FOREIGN KEY (article_id_2) REFERENCES articles(id),
                    UNIQUE(article_id_1, article_id_2)
                )
            """)

            # Create article_clusters table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS article_clusters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cluster_id TEXT UNIQUE NOT NULL,
                    main_article_id INTEGER NOT NULL,
                    cluster_score REAL NOT NULL,
                    summary TEXT,
                    sources_covered TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (main_article_id) REFERENCES articles(id)
                )
            """)

            # Create cluster_articles table (many-to-many)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cluster_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cluster_id TEXT NOT NULL,
                    article_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(id),
                    UNIQUE(cluster_id, article_id)
                )
            """)

            # Create indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_similarities_article1 ON article_similarities(article_id_1);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_similarities_article2 ON article_similarities(article_id_2);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_similarities_score ON article_similarities(similarity_score);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_clusters_main_article ON article_clusters(main_article_id);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cluster_articles_cluster ON cluster_articles(cluster_id);
            """)

            logger.info("Successfully created similarity tables and indexes")

        except sqlite3.OperationalError as e:
            # Tables might already exist
            logger.debug(f"Similarity tables might already exist: {e}")

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

    def save_similarity(self, similarity_result) -> bool:
        """Save similarity result to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO article_similarities
                    (article_id_1, article_id_2, similarity_score, title_similarity,
                     keyword_similarity, time_similarity, similarity_method, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    similarity_result.article_id_1,
                    similarity_result.article_id_2,
                    similarity_result.similarity_score,
                    similarity_result.title_similarity,
                    similarity_result.keyword_similarity,
                    similarity_result.time_similarity,
                    similarity_result.method_used,
                    similarity_result.explanation
                ))
            return True
        except Exception as e:
            logger.error(f"Error saving similarity result: {e}")
            return False

    def get_similar_articles(self, article_id: int, limit: int = 10) -> List[Dict]:
        """Get articles similar to the specified article."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT s.*, a.title, a.source, a.category, a.summary, a.url, a.published_date
                FROM article_similarities s
                JOIN articles a ON (
                    CASE
                        WHEN s.article_id_1 = ? THEN a.id = s.article_id_2
                        WHEN s.article_id_2 = ? THEN a.id = s.article_id_1
                        ELSE 0
                    END
                )
                WHERE s.article_id_1 = ? OR s.article_id_2 = ?
                ORDER BY s.similarity_score DESC
                LIMIT ?
            """, (article_id, article_id, article_id, article_id, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_similarities(self, limit: int = 50) -> List[Dict]:
        """Get recent similarity results."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM article_similarities
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def save_article_cluster(self, cluster) -> bool:
        """Save article cluster to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Save cluster metadata
                conn.execute("""
                    INSERT OR REPLACE INTO article_clusters
                    (cluster_id, main_article_id, cluster_score, summary, sources_covered)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    cluster.cluster_id,
                    cluster.main_article_id,
                    cluster.cluster_score,
                    cluster.summary,
                    ','.join(cluster.sources_covered)
                ))

                # Save cluster article relationships
                for article_id in cluster.similar_articles:
                    conn.execute("""
                        INSERT OR REPLACE INTO cluster_articles
                        (cluster_id, article_id)
                        VALUES (?, ?)
                    """, (cluster.cluster_id, article_id))

            return True
        except Exception as e:
            logger.error(f"Error saving article cluster: {e}")
            return False

    def get_article_clusters(self, limit: int = 10) -> List[Dict]:
        """Get article clusters with their associated articles."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get cluster metadata
            cursor = conn.execute("""
                SELECT c.*, a.title as main_title, a.source as main_source
                FROM article_clusters c
                JOIN articles a ON c.main_article_id = a.id
                ORDER BY c.created_at DESC
                LIMIT ?
            """, (limit,))

            clusters = []
            for cluster_row in cursor.fetchall():
                cluster_dict = dict(cluster_row)

                # Get cluster articles
                article_cursor = conn.execute("""
                    SELECT a.id, a.title, a.source, a.category, a.url
                    FROM cluster_articles ca
                    JOIN articles a ON ca.article_id = a.id
                    WHERE ca.cluster_id = ?
                """, (cluster_dict['cluster_id'],))

                cluster_dict['similar_articles'] = [dict(row) for row in article_cursor.fetchall()]
                cluster_dict['sources_covered'] = cluster_dict['sources_covered'].split(',') if cluster_dict['sources_covered'] else []

                clusters.append(cluster_dict)

            return clusters
