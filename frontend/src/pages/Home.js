import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  AreaChart, Area,
  BarChart, Bar,
  PieChart, Pie, Cell
} from 'recharts';
import config from '../config';

const CHART_COLORS = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#00BCD4'];

const Home = () => {
  const [sensorData, setSensorData] = useState([]);
  const [predictionHistory, setPredictionHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchData = async () => {
    try {
      const [sensorRes, predRes] = await Promise.all([
        axios.get(config.SENSOR_DATA_URL),
        axios.get(config.PREDICTIONS_HISTORY_URL + '?limit=50').catch(() => ({ data: [] }))
      ]);

      // Reverse sensor data so it's chronological (oldest first)
      const chronologicalData = [...(sensorRes.data || [])].reverse();
      setSensorData(chronologicalData);
      setPredictionHistory(predRes.data || []);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // Compute stats
  const latestReading = sensorData.length > 0 ? sensorData[sensorData.length - 1] : null;
  const avgDistance = sensorData.length > 0
    ? (sensorData.reduce((sum, d) => sum + (d.distance || 0), 0) / sensorData.length).toFixed(1)
    : '—';
  const avgTemp = sensorData.length > 0
    ? (sensorData.reduce((sum, d) => sum + (d.temperature || 0), 0) / sensorData.length).toFixed(1)
    : '—';
  const totalReadings = sensorData.length;

  // Prediction distribution for pie chart
  const predictionCounts = {};
  predictionHistory.forEach(p => {
    const label = p.prediction || 'unknown';
    predictionCounts[label] = (predictionCounts[label] || 0) + 1;
  });
  const pieData = Object.entries(predictionCounts).map(([name, value]) => ({ name, value }));

  // Format chart data labels
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Activity timeline data from predictions
  const activityTimeline = predictionHistory.slice(0, 20).reverse().map(p => ({
    time: formatTime(p.created_at),
    confidence: (p.confidence * 100).toFixed(1),
    prediction: p.prediction,
    distance: p.distance,
  }));

  if (loading) {
    return (
      <div className="home-page">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="home-page">
      <h1>HITAM IoT Water Monitoring Dashboard</h1>
      <p>
        Real-time sensor data and ML-powered water activity predictions
        {lastUpdate && (
          <span className="realtime-badge">
            <span className="realtime-dot"></span>
            Last updated: {lastUpdate}
          </span>
        )}
      </p>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📏</div>
          <div className="stat-value">{latestReading ? latestReading.distance?.toFixed(1) : '—'}</div>
          <div className="stat-label">Current Distance (cm)</div>
          <div className="stat-change positive">● Live</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🌡️</div>
          <div className="stat-value">{latestReading ? latestReading.temperature?.toFixed(1) : '—'}°C</div>
          <div className="stat-label">Current Temperature</div>
          <div className="stat-change positive">● Live</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-value">{avgDistance}</div>
          <div className="stat-label">Avg Distance (cm)</div>
          <div className="stat-change positive">↑ {totalReadings} readings</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🤖</div>
          <div className="stat-value">{predictionHistory.length}</div>
          <div className="stat-label">Total Predictions</div>
          <div className="stat-change positive">ML Model Active</div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="charts-grid">
        {/* Distance Over Time - Area Chart */}
        <div className="chart-card">
          <h3>
            Water Level Distance
            <span className="realtime-badge">
              <span className="realtime-dot"></span>
              Live
            </span>
          </h3>
          <p className="chart-subtitle">Distance sensor readings over time (cm)</p>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={sensorData.slice(-30)} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="distanceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4CAF50" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#4CAF50" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8f0e8" />
              <XAxis
                dataKey="created_at"
                tickFormatter={formatTime}
                tick={{ fontSize: 11 }}
                stroke="#7a9a7a"
              />
              <YAxis tick={{ fontSize: 11 }} stroke="#7a9a7a" />
              <Tooltip
                contentStyle={{
                  background: 'white',
                  border: '1px solid #d4e5d4',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                }}
                labelFormatter={formatTime}
                formatter={(value) => [`${value} cm`, 'Distance']}
              />
              <Area
                type="monotone"
                dataKey="distance"
                stroke="#4CAF50"
                strokeWidth={2.5}
                fill="url(#distanceGradient)"
                animationDuration={800}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Temperature Over Time - Line Chart */}
        <div className="chart-card">
          <h3>
            Temperature Readings
            <span className="realtime-badge">
              <span className="realtime-dot"></span>
              Live
            </span>
          </h3>
          <p className="chart-subtitle">Temperature sensor readings over time (°C)</p>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={sensorData.slice(-30)} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8f0e8" />
              <XAxis
                dataKey="created_at"
                tickFormatter={formatTime}
                tick={{ fontSize: 11 }}
                stroke="#7a9a7a"
              />
              <YAxis tick={{ fontSize: 11 }} stroke="#7a9a7a" />
              <Tooltip
                contentStyle={{
                  background: 'white',
                  border: '1px solid #d4e5d4',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                }}
                labelFormatter={formatTime}
                formatter={(value) => [`${value}°C`, 'Temperature']}
              />
              <Line
                type="monotone"
                dataKey="temperature"
                stroke="#2196F3"
                strokeWidth={2.5}
                dot={{ r: 3, fill: '#2196F3' }}
                activeDot={{ r: 6, stroke: '#2196F3', strokeWidth: 2, fill: 'white' }}
                animationDuration={800}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Prediction Distribution - Pie Chart */}
        {pieData.length > 0 && (
          <div className="chart-card">
            <h3>Prediction Distribution</h3>
            <p className="chart-subtitle">Breakdown of ML-predicted water activities</p>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                  animationDuration={800}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [value, 'Count']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Activity Timeline - Bar Chart */}
        {activityTimeline.length > 0 && (
          <div className="chart-card">
            <h3>Prediction Confidence Timeline</h3>
            <p className="chart-subtitle">Recent prediction confidence scores (%)</p>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={activityTimeline} margin={{ top: 5, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e8f0e8" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 10 }}
                  angle={-45}
                  textAnchor="end"
                  height={50}
                  stroke="#7a9a7a"
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  stroke="#7a9a7a"
                  domain={[0, 100]}
                />
                <Tooltip
                  contentStyle={{
                    background: 'white',
                    border: '1px solid #d4e5d4',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  }}
                  formatter={(value, name, props) => [
                    `${value}%`,
                    `Confidence (${props.payload.prediction})`
                  ]}
                />
                <Bar
                  dataKey="confidence"
                  fill="#4CAF50"
                  radius={[6, 6, 0, 0]}
                  animationDuration={800}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Combined Distance + Temperature Chart */}
      <div className="charts-grid">
        <div className="chart-card full-width">
          <h3>Distance vs Temperature Correlation</h3>
          <p className="chart-subtitle">Combined view of both sensor parameters over time</p>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sensorData.slice(-40)} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8f0e8" />
              <XAxis
                dataKey="created_at"
                tickFormatter={formatTime}
                tick={{ fontSize: 11 }}
                stroke="#7a9a7a"
              />
              <YAxis yAxisId="left" tick={{ fontSize: 11 }} stroke="#4CAF50" />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} stroke="#2196F3" />
              <Tooltip
                contentStyle={{
                  background: 'white',
                  border: '1px solid #d4e5d4',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                }}
                labelFormatter={formatTime}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="distance"
                stroke="#4CAF50"
                strokeWidth={2}
                dot={false}
                name="Distance (cm)"
                animationDuration={800}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="temperature"
                stroke="#2196F3"
                strokeWidth={2}
                dot={false}
                name="Temperature (°C)"
                animationDuration={800}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Sensor Data Table */}
      <div className="recent-data-section">
        <h3>
          Recent Sensor Readings
          <span className="realtime-badge">
            <span className="realtime-dot"></span>
            Auto-refresh 30s
          </span>
        </h3>
        <div className="nodes-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Node</th>
                <th>Distance (cm)</th>
                <th>Temperature (°C)</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {sensorData.slice(-10).reverse().map((row) => (
                <tr key={row.id}>
                  <td>{row.id}</td>
                  <td style={{ fontWeight: 600, color: '#388E3C' }}>{row.node_id}</td>
                  <td>{row.distance?.toFixed(1)}</td>
                  <td>{row.temperature?.toFixed(1)}</td>
                  <td style={{ fontSize: '0.85rem', color: '#7a9a7a' }}>
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Home;
