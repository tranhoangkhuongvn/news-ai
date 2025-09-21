import React, { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  placeholder = "Type your message..."
}) => {
  const [message, setMessage] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled && !isComposing) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const suggestedQuestions = [
    "What's happening in Australian sports today?",
    "Tell me about recent business news",
    "Any breaking news from Australia?",
    "What are the top lifestyle stories?",
    "Show me recent music news"
  ];

  const handleSuggestionClick = (suggestion: string) => {
    if (!disabled) {
      onSendMessage(suggestion);
    }
  };

  return (
    <div
      style={{
        padding: '16px',
        borderTop: '1px solid #e5e7eb',
        backgroundColor: '#ffffff'
      }}
    >
      {/* Suggested Questions (show when input is empty) */}
      {!message && (
        <div style={{ marginBottom: '12px' }}>
          <div
            style={{
              fontSize: '12px',
              color: '#6b7280',
              marginBottom: '8px',
              fontWeight: '500'
            }}
          >
            💡 Try asking:
          </div>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '6px'
            }}
          >
            {suggestedQuestions.slice(0, 3).map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={disabled}
                style={{
                  padding: '4px 8px',
                  backgroundColor: disabled ? '#f9fafb' : '#f3f4f6',
                  color: disabled ? '#9ca3af' : '#4b5563',
                  border: '1px solid #e5e7eb',
                  borderRadius: '12px',
                  fontSize: '11px',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (!disabled) {
                    e.currentTarget.style.backgroundColor = '#e5e7eb';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!disabled) {
                    e.currentTarget.style.backgroundColor = '#f3f4f6';
                  }
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            style={{
              width: '100%',
              minHeight: '40px',
              maxHeight: '120px',
              padding: '10px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '14px',
              lineHeight: '1.5',
              resize: 'none',
              outline: 'none',
              backgroundColor: disabled ? '#f9fafb' : '#ffffff',
              color: disabled ? '#9ca3af' : '#1f2937',
              transition: 'border-color 0.2s'
            }}
            onFocus={(e) => {
              if (!disabled) {
                e.currentTarget.style.borderColor = '#3b82f6';
              }
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = '#d1d5db';
            }}
          />

          {/* Character count */}
          {message.length > 0 && (
            <div
              style={{
                position: 'absolute',
                bottom: '2px',
                right: '8px',
                fontSize: '10px',
                color: message.length > 500 ? '#ef4444' : '#9ca3af'
              }}
            >
              {message.length}/1000
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={disabled || !message.trim() || message.length > 1000}
          style={{
            padding: '10px 16px',
            backgroundColor: disabled || !message.trim() ? '#e5e7eb' : '#3b82f6',
            color: disabled || !message.trim() ? '#9ca3af' : '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: disabled || !message.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            minWidth: '80px',
            justifyContent: 'center'
          }}
          onMouseEnter={(e) => {
            if (!disabled && message.trim()) {
              e.currentTarget.style.backgroundColor = '#2563eb';
            }
          }}
          onMouseLeave={(e) => {
            if (!disabled && message.trim()) {
              e.currentTarget.style.backgroundColor = '#3b82f6';
            }
          }}
        >
          {disabled ? (
            <>
              <div
                style={{
                  width: '12px',
                  height: '12px',
                  border: '2px solid #9ca3af',
                  borderTop: '2px solid transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}
              />
            </>
          ) : (
            <>
              <span>Send</span>
              <span style={{ fontSize: '12px' }}>⏎</span>
            </>
          )}
        </button>
      </form>

      {/* Helper Text */}
      <div
        style={{
          fontSize: '11px',
          color: '#9ca3af',
          marginTop: '8px',
          textAlign: 'center'
        }}
      >
        Press Enter to send • Shift+Enter for new line
      </div>

      {/* CSS Animation */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default ChatInput;