import React from 'react';
import type { NewsArticle } from '../types/news';

interface ArticleCardProps {
  article: NewsArticle;
  showCategory?: boolean;
}

const ArticleCard: React.FC<ArticleCardProps> = ({ article, showCategory = true }) => {
  const getCategoryColor = (category: string) => {
    const colors = {
      music: '#8B5CF6',
      lifestyle: '#10B981',
      finance: '#F59E0B',
      sports: '#EF4444'
    };
    return colors[category as keyof typeof colors] || '#6B7280';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-AU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleArticleClick = () => {
    if (article.url) {
      window.open(article.url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleArticleClick();
    }
  };

  return (
    <div
      className="article-card clickable-card"
      onClick={handleArticleClick}
      onKeyPress={handleKeyPress}
      tabIndex={0}
      role="button"
      aria-label={`Read full article: ${article.title}`}
      title="Click to read full article"
    >
      <div className="article-card-header">
        {showCategory && (
          <span
            className="category-badge"
            style={{ backgroundColor: getCategoryColor(article.category) }}
          >
            {article.category.charAt(0).toUpperCase() + article.category.slice(1)}
          </span>
        )}
        <span className="source">{article.source}</span>
        <span className="external-link-icon">🔗</span>
      </div>

      <h3 className="article-title clickable-title">{article.title}</h3>

      <p className="article-summary clickable-content">{article.summary}</p>

      <div className="highlights">
        <h4>Key Highlights:</h4>
        <ul>
          {article.highlights.map((highlight, index) => (
            <li key={index}>{highlight}</li>
          ))}
        </ul>
      </div>

      <div className="article-footer">
        <span className="author">{article.author}</span>
        <span className="publish-date">{formatDate(article.publishedAt)}</span>
        <span className="read-more">Click to read more →</span>
      </div>
    </div>
  );
};

export default ArticleCard;