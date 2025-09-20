import React, { useState } from 'react';
import type { NewsCategory } from '../types/news';
import { mockDashboardData, categoryFilters } from '../data/mockData';
import CategoryFilter from './CategoryFilter';
import TopArticles from './TopArticles';
import ArticleCard from './ArticleCard';

const Dashboard: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<NewsCategory | 'all'>('all');

  const getFilteredArticles = () => {
    if (selectedCategory === 'all') {
      return mockDashboardData.topArticles;
    }
    return mockDashboardData.categories[selectedCategory];
  };

  const filteredArticles = getFilteredArticles();

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Australian News Dashboard</h1>
        <p>Stay updated with the latest highlights from top Australian news sources</p>
      </header>

      <div className="dashboard-content">
        <CategoryFilter
          categories={categoryFilters}
          selectedCategory={selectedCategory}
          onCategoryChange={setSelectedCategory}
        />

        {selectedCategory === 'all' ? (
          <TopArticles articles={filteredArticles} />
        ) : (
          <div className="category-articles">
            <h2>
              {categoryFilters.find(c => c.category === selectedCategory)?.label} Articles
            </h2>
            <div className="articles-grid">
              {filteredArticles.map((article) => (
                <ArticleCard key={article.id} article={article} showCategory={false} />
              ))}
            </div>
          </div>
        )}

        <footer className="dashboard-footer">
          <h3>News Sources</h3>
          <div className="sources-list">
            {mockDashboardData.sources.map((source) => (
              <span key={source.id} className="source-tag">
                {source.name}
              </span>
            ))}
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Dashboard;