# backend/app/models/news.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    url = Column(String, unique=True, nullable=False)
    source = Column(String, nullable=False)
    category = Column(String)
    published_date = Column(DateTime)
    scraped_date = Column(DateTime, default=datetime.utcnow)
    embedding_stored = Column(Boolean, default=False)
    sentiment_score = Column(Float)
    is_processed = Column(Boolean, default=False)

class DailyDigest(Base):
    __tablename__ = "daily_digests"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    top_stories = Column(Text)  # JSON string
    categories_summary = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)