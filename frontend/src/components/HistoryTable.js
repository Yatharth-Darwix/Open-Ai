import React, { useState } from 'react';

function HistoryTable({ history }) {
  const [selectedYear, setSelectedYear] = useState('All');

  const years = ['All', ...new Set(history.map(item => {
    const yearMatch = item.month.match(/\d{4}$/);
    return yearMatch ? yearMatch[0] : null;
  }).filter(Boolean))];

  const filteredHistory = selectedYear === 'All' 
    ? history 
    : history.filter(item => item.month.endsWith(selectedYear));

  return (
    <div className="card history-card">
      <div className="card-header-row">
        <h2>Monthly Expenses</h2>
        <div className="filter-group">
          <select 
            className="dropdown"
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
          >
            {years.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="history-table-container">
        <table className="history-table">
          <thead>
            <tr>
              <th>Month</th>
              <th>Total Spend</th>
              <th>Trend</th>
            </tr>
          </thead>
          <tbody>
            {filteredHistory.length > 0 ? (
              filteredHistory.map((item, index) => {
                const prevMonth = history[history.indexOf(item) + 1];
                let trend = '—';
                if (prevMonth && prevMonth.amount > 0) {
                    const diff = item.amount - prevMonth.amount;
                    const percent = (diff / prevMonth.amount) * 100;
                    trend = (
                        <span style={{ color: diff > 0 ? '#ef4444' : '#10b981', fontSize: '0.8rem' }}>
                            {diff > 0 ? '↑' : '↓'} {Math.abs(percent).toFixed(0)}%
                        </span>
                    );
                }

                return (
                  <tr key={index}>
                    <td>{item.month}</td>
                    <td>${item.amount.toFixed(2)}</td>
                    <td>{trend}</td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan="3" style={{textAlign: 'center', color: '#888', padding: '20px'}}>
                  No data for the selected period.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default HistoryTable;