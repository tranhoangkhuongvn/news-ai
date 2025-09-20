import React from 'react';

interface RefreshButtonProps {
  onClick: () => void;
  loading?: boolean;
  lastUpdated?: string;
  disabled?: boolean;
}

const RefreshButton: React.FC<RefreshButtonProps> = ({
  onClick,
  loading = false,
  lastUpdated,
  disabled = false
}) => {
  return (
    <div className="refresh-button-container">
      <button
        className="refresh-button"
        onClick={onClick}
        disabled={disabled || loading}
        title="Refresh news data"
      >
        <span className={`refresh-icon ${loading ? 'spinning' : ''}`}>
          🔄
        </span>
        {loading ? 'Refreshing...' : 'Refresh'}
      </button>
      {lastUpdated && (
        <span className="last-updated">
          Last updated: {lastUpdated}
        </span>
      )}
    </div>
  );
};

export default RefreshButton;