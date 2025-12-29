import React from 'react';

function BalanceDisplay({ balance, threshold }) {
  const isLow = balance < threshold;
  
  return (
    <div className="card balance-card">
      <div className="card-header-row">
        <h2>Remaining Credits</h2>
        <div className={`status-badge ${isLow ? 'danger' : 'success'}`}>
          <span className="status-dot"></span>
          {isLow ? 'Critical Low' : 'Healthy'}
        </div>
      </div>
      
      <div className="big-number">
        <span className="currency">$</span>{balance.toFixed(2)}
      </div>
      
      <div className="threshold-container">
        <div className="threshold-bar-bg">
          <div 
            className="threshold-bar-fill" 
            style={{ 
              width: `${Math.min((balance / (threshold * 5)) * 100, 100)}%`,
              backgroundColor: isLow ? '#ef4444' : '#10b981'
            }}
          ></div>
        </div>
        <p className="threshold-text">Alert triggers below ${threshold.toFixed(2)}</p>
      </div>
    </div>
  );
}

export default BalanceDisplay;