import React from 'react';

function UsageStats({ stats }) {
  // Calculate average and projection
  const today = new Date();
  const dayOfMonth = today.getDate();
  const daysInMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
  
  const avgDaily = stats.monthly_usage / dayOfMonth;
  const projection = avgDaily * daysInMonth;

  return (
    <div className="card stats-card">
      <h2>Usage & Insights</h2>
      <div className="stats-grid-inner">
        <div className="stat-item">
          <span className="stat-label">Today</span>
          <span className="stat-value highlight">${stats.daily_usage.toFixed(2)}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">This Month</span>
          <span className="stat-value highlight">${stats.monthly_usage.toFixed(2)}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Avg. Daily</span>
          <span className="stat-value">${avgDaily.toFixed(2)}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Projected</span>
          <span className="stat-value">${projection.toFixed(2)}</span>
        </div>
      </div>
      
      <div className="usage-visual-bar">
        <div className="usage-progress-bg">
          <div 
            className="usage-progress-fill" 
            style={{ width: `${Math.min((dayOfMonth / daysInMonth) * 100, 100)}%` }}
          ></div>
        </div>
        <span className="usage-progress-text">Day {dayOfMonth} of {daysInMonth}</span>
      </div>
    </div>
  );
}

export default UsageStats;