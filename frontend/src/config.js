// src/config.js
// Central config for API URLs and other constants

// Use environment variable for production, fallback to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:8000";

const config = {
  API_BASE_URL,
  SENSOR_DATA_URL: `${API_BASE_URL}/sensor-data`,
  TANK_PARAMETERS_URL: `${API_BASE_URL}/tank-parameters`,
  PREDICT_URL: `${API_BASE_URL}/api/v1/predict`,
  MODEL_INFO_URL: `${API_BASE_URL}/api/v1/model-info`,
  PREDICTIONS_HISTORY_URL: `${API_BASE_URL}/api/v1/predictions-history`,
};

export default config;
