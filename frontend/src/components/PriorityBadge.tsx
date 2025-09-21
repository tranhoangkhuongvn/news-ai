import React from 'react';

interface PriorityBadgeProps {
  priority: 'BREAKING' | 'HIGH' | 'MEDIUM' | 'LOW';
  score?: number;
  size?: 'small' | 'medium' | 'large';
}

const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, score, size = 'medium' }) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'BREAKING':
        return '#ef4444'; // Red
      case 'HIGH':
        return '#f97316'; // Orange
      case 'MEDIUM':
        return '#eab308'; // Yellow
      case 'LOW':
        return '#6b7280'; // Gray
      default:
        return '#6b7280';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'BREAKING':
        return '🚨';
      case 'HIGH':
        return '⚡';
      case 'MEDIUM':
        return '📰';
      case 'LOW':
        return '📄';
      default:
        return '📄';
    }
  };

  const getSizeClasses = (size: string) => {
    switch (size) {
      case 'small':
        return 'px-2 py-1 text-xs';
      case 'large':
        return 'px-4 py-2 text-base';
      default:
        return 'px-3 py-1 text-sm';
    }
  };

  const baseClasses = `inline-flex items-center gap-1 rounded-full font-semibold text-white ${getSizeClasses(size)}`;

  return (
    <span
      className={baseClasses}
      style={{ backgroundColor: getPriorityColor(priority) }}
      title={score ? `Priority Score: ${score}` : undefined}
    >
      <span>{getPriorityIcon(priority)}</span>
      <span>{priority}</span>
      {score && size !== 'small' && (
        <span className="ml-1 text-xs opacity-90">
          {score.toFixed(2)}
        </span>
      )}
    </span>
  );
};

export default PriorityBadge;