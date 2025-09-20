from dataclasses import dataclass
from typing import List

@dataclass
class NewsArticle:
    """Data class for storing news article information"""
    title: str
    url: str
    category: str
    summary: str
    published_date: str
    author: str
    content: str
    source: str
    tags: List[str]
    extracted_at: str