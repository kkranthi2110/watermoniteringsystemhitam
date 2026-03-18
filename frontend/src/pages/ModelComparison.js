import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';

const ModelComparison = () => {
  // Hardcoded based on the training_log.md experiments
  const [modelData, setModelData] = useState([
    { name: 'Baseline LSTM', accuracy: 86.15, f1: 67.5, type: 'LSTM', layers: 2 },
    { name: 'Bi-LSTM + BN', accuracy: 88.29, f1: 80.1, type: 'LSTM', layers: 3 },
    { name: 'Deep CNN + GAP', accuracy: 84.86, f1: 61.9, type: 'CNN', layers: 3 },
    { name: 'Enhanced GRU', accuracy: 92.66, f1: 88.4, type: 'GRU', layers: 3 },
    { name: 'CNN-LSTM Hybrid', accuracy: 85.92, f1: 71.1, type: 'Hybrid', layers: 4 }
  ]);

  return (
    <div className="page-container model-comparison-page fade-in">
      <h1 className="page-title">ML Model Comparison</h1>
      <p className="page-subtitle">A deep dive into the 5 model architectures tested for water activity classification.</p>

      <div className="charts-grid">
        <div className="chart-card full-width">
          <h3>Accuracy vs F1 Score</h3>
          <p className="chart-subtitle">Comparing the performance metrics across different models</p>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={modelData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
              <XAxis dataKey="name" tick={{fill: 'var(--text-secondary)'}} />
              <YAxis yAxisId="left" orientation="left" stroke="var(--primary-color)" domain={[60, 100]} />
              <YAxis yAxisId="right" orientation="right" stroke="var(--info-color)" domain={[50, 100]} />
              <Tooltip 
                contentStyle={{backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-light)'}} 
                itemStyle={{color: 'var(--text-primary)'}}
              />
              <Legend />
              <Bar yAxisId="left" dataKey="accuracy" name="Accuracy (%)" fill="var(--primary-color)" radius={[4, 4, 0, 0]} animationDuration={1500} />
              <Bar yAxisId="right" dataKey="f1" name="F1 Score (x100)" fill="var(--info-color)" radius={[4, 4, 0, 0]} animationDuration={1500} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Performance Radar</h3>
          <p className="chart-subtitle">Multidimensional comparison</p>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={modelData}>
              <PolarGrid stroke="var(--border-color)" />
              <PolarAngleAxis dataKey="name" tick={{fill: 'var(--text-secondary)', fontSize: 11}} />
              <PolarRadiusAxis angle={30} domain={[60, 100]} tick={{fill: 'var(--text-muted)'}} />
              <Radar name="Accuracy" dataKey="accuracy" stroke="var(--primary-color)" fill="var(--primary-color)" fillOpacity={0.4} />
              <Radar name="F1 Score" dataKey="f1" stroke="var(--info-color)" fill="var(--info-color)" fillOpacity={0.4} />
              <Tooltip contentStyle={{backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-light)'}} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Model Training Log</h3>
          <div className="table-responsive" style={{overflowX: 'auto', marginTop: '10px'}}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Experiment</th>
                  <th>Type</th>
                  <th>Layers</th>
                  <th>Accuracy</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {modelData.map((model, index) => (
                  <tr key={index}>
                    <td>{model.name}</td>
                    <td>{model.type}</td>
                    <td>{model.layers}</td>
                    <td style={{fontWeight: model.accuracy > 90 ? 'bold' : 'normal', color: model.accuracy > 90 ? 'var(--primary-dark)' : 'inherit'}}>
                      {model.accuracy}%
                    </td>
                    <td>
                      {model.accuracy === 92.66 ? 
                        <span className="badge success">Deployed Best Model</span> : 
                        <span className="badge secondary">Archived</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelComparison;
