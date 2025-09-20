import React, { useState } from 'react';
import type { NewsCategory } from '../types/news';
import { categoryFilters } from '../data/mockData';
import { useDashboardData, useAPIHealth, useNewsExtraction } from '../hooks/useNewsAPI';
import CategoryFilter from './CategoryFilter';
import TopArticles from './TopArticles';
import ArticleCard from './ArticleCard';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import RefreshButton from './RefreshButton';

const Dashboard: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<NewsCategory | 'all'>('all');
  const { data: dashboardData, loading, error, refetch } = useDashboardData();
  const { isHealthy } = useAPIHealth();
  const { extractNews, loading: extracting } = useNewsExtraction();

  const getFilteredArticles = () => {
    if (!dashboardData) return [];

    if (selectedCategory === 'all') {
      return dashboardData.topArticles;
    }
    return dashboardData.categories[selectedCategory] || [];
  };

  const filteredArticles = getFilteredArticles();

  const handleRefresh = async () => {
    await refetch();
  };

  const handleExtractLatest = async () => {
    const result = await extractNews();
    if (result) {
      // Refresh dashboard data after extraction
      await refetch();
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading Australian news..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Failed to load news"
        message={error}
        onRetry={handleRefresh}
      />
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Australian News Dashboard</h1>
          <p>Stay updated with the latest highlights from top Australian news sources</p>
          {!isHealthy && (
            <div className="api-status-warning">
              ⚠️ API connection issue - using cached data
            </div>
          )}
        </div>
        <div className="header-actions">
          <RefreshButton
            onClick={handleRefresh}
            loading={loading}
            lastUpdated={dashboardData ? new Date().toLocaleTimeString() : undefined}
          />
          <button
            className="extract-button"
            onClick={handleExtractLatest}
            disabled={extracting}
          >
            {extracting ? 'Extracting...' : 'Get Latest News'}
          </button>
        </div>
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
            {dashboardData?.sources?.map((source) => (
              <span key={source.id} className="source-tag">
                {source.name}
              </span>
            )) || (
              <span className="no-sources">No sources available</span>
            )}
          </div>
          <div className="dashboard-stats">
            <span>Total Articles: {dashboardData?.topArticles?.length || 0}</span>
            <span>API Status: {isHealthy ? '🟢 Connected' : '🔴 Disconnected'}</span>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Dashboard;