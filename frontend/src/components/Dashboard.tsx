import React, { useState } from 'react';
import type { NewsCategory } from '../types/news';
import { categoryFilters } from '../data/mockData';
import { useDashboardData, useAPIHealth, useNewsExtraction, useEnhancedNewsExtraction } from '../hooks/useNewsAPI';
import CategoryFilter from './CategoryFilter';
import TopArticles from './TopArticles';
import ArticleCard from './ArticleCard';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import RefreshButton from './RefreshButton';
import EnhancedStoryCard from './EnhancedStoryCard';
import EnhancedExtractionProgress from './EnhancedExtractionProgress';

const Dashboard: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<NewsCategory | 'all'>('all');
  const [showEnhancedStories, setShowEnhancedStories] = useState(false);
  const { data: dashboardData, loading, error, refetch } = useDashboardData();
  const { isHealthy } = useAPIHealth();
  const { extractNews, loading: extracting } = useNewsExtraction();
  const {
    extractEnhancedNews,
    loading: enhancedLoading,
    error: enhancedError,
    data: enhancedData,
    progress,
    clearResults,
  } = useEnhancedNewsExtraction();

  const getFilteredArticles = () => {
    if (!dashboardData) return [];

    if (selectedCategory === 'all') {
      return dashboardData.topArticles;
    }
    return dashboardData.categories[selectedCategory] || [];
  };

  const filteredArticles = getFilteredArticles();

  const getDisplayedArticlesCount = () => {
    if (showEnhancedStories && enhancedData?.top_stories) {
      return enhancedData.top_stories.length;
    }
    return filteredArticles.length;
  };

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

  const handleEnhancedExtract = async () => {
    setShowEnhancedStories(true);
    const result = await extractEnhancedNews({
      sources: ['abc', 'guardian', 'smh', 'news_com_au'],
      categories: ['sports', 'finance', 'lifestyle', 'music'],
      articles_per_category: 20,
    });

    if (result) {
      // Refresh dashboard data after extraction
      await refetch();
    }
  };

  const handleClearEnhancedResults = () => {
    clearResults();
    setShowEnhancedStories(false);
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
            style={{
              padding: '8px 16px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              cursor: extracting ? 'not-allowed' : 'pointer',
              opacity: extracting ? 0.6 : 1,
              marginRight: '8px',
            }}
          >
            {extracting ? 'Extracting...' : 'Get Latest News'}
          </button>
          <button
            onClick={handleEnhancedExtract}
            disabled={enhancedLoading}
            style={{
              padding: '10px 20px',
              background: enhancedLoading
                ? '#9ca3af'
                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: enhancedLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease-in-out',
              boxShadow: enhancedLoading ? 'none' : '0 2px 4px rgba(0, 0, 0, 0.1)',
            }}
            onMouseEnter={(e) => {
              if (!enhancedLoading) {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.15)';
              }
            }}
            onMouseLeave={(e) => {
              if (!enhancedLoading) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
              }
            }}
          >
            {enhancedLoading ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>🔄</span>
                Processing...
              </span>
            ) : (
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>⚡</span>
                Smart News Discovery
              </span>
            )}
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Enhanced Progress Display */}
        {progress && (
          <EnhancedExtractionProgress
            phase={progress.phase}
            message={progress.message}
            metrics={enhancedData?.metrics}
          />
        )}

        {/* Enhanced Error Display */}
        {enhancedError && (
          <ErrorMessage
            title="Enhanced Extraction Failed"
            message={enhancedError}
            onRetry={handleEnhancedExtract}
          />
        )}

        {/* Enhanced Stories Display */}
        {showEnhancedStories && enhancedData?.top_stories && (
          <div style={{ marginBottom: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <h2 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: '700', color: '#111827' }}>
                  🏆 Top Prioritized Stories
                </h2>
                <p style={{ margin: '0', fontSize: '14px', color: '#6b7280' }}>
                  Intelligently ranked using breaking news indicators, cross-source coverage, and content quality
                </p>
              </div>
              <button
                onClick={handleClearEnhancedResults}
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#f3f4f6',
                  color: '#6b7280',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                ✕ Clear Results
              </button>
            </div>

            {/* Extraction Summary */}
            <div
              style={{
                padding: '16px',
                backgroundColor: '#f9fafb',
                borderRadius: '8px',
                marginBottom: '20px',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: '16px',
                fontSize: '12px',
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
                  {enhancedData.metrics.total_articles_extracted}
                </div>
                <div style={{ color: '#6b7280' }}>Articles Extracted</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
                  {enhancedData.extraction_summary.extraction_rate}%
                </div>
                <div style={{ color: '#6b7280' }}>Extraction Rate</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
                  {enhancedData.metrics.similar_pairs_found}
                </div>
                <div style={{ color: '#6b7280' }}>Similar Pairs</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
                  {enhancedData.metrics.stories_prioritized}
                </div>
                <div style={{ color: '#6b7280' }}>Stories Analyzed</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
                  {enhancedData.processing_time.toFixed(1)}s
                </div>
                <div style={{ color: '#6b7280' }}>Processing Time</div>
              </div>
            </div>

            {/* Enhanced Stories */}
            <div>
              {enhancedData.top_stories.map((story) => (
                <EnhancedStoryCard
                  key={story.story_id}
                  story={story}
                  onClick={() => {
                    // Navigate to representative article
                    if (story.representative_article?.url) {
                      window.open(story.representative_article.url, '_blank');
                    }
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Regular Dashboard Content */}
        {!showEnhancedStories && (
          <>
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
          </>
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
            <span>Total Articles: {getDisplayedArticlesCount()}</span>
            <span>API Status: {isHealthy ? '🟢 Connected' : '🔴 Disconnected'}</span>
          </div>
          <div className="developer-acknowledgment">
            <span>Developed by Khuong Tran © 2025</span>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Dashboard;