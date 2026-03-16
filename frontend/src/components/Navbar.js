import React from 'react';

const Navbar = ({ onToggleSidebar }) => {
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
      
      {/* <div className="navbar-right">
        <div className="notification-icon">
          <svg 
            width="24" 
            height="24" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
            strokeLinecap="round" 
            strokeLinejoin="round"
          >
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
          <span className="notification-badge">3</span>
        </div>
      </div> */}
    </nav>
  );
};

export default Navbar;