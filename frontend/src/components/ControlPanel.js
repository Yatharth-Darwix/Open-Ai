import React, { useState } from 'react';

function ControlPanel({ onSync, onCheckNow, lastUpdated }) {
  const [syncAmount, setSyncAmount] = useState('');

  const handleSyncSubmit = (e) => {
    e.preventDefault();
    if (syncAmount) {
      onSync(parseFloat(syncAmount));
      setSyncAmount('');
    }
  };

  return (
    <div className="card control-card">
      <div className="control-group">
        <h2>Manual Sync</h2>
        <p className="help-text" style={{margin: '0 0 16px 0', fontSize: '0.85rem'}}>Calibrate ledger with OpenAI dashboard.</p>
        <form onSubmit={handleSyncSubmit} className="sync-form">
          <div className="input-group">
            <span className="currency-symbol">$</span>
            <input
              type="number"
              step="0.01"
              placeholder="0.00"
              value={syncAmount}
              onChange={(e) => setSyncAmount(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary">Sync</button>
        </form>
      </div>

      <div className="control-divider"></div>

      <div className="control-group">
        <h2>System Status</h2>
        <div className="status-row">
           <span className="status-label">Last Checked:</span>
           <span className="status-value">
             {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Never'}
           </span>
        </div>
        <button onClick={onCheckNow} className="btn-secondary">
          Trigger Instant Check
        </button>
      </div>
    </div>
  );
}

export default ControlPanel;