import React from 'react';

const Navbar = ({ onToggleSidebar, darkMode, onToggleDarkMode }) => {
  return (
    <nav className="navbar">
      <div className="navbar-left">
        <button className="hamburger-btn" onClick={onToggleSidebar}>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
        </button>
        
        <div className="logo">
          <img src="/hitam-logo.svg" alt="HITAM Logo" className="logo-img" />
        </div>
      </div>
      
      <div className="navbar-center">
        <h1 className="navbar-title">HITAM IoT Water Monitoring System</h1>
        <p className="navbar-subtitle">find your path</p>
      </div>
      
      <div className="navbar-right">
        <button className="theme-toggle-btn" onClick={onToggleDarkMode} aria-label="Toggle Dark Mode" title="Toggle Dark Mode">
          {darkMode ? '☀️' : '🌙'}
        </button>
      </div>

    </nav>
  );
};

export default Navbar;