import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import config from '../config';

const Prediction = () => {
  const [distance, setDistance] = useState('');
  const [temperature, setTemperature] = useState('');
  const [timeFeatures, setTimeFeatures] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [modelInfo, setModelInfo] = useState(null);
  const [predictionHistory, setPredictionHistory] = useState([]);

  const [batchFile, setBatchFile] = useState(null);
  const [batchResults, setBatchResults] = useState([]);
  const [batchLoading, setBatchLoading] = useState(false);

  // Fetch model information on component mount
  useEffect(() => {
    const fetchModelInfo = async () => {
      try {
        const response = await axios.get(config.MODEL_INFO_URL);
        setModelInfo(response.data);
      } catch (err) {
        console.error('Error fetching model info:', err);
      }
    };
    fetchModelInfo();
  }, []);

  const handleBatchSubmit = async (e) => {
    e.preventDefault();
    if (!batchFile) return;
    
    setBatchLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', batchFile);
    
    try {
      const response = await axios.post(`${config.API_BASE_URL}/api/v1/predict/batch`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setBatchResults(response.data.results);
    } catch (err) {
      setError('Failed to process batch file. Please check the CSV format.');
      console.error('Batch error:', err);
    } finally {
      setBatchLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setPrediction(null);
    setConfidence(null);

    try {
      // Parse time features (comma-separated)
      const timeFeaturesArray = timeFeatures.split(',').map(f => parseFloat(f.trim())).filter(f => !isNaN(f));

      const requestData = {
        distance: parseFloat(distance),
        temperature: parseFloat(temperature),
        time_features: timeFeaturesArray
      };

      const response = await axios.post(config.PREDICT_URL, requestData);

      const confidencePercent = (response.data.confidence * 100).toFixed(2);
      setPrediction(response.data.prediction);
      setConfidence(confidencePercent);

      // Add to history
      const newHistory = [{
        prediction: response.data.prediction,
        confidence: confidencePercent,
        distance: parseFloat(distance),
        temperature: parseFloat(temperature),
        timestamp: new Date().toLocaleTimeString()
      }, ...predictionHistory].slice(0, 10); // Keep last 10 predictions
      
      setPredictionHistory(newHistory);
    } catch (err) {
      setError('Failed to get prediction. Please check your input and try again.');
      console.error('Prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="prediction-page">
      <h1 className="page-title">Water Activity Prediction</h1>
      <p className="page-subtitle">Use the advanced ML model to predict water usage activity based on sensor readings.</p>

      {/* Model Information Card */}
      {modelInfo && (
        <div className="model-info-section">
          <h2>Model Information</h2>
          <div className="model-grid">
            <div className="model-card">
              <span className="label">Model Type:</span>
              <span className="value">{modelInfo.model_type}</span>
            </div>
            <div className="model-card">
              <span className="label">Accuracy:</span>
              <span className="value">{(modelInfo.accuracy * 100).toFixed(1)}%</span>
            </div>
            <div className="model-card">
              <span className="label">Version:</span>
              <span className="value">{modelInfo.version}</span>
            </div>
            <div className="model-card">
              <span className="label">Classes:</span>
              <span className="value">{modelInfo.classes?.join(', ') || 'N/A'}</span>
            </div>
          </div>
        </div>
      )}

        <div className="form-row" style={{ alignItems: 'flex-start' }}>
          <form onSubmit={handleSubmit} className="prediction-form" style={{ flex: 1, margin: 0 }}>
            <h2>Single Prediction</h2>
            <div className="form-group">
              <label htmlFor="distance">Distance (cm):</label>
              <input
                type="number"
                id="distance"
                value={distance}
                onChange={(e) => setDistance(e.target.value)}
                step="0.01"
                required
                placeholder="e.g., 85.5"
              />
            </div>

            <div className="form-group">
              <label htmlFor="temperature">Temperature (°C):</label>
              <input
                type="number"
                id="temperature"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                step="0.01"
                required
                placeholder="e.g., 25.3"
              />
            </div>

            <div className="form-group">
              <label htmlFor="timeFeatures">Time Features (comma-separated):</label>
              <input
                type="text"
                id="timeFeatures"
                value={timeFeatures}
                onChange={(e) => setTimeFeatures(e.target.value)}
                placeholder="e.g., 0.5, 0.8, 0.2"
              />
              <small>Optional: Additional time-based features for better prediction</small>
            </div>

            <button type="submit" disabled={loading} className="predict-btn" style={{ width: '100%' }}>
              {loading ? 'Predicting...' : 'Get Prediction'}
            </button>
          </form>

          <form onSubmit={handleBatchSubmit} className="prediction-form" style={{ flex: 1, margin: 0 }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge info">BONUS</span> Batch Predictions
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px' }}>
              Upload a CSV file to process multiple sensor readings at once. The CSV must contain `distance` and `temperature` columns.
            </p>
            
            <div className="form-group">
              <label htmlFor="csvFile">Upload CSV File:</label>
              <input
                type="file"
                id="csvFile"
                accept=".csv"
                onChange={(e) => setBatchFile(e.target.files[0])}
                required
                style={{ padding: '8px', background: 'var(--bg-primary)' }}
              />
            </div>

            <button type="submit" disabled={batchLoading || !batchFile} className="submit-btn" style={{ width: '100%', marginTop: 'auto' }}>
              {batchLoading ? 'Processing Batch...' : 'Process CSV'}
            </button>
          </form>
        </div>

      {error && <div className="error-message">{error}</div>}

      {/* Batch Results Table */}
      {batchResults.length > 0 && (
        <div className="history-section" style={{ marginTop: '30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2>Batch Prediction Results</h2>
            <span className="badge success">Processed {batchResults.length} rows</span>
          </div>
          <div className="table-responsive" style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <table className="data-table">
              <thead style={{ position: 'sticky', top: 0, zIndex: 1 }}>
                <tr>
                  <th>#</th>
                  <th>Distance (cm)</th>
                  <th>Temp (°C)</th>
                  <th>Predicted Activity</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {batchResults.map((result, index) => (
                  <tr key={index}>
                    <td>{index + 1}</td>
                    <td>{result.distance.toFixed(1)}</td>
                    <td>{result.temperature.toFixed(1)}</td>
                    <td style={{ fontWeight: 'bold', color: 'var(--primary-dark)' }}>
                      {result.prediction.replace(/_/g, ' ').toUpperCase()}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '60px', height: '6px', background: 'var(--border-light)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ width: `${result.confidence * 100}%`, height: '100%', background: 'var(--success-color)' }}></div>
                        </div>
                        <span style={{ fontSize: '0.8rem' }}>{(result.confidence * 100).toFixed(1)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {prediction && (
        <div className="prediction-results-section">
          <h2>Prediction Results</h2>
          <div className="results-grid">
            <div className="result-card">
              <h3>Predicted Activity</h3>
              <div className="activity-label">
                {prediction.replace(/_/g, ' ').toUpperCase()}
              </div>
              <div className="confidence-display">
                <div className="confidence-text">
                  Confidence: {confidence}%
                </div>
                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={{ width: `${confidence}%`, background: 'linear-gradient(90deg, var(--primary-color), var(--primary-light))' }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="result-card chart-card">
              <h3>Confidence Distribution</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Confidence', value: parseFloat(confidence) },
                      { name: 'Uncertainty', value: 100 - parseFloat(confidence) }
                    ]}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    <Cell fill="var(--primary-color)" />
                    <Cell fill="#e0e0e0" />
                  </Pie>
                  <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {predictionHistory.length > 0 && (
        <div className="history-section">
          <h2>Prediction History</h2>
          <div className="history-chart">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={predictionHistory.reverse()}
                margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis 
                  dataKey="timestamp" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis label={{ value: 'Confidence (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'white', border: `1px solid var(--border-color)` }}
                  formatter={(value) => [`${value}%`, 'Confidence']}
                />
                <Bar dataKey="confidence" fill="var(--primary-color)" name="Confidence" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default Prediction;