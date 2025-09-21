"""
Text processing utilities for similarity detection.
"""

import re
import string
from typing import Set, List
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# Common words to remove from titles for better similarity matching
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'between', 'among', 'under', 'over', 'through', 'until',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'can', 'must', 'shall', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
    'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
    'his', 'her', 'its', 'our', 'their', 'says', 'said', 'new', 'news'
}

# Australian news-specific stop words
AUS_NEWS_WORDS = {
    'australia', 'australian', 'aus', 'sydney', 'melbourne', 'brisbane',
    'perth', 'adelaide', 'darwin', 'canberra', 'nsw', 'vic', 'qld', 'wa',
    'sa', 'nt', 'act', 'tas', 'breaking', 'live', 'update', 'latest'
}

ALL_STOP_WORDS = STOP_WORDS | AUS_NEWS_WORDS

def clean_title(title: str) -> str:
    """
    Clean and normalize a news title for similarity comparison.

    Args:
        title: Raw news article title

    Returns:
        Cleaned and normalized title
    """
    if not title:
        return ""

    # Convert to lowercase
    title = title.lower()

    # Remove punctuation except apostrophes
    title = re.sub(r"[^\w\s']", ' ', title)

    # Remove extra whitespace
    title = ' '.join(title.split())

    # Remove stop words
    words = title.split()
    meaningful_words = [word for word in words if word not in ALL_STOP_WORDS and len(word) > 2]

    return ' '.join(meaningful_words)

def extract_keywords(text: str, min_length: int = 3, max_words: int = 20) -> Set[str]:
    """
    Extract meaningful keywords from text.

    Args:
        text: Input text to extract keywords from
        min_length: Minimum length of keywords
        max_words: Maximum number of keywords to return

    Returns:
        Set of extracted keywords
    """
    if not text:
        return set()

    # Clean and normalize text
    text = text.lower()
    text = re.sub(r"[^\w\s']", ' ', text)
    text = ' '.join(text.split())

    # Extract words
    words = text.split()

    # Filter meaningful words
    keywords = {
        word for word in words
        if (len(word) >= min_length and
            word not in ALL_STOP_WORDS and
            not word.isdigit())
    }

    # Return top keywords by frequency if we have too many
    if len(keywords) > max_words:
        word_freq = {}
        for word in words:
            if word in keywords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and take top words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = {word for word, _ in sorted_words[:max_words]}

    return keywords

def normalize_date(date_str: str) -> datetime:
    """
    Parse and normalize a date string to datetime object.

    Args:
        date_str: Date string in various formats

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date cannot be parsed
    """
    if not date_str:
        raise ValueError("Empty date string")

    try:
        # Try parsing with dateutil (handles many formats)
        return date_parser.parse(date_str)
    except (ValueError, TypeError) as e:
        # Fallback for common Australian date formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%d-%m-%Y %H:%M:%S',
            '%d-%m-%Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Could not parse date: {date_str}")

def calculate_time_similarity(date1_str: str, date2_str: str) -> float:
    """
    Calculate time-based similarity between two articles.

    Args:
        date1_str: First article's published date
        date2_str: Second article's published date

    Returns:
        Similarity score (0.0 to 1.0)
    """
    try:
        date1 = normalize_date(date1_str)
        date2 = normalize_date(date2_str)

        # Calculate time difference in hours
        time_diff = abs((date1 - date2).total_seconds()) / 3600

        # Similarity scoring based on time windows
        if time_diff <= 6:      # Same day, close time
            return 1.0
        elif time_diff <= 24:   # Same day
            return 0.8
        elif time_diff <= 48:   # Within 2 days
            return 0.5
        elif time_diff <= 168:  # Within a week
            return 0.2
        else:                   # More than a week
            return 0.0

    except (ValueError, TypeError):
        # If we can't parse dates, assume they're not similar
        return 0.0

def get_title_signature(title: str) -> str:
    """
    Generate a signature for a title to help with quick comparisons.

    Args:
        title: Article title

    Returns:
        Title signature (first few significant words)
    """
    cleaned = clean_title(title)
    words = cleaned.split()

    # Take first 3-5 most significant words
    significant_words = [word for word in words if len(word) > 3][:5]

    return ' '.join(significant_words[:3])  # Use first 3 words as signature