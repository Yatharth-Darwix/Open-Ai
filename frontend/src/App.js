import React, { useState, useEffect } from 'react';
import axios from 'axios';
import BalanceDisplay from './components/BalanceDisplay';
import UsageStats from './components/UsageStats';
import HistoryTable from './components/HistoryTable';
import ControlPanel from './components/ControlPanel';
import './App.css';

function App() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
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
      setMessage('Failed to fetch status. Backend might be down.');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); 
    return () => clearInterval(interval);
  }, []);

  const handleSync = async (amount) => {
    try {
      await axios.post('/api/sync', { amount });
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
        setMessage('Immediate check triggered. Refreshing...');
        setTimeout(fetchStatus, 2000); 
    } catch (err) {
        setMessage('Error triggering check.');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading Financial Data...</p>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <div className="header-brand">
            <h1>OpenAI Monitor</h1>
            <span className="badge-beta">PRO</span>
          </div>
        </header>

        {status && (
          <div className="dashboard-grid">
            <BalanceDisplay 
              balance={status.balance} 
              threshold={status.threshold} 
            />
            
            <UsageStats stats={status} />
            
            <ControlPanel 
              onSync={handleSync} 
              onCheckNow={handleCheckNow} 
              lastUpdated={lastUpdated} 
            />

            <HistoryTable history={status.history} />
          </div>
        )}

        {message && <div className="toast">{message}</div>}
      </div>
    </div>
  );
}

export default App;