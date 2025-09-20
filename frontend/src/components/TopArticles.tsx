import React from 'react';
import type { NewsArticle } from '../types/news';
import ArticleCard from './ArticleCard';

interface TopArticlesProps {
  articles: NewsArticle[];
}

const TopArticles: React.FC<TopArticlesProps> = ({ articles }) => {
  return (
    <div className="top-articles">
      <h2>Top 10 Articles Across Australian News Sources</h2>
      <div className="articles-grid">
        {articles.map((article, index) => (
          <div key={article.id} className="article-item">
            <div className="article-rank">#{index + 1}</div>
            <ArticleCard article={article} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopArticles;