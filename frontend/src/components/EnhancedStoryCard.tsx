import React from 'react';
import type { PrioritizedStory } from '../types/news';
import PriorityBadge from './PriorityBadge';

interface EnhancedStoryCardProps {
  story: PrioritizedStory;
  onClick?: () => void;
}

const EnhancedStoryCard: React.FC<EnhancedStoryCardProps> = ({ story, onClick }) => {
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'sports':
        return '#ef4444';
      case 'finance':
        return '#f59e0b';
      case 'lifestyle':
        return '#10b981';
      case 'music':
        return '#8b5cf6';
      default:
        return '#6b7280';
    }
  };

  const formatScore = (score: number) => (score * 100).toFixed(0);

  return (
    <div
      className={`enhanced-story-card ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '16px',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        transition: 'all 0.2s ease-in-out',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        e.currentTarget.style.transform = 'translateY(-1px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* Priority Badge and Category */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <PriorityBadge priority={story.priority_level} score={story.priority_score} />
        <span
          style={{
            padding: '4px 8px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '500',
            color: 'white',
            backgroundColor: getCategoryColor(story.category),
            textTransform: 'capitalize',
          }}
        >
          {story.category}
        </span>
      </div>

      {/* Story Title */}
      <h3
        style={{
          fontSize: '18px',
          fontWeight: '600',
          lineHeight: '1.4',
          margin: '0 0 12px 0',
          color: '#111827',
        }}
      >
        {story.title}
      </h3>

      {/* Summary */}
      <p
        style={{
          fontSize: '14px',
          lineHeight: '1.5',
          color: '#6b7280',
          margin: '0 0 16px 0',
          display: '-webkit-box',
          WebkitLineClamp: 3,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}
      >
        {story.summary}
      </p>

      {/* Story Metadata */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginBottom: '16px', fontSize: '12px', color: '#6b7280' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>📰</span>
          <span>{story.coverage_description}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>⏰</span>
          <span>{story.time_description}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>📍</span>
          <span style={{ textTransform: 'capitalize' }}>{story.geographic_scope}</span>
        </div>
      </div>

      {/* Urgency Keywords */}
      {story.urgency_keywords.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {story.urgency_keywords.slice(0, 3).map((keyword, index) => (
              <span
                key={index}
                style={{
                  padding: '2px 6px',
                  backgroundColor: story.is_breaking ? '#fef2f2' : '#f3f4f6',
                  color: story.is_breaking ? '#dc2626' : '#374151',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: '500',
                }}
              >
                {keyword}
              </span>
            ))}
            {story.urgency_keywords.length > 3 && (
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                +{story.urgency_keywords.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Priority Score Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <div style={{ textAlign: 'center', padding: '8px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
          <div style={{ fontSize: '16px', fontWeight: '600', color: '#ef4444' }}>
            {formatScore(story.breaking_news_score)}%
          </div>
          <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>Breaking</div>
        </div>
        <div style={{ textAlign: 'center', padding: '8px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
          <div style={{ fontSize: '16px', fontWeight: '600', color: '#f59e0b' }}>
            {formatScore(story.coverage_score)}%
          </div>
          <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>Coverage</div>
        </div>
        <div style={{ textAlign: 'center', padding: '8px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
          <div style={{ fontSize: '16px', fontWeight: '600', color: '#10b981' }}>
            {formatScore(story.quality_score)}%
          </div>
          <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>Quality</div>
        </div>
      </div>

      {/* Sources */}
      <div>
        <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>
          Sources ({story.article_count} articles):
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {story.sources.map((source, index) => (
            <span
              key={index}
              style={{
                padding: '4px 8px',
                backgroundColor: '#e5e7eb',
                color: '#374151',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: '500',
              }}
            >
              {source}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default EnhancedStoryCard;