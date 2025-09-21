import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ArticleReferences from './ArticleReferences';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: any[];
  context_articles?: any[];
}

interface ChatBotProps {
  onClose?: () => void;
  categoryFilter?: string;
}

const ChatBot: React.FC<ChatBotProps> = ({ onClose, categoryFilter }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showSources, setShowSources] = useState(false);
  const [currentSources, setCurrentSources] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Add welcome message
    const welcomeMessage: Message = {
      role: 'assistant',
      content: `Hello! I'm your Australian News AI assistant. I can help you find and discuss recent news from ABC News, The Guardian Australia, Sydney Morning Herald, and News.com.au.

What would you like to know about Australian news today?`,
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
  }, []);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/chat/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          session_id: sessionId,
          category_filter: categoryFilter
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        sources: data.sources,
        context_articles: data.context_articles
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update session ID if new session was created
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      // Update sources for reference panel
      if (data.sources && data.sources.length > 0) {
        setCurrentSources(data.sources);
      }

    } catch (error) {
      console.error('Error sending message:', error);

      const errorMessage: Message = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error while processing your message. Please try again or check your connection.',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    const welcomeMessage: Message = {
      role: 'assistant',
      content: `Hello! I'm your Australian News AI assistant. I can help you find and discuss recent news from ABC News, The Guardian Australia, Sydney Morning Herald, and News.com.au.

What would you like to know about Australian news today?`,
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
    setSessionId(null);
    setCurrentSources([]);
    setShowSources(false);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        backgroundColor: '#ffffff',
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          backgroundColor: '#f8fafc',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#3b82f6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '16px'
            }}
          >
            🤖
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1f2937' }}>
              Australian News AI
            </h3>
            <p style={{ margin: 0, fontSize: '12px', color: '#6b7280' }}>
              {categoryFilter ? `Focused on ${categoryFilter}` : 'All Australian news sources'}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {currentSources.length > 0 && (
            <button
              onClick={() => setShowSources(!showSources)}
              style={{
                padding: '6px 12px',
                backgroundColor: showSources ? '#3b82f6' : '#f3f4f6',
                color: showSources ? '#ffffff' : '#6b7280',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              📰 Sources ({currentSources.length})
            </button>
          )}

          <button
            onClick={clearChat}
            style={{
              padding: '6px 12px',
              backgroundColor: '#f3f4f6',
              color: '#6b7280',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            🗑️ Clear
          </button>

          {onClose && (
            <button
              onClick={onClose}
              style={{
                padding: '6px 12px',
                backgroundColor: '#f3f4f6',
                color: '#6b7280',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Messages Area */}
        <div
          style={{
            flex: showSources ? '1' : '1',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px'
            }}
          >
            {messages.map((message, index) => (
              <ChatMessage
                key={index}
                message={message}
                onSourcesClick={message.sources?.length ? () => {
                  setCurrentSources(message.sources || []);
                  setShowSources(true);
                } : undefined}
              />
            ))}

            {isLoading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6b7280' }}>
                <div
                  style={{
                    width: '16px',
                    height: '16px',
                    border: '2px solid #e5e7eb',
                    borderTop: '2px solid #3b82f6',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}
                />
                <span style={{ fontSize: '14px' }}>AI is thinking...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <ChatInput
            onSendMessage={sendMessage}
            disabled={isLoading}
            placeholder="Ask me about Australian news..."
          />
        </div>

        {/* Sources Panel */}
        {showSources && currentSources.length > 0 && (
          <div
            style={{
              width: '320px',
              minWidth: '320px',
              borderLeft: '1px solid #e5e7eb',
              backgroundColor: '#f9fafb'
            }}
          >
            <ArticleReferences
              sources={currentSources}
              onClose={() => setShowSources(false)}
            />
          </div>
        )}
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

export default ChatBot;