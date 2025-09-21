import React from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: any[];
  context_articles?: any[];
}

interface ChatMessageProps {
  message: Message;
  onSourcesClick?: () => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, onSourcesClick }) => {
  const isUser = message.role === 'user';

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderContent = (content: string) => {
    // Split content by newlines and render as paragraphs
    const paragraphs = content.split('\n').filter(p => p.trim());

    return paragraphs.map((paragraph, index) => {
      // Check if this is a numbered list item
      if (paragraph.match(/^\d+\./)) {
        return (
          <div key={index} style={{ margin: '12px 0', paddingLeft: '8px' }}>
            <strong style={{ color: '#1f2937', fontSize: '15px', lineHeight: '1.6' }}>{paragraph}</strong>
          </div>
        );
      }

      // Regular paragraph
      return (
        <p key={index} style={{ margin: '10px 0', lineHeight: '1.6', fontSize: '15px' }}>
          {paragraph}
        </p>
      );
    });
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: '14px',
        maxWidth: '100%'
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          backgroundColor: isUser ? '#3b82f6' : '#10b981',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          flexShrink: 0
        }}
      >
        {isUser ? '👤' : '🤖'}
      </div>

      {/* Message Content */}
      <div
        style={{
          maxWidth: '85%',
          minWidth: '250px'
        }}
      >
        {/* Message Bubble */}
        <div
          style={{
            padding: '16px 20px',
            borderRadius: '16px',
            backgroundColor: isUser ? '#3b82f6' : '#f3f4f6',
            color: isUser ? '#ffffff' : '#1f2937',
            fontSize: '15px',
            lineHeight: '1.6',
            wordWrap: 'break-word',
            minHeight: '44px'
          }}
        >
          {isUser ? (
            <p style={{ margin: 0 }}>{message.content}</p>
          ) : (
            <div style={{ margin: 0 }}>
              {renderContent(message.content)}
            </div>
          )}
        </div>

        {/* Message Footer */}
        <div
          style={{
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            alignItems: 'center',
            gap: '8px',
            marginTop: '4px'
          }}
        >
          <span style={{ fontSize: '11px', color: '#9ca3af' }}>
            {formatTimestamp(message.timestamp)}
          </span>

          {/* Sources Button */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <button
              onClick={onSourcesClick}
              style={{
                padding: '2px 8px',
                backgroundColor: '#e5e7eb',
                color: '#6b7280',
                border: 'none',
                borderRadius: '12px',
                fontSize: '10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#d1d5db';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#e5e7eb';
              }}
            >
              📰 {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
            </button>
          )}

          {/* Context Articles Indicator */}
          {!isUser && message.context_articles && message.context_articles.length > 0 && (
            <span
              style={{
                padding: '2px 8px',
                backgroundColor: '#fef3c7',
                color: '#92400e',
                borderRadius: '12px',
                fontSize: '10px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              🔍 {message.context_articles.length} context
            </span>
          )}
        </div>

        {/* Quick Preview of Sources (if no click handler) */}
        {!isUser && message.sources && message.sources.length > 0 && !onSourcesClick && (
          <div
            style={{
              marginTop: '8px',
              padding: '8px 12px',
              backgroundColor: '#f9fafb',
              borderRadius: '8px',
              fontSize: '12px'
            }}
          >
            <div style={{ fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
              Sources:
            </div>
            {message.sources.slice(0, 2).map((source, index) => (
              <div key={index} style={{ margin: '2px 0', color: '#6b7280' }}>
                • {source.title} ({source.source})
              </div>
            ))}
            {message.sources.length > 2 && (
              <div style={{ color: '#9ca3af', fontStyle: 'italic' }}>
                +{message.sources.length - 2} more...
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;