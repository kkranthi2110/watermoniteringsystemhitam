import React, { useState } from 'react';
import axios from 'axios';
import config from '../config';

const Login = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/api/v1/auth/login' : '/api/v1/auth/register';
      const response = await axios.post(`${config.API_BASE_URL}${endpoint}`, {
        username,
        password
      });

      if (isLogin) {
        // Mock token logic
        const token = response.data.access_token;
        localStorage.setItem('auth_token', token);
        onLogin(true);
      } else {
        // Register success, switch to login
        setIsLogin(true);
        setError('Registration successful! Please login.');
      }
    } catch (err) {
      if (err.response) {
        setError(err.response.data.detail);
      } else {
        setError('Server error occurred.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'var(--bg-primary)' }}>
      <div className="login-card" style={{ background: 'var(--bg-card)', padding: '40px', borderRadius: '12px', boxShadow: 'var(--shadow)', width: '100%', maxWidth: '400px' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '10px' }}>
          {isLogin ? 'Welcome Back' : 'Create Account'}
        </h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '30px' }}>
          HITAM IoT Water Monitoring
        </p>

        {error && (
          <div className="error-message" style={{ marginBottom: '20px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label>Username</label>
            <input 
              type="text" 
              required 
              value={username} 
              onChange={e => setUsername(e.target.value)} 
              placeholder="admin"
            />
          </div>
          
          <div className="form-group" style={{ margin: 0 }}>
            <label>Password</label>
            <input 
              type="password" 
              required 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              placeholder="admin123"
            />
          </div>

          <button type="submit" disabled={loading} className="predict-btn" style={{ width: '100%', marginTop: '10px', background: 'var(--primary-color)' }}>
            {loading ? 'Processing...' : (isLogin ? 'Login to Dashboard' : 'Register')}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '14px' }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <span 
            onClick={() => { setIsLogin(!isLogin); setError(''); }}
            style={{ color: 'var(--primary-color)', cursor: 'pointer', fontWeight: 'bold' }}
          >
            {isLogin ? 'Sign up' : 'Log in'}
          </span>
        </p>
      </div>
    </div>
  );
};

export default Login;
