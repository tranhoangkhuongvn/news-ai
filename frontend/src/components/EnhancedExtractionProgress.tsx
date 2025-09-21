import React from 'react';

interface EnhancedExtractionProgressProps {
  phase: 'extraction' | 'similarity' | 'prioritization' | 'complete';
  message: string;
  metrics?: {
    total_articles_extracted?: number;
    similar_pairs_found?: number;
    stories_prioritized?: number;
    processing_time?: number;
  };
}

const EnhancedExtractionProgress: React.FC<EnhancedExtractionProgressProps> = ({
  phase,
  message,
  metrics,
}) => {
  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case 'extraction':
        return '📰';
      case 'similarity':
        return '🔗';
      case 'prioritization':
        return '⭐';
      case 'complete':
        return '✅';
      default:
        return '🔄';
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'extraction':
        return '#3b82f6';
      case 'similarity':
        return '#8b5cf6';
      case 'prioritization':
        return '#f59e0b';
      case 'complete':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getPhaseProgress = (phase: string) => {
    switch (phase) {
      case 'extraction':
        return 35;
      case 'similarity':
        return 65;
      case 'prioritization':
        return 85;
      case 'complete':
        return 100;
      default:
        return 0;
    }
  };

  return (
    <div
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        padding: '24px',
        backgroundColor: '#ffffff',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        margin: '16px 0',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <div
          style={{
            fontSize: '24px',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%',
            backgroundColor: `${getPhaseColor(phase)}15`,
          }}
        >
          {getPhaseIcon(phase)}
        </div>
        <div>
          <h3
            style={{
              margin: '0 0 4px 0',
              fontSize: '18px',
              fontWeight: '600',
              color: '#111827',
            }}
          >
            Enhanced News Extraction
          </h3>
          <p
            style={{
              margin: '0',
              fontSize: '14px',
              color: '#6b7280',
            }}
          >
            {message}
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{ marginBottom: '20px' }}>
        <div
          style={{
            width: '100%',
            height: '8px',
            backgroundColor: '#f3f4f6',
            borderRadius: '4px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${getPhaseProgress(phase)}%`,
              height: '100%',
              backgroundColor: getPhaseColor(phase),
              transition: 'width 0.5s ease-in-out',
            }}
          />
        </div>
        <div
          style={{
            marginTop: '8px',
            fontSize: '12px',
            color: '#6b7280',
            textAlign: 'center',
          }}
        >
          {getPhaseProgress(phase)}% Complete
        </div>
      </div>

      {/* Phase Steps */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
        {[
          { key: 'extraction', label: 'Extract', icon: '📰' },
          { key: 'similarity', label: 'Cluster', icon: '🔗' },
          { key: 'prioritization', label: 'Prioritize', icon: '⭐' },
          { key: 'complete', label: 'Complete', icon: '✅' },
        ].map((step) => {
          const isActive = step.key === phase;
          const isCompleted = getPhaseProgress(step.key) <= getPhaseProgress(phase);

          return (
            <div
              key={step.key}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                flex: 1,
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '14px',
                  backgroundColor: isCompleted
                    ? getPhaseColor(step.key)
                    : '#f3f4f6',
                  color: isCompleted ? '#ffffff' : '#6b7280',
                  marginBottom: '8px',
                  transition: 'all 0.3s ease-in-out',
                }}
              >
                {step.icon}
              </div>
              <span
                style={{
                  fontSize: '11px',
                  color: isActive ? getPhaseColor(step.key) : '#6b7280',
                  fontWeight: isActive ? '600' : '400',
                  transition: 'all 0.3s ease-in-out',
                }}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Metrics */}
      {metrics && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '16px',
            padding: '16px',
            backgroundColor: '#f9fafb',
            borderRadius: '8px',
          }}
        >
          {metrics.total_articles_extracted !== undefined && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '20px', fontWeight: '600', color: '#111827' }}>
                {metrics.total_articles_extracted}
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>Articles</div>
            </div>
          )}
          {metrics.similar_pairs_found !== undefined && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '20px', fontWeight: '600', color: '#111827' }}>
                {metrics.similar_pairs_found}
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>Similar Pairs</div>
            </div>
          )}
          {metrics.stories_prioritized !== undefined && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '20px', fontWeight: '600', color: '#111827' }}>
                {metrics.stories_prioritized}
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>Stories</div>
            </div>
          )}
          {metrics.processing_time !== undefined && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '20px', fontWeight: '600', color: '#111827' }}>
                {metrics.processing_time.toFixed(1)}s
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>Time</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EnhancedExtractionProgress;