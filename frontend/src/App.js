import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncAmount, setSyncAmount] = useState('');
  const [message, setMessage] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchStatus = async () => {
    try {
      const res = await axios.get('/api/status');
      setStatus(res.data);
      setLastUpdated(new Date());
      setLoading(false);
    } catch (err) {
      console.error(err);
      setMessage('Failed to fetch status. Backend might be down or key is invalid.');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Auto-refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const handleSync = async (e) => {
    e.preventDefault();
    if (!syncAmount) return;
    try {
      await axios.post('/api/sync', { amount: parseFloat(syncAmount) });
      setSyncAmount('');
      setMessage('Balance synced successfully!');
      fetchStatus();
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage('Error syncing balance.');
    }
  };

  const handleCheckNow = async () => {
    try {
        await axios.post('/api/check-now');
        setMessage('Immediate check triggered. Refresh shortly.');
        setTimeout(fetchStatus, 2000); // Fetch after 2 seconds to see result
    } catch (err) {
        setMessage('Error triggering check.');
    }
  }

  if (loading) return <div className="App"><div className="container">Loading...</div></div>;

  const threshold = status ? status.threshold : 10.0;
  const isLowBalance = status && status.balance < threshold;

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>OpenAI Financial Monitor</h1>
          <div className={`status-badge ${isLowBalance ? 'danger' : 'success'}`}>
            <span className="status-dot"></span>
            {isLowBalance ? 'Low Balance' : 'Healthy'}
          </div>
        </header>

        {status && (
          <div className="dashboard-grid">
            <div className="card balance-card">
              <h2>Estimated Balance</h2>
              <div className="big-number">${status.balance.toFixed(2)}</div>
              <p className="threshold-text">Alert Threshold: ${threshold.toFixed(2)}</p>
            </div>

            <div className="card stats-card">
              <h2>Statistics</h2>
              <div className="stat-row">
                <span className="stat-label">Total Deposited</span>
                <span className="stat-value">${status.total_deposited.toFixed(2)}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Total API Spend</span>
                <span className="stat-value">${status.total_spend.toFixed(2)}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Usage (Today)</span>
                <span className="stat-value">${status.daily_usage.toFixed(2)}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Usage (Month)</span>
                <span className="stat-value">${status.monthly_usage.toFixed(2)}</span>
              </div>
              <div className="stat-row" style={{marginTop: '12px', border: 'none', flexDirection: 'column', alignItems: 'flex-start', gap: '8px'}}>
                 <button onClick={handleCheckNow} className="btn-text">Check for updates now →</button>
                 {lastUpdated && (
                   <span className="help-text" style={{margin: 0, fontSize: '0.7rem'}}>
                     Last updated: {lastUpdated.toLocaleTimeString()} (Auto-refreshing every 10s)
                   </span>
                 )}
              </div>
            </div>

            <div className="card sync-card">
              <h2>Sync Balance</h2>
              <p className="help-text">Calibrate with exact amount from OpenAI Dashboard.</p>
              <form onSubmit={handleSync}>
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
                <button type="submit" className="btn-secondary">Sync Balance</button>
              </form>
            </div>

            {/* Monthly History Section */}
            <div className="card history-card" style={{gridColumn: '1 / -1'}}>
              <h2>Monthly Spend History</h2>
              <div className="history-table-container">
                <table className="history-table">
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th>Spend Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {status.history && status.history.length > 0 ? (
                      status.history.map((item, index) => (
                        <tr key={index}>
                          <td>{item.month}</td>
                          <td>${item.amount.toFixed(2)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="2" style={{textAlign: 'center', color: '#888'}}>No history data available yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {message && <div className="toast">{message}</div>}
      </div>
    </div>
  );
}

export default App;
