import React from 'react';

interface Source {
  title: string;
  url: string;
  source: string;
  published_date?: string;
  summary?: string;
}

interface ArticleReferencesProps {
  sources: Source[];
  onClose: () => void;
}

const ArticleReferences: React.FC<ArticleReferencesProps> = ({ sources, onClose }) => {
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '';
    }
  };

  const getSourceColor = (source: string) => {
    const colors: { [key: string]: string } = {
      'ABC News': '#FF6B35',
      'The Guardian': '#052962',
      'Sydney Morning Herald': '#004A9F',
      'News.com.au': '#E60000'
    };
    return colors[source] || '#6b7280';
  };

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#f9fafb'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: '#ffffff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div>
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#1f2937' }}>
            📰 News Sources
          </h4>
          <p style={{ margin: 0, fontSize: '12px', color: '#6b7280' }}>
            {sources.length} article{sources.length !== 1 ? 's' : ''} referenced
          </p>
        </div>
        <button
          onClick={onClose}
          style={{
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            backgroundColor: '#f3f4f6',
            color: '#6b7280',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#e5e7eb';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#f3f4f6';
          }}
        >
          ✕
        </button>
      </div>

      {/* Sources List */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px'
        }}
      >
        {sources.length === 0 ? (
          <div
            style={{
              padding: '32px 16px',
              textAlign: 'center',
              color: '#9ca3af',
              fontSize: '14px'
            }}
          >
            No sources available
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {sources.map((source, index) => (
              <div
                key={index}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '8px',
                  padding: '12px',
                  border: '1px solid #e5e7eb',
                  transition: 'all 0.2s',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
                  e.currentTarget.style.borderColor = '#d1d5db';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.borderColor = '#e5e7eb';
                }}
                onClick={() => window.open(source.url, '_blank', 'noopener,noreferrer')}
              >
                {/* Source Header */}
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '8px'
                  }}
                >
                  <div
                    style={{
                      display: 'inline-block',
                      padding: '2px 6px',
                      backgroundColor: getSourceColor(source.source),
                      color: '#ffffff',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: '500',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}
                  >
                    {source.source.replace('News.com.au', 'News.com')}
                  </div>
                  {source.published_date && (
                    <span
                      style={{
                        fontSize: '10px',
                        color: '#9ca3af'
                      }}
                    >
                      {formatDate(source.published_date)}
                    </span>
                  )}
                </div>

                {/* Article Title */}
                <h5
                  style={{
                    margin: '0 0 8px 0',
                    fontSize: '13px',
                    fontWeight: '600',
                    color: '#1f2937',
                    lineHeight: '1.4',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}
                >
                  {source.title}
                </h5>

                {/* Summary */}
                {source.summary && (
                  <p
                    style={{
                      margin: 0,
                      fontSize: '11px',
                      color: '#6b7280',
                      lineHeight: '1.4',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden'
                    }}
                  >
                    {source.summary}
                  </p>
                )}

                {/* External Link Indicator */}
                <div
                  style={{
                    marginTop: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '10px',
                    color: '#9ca3af'
                  }}
                >
                  <span>🔗</span>
                  <span>Click to read full article</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div
        style={{
          padding: '12px 16px',
          borderTop: '1px solid #e5e7eb',
          backgroundColor: '#ffffff',
          fontSize: '10px',
          color: '#9ca3af',
          textAlign: 'center'
        }}
      >
        Sources are used to provide context for AI responses
      </div>
    </div>
  );
};

export default ArticleReferences;