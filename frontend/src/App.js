import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import NodeCreation from './pages/NodeCreation';
import Prediction from './pages/Prediction';
import ModelComparison from './pages/ModelComparison';
import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <Router>
      <div className={`App ${darkMode ? 'dark-mode' : ''}`}>
        <Navbar 
          onToggleSidebar={toggleSidebar} 
          darkMode={darkMode} 
          onToggleDarkMode={toggleDarkMode} 
        />
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className={`main-content ${sidebarOpen ? 'sidebar-open' : ''}`}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/node-creation" element={<NodeCreation />} />
            <Route path="/prediction" element={<Prediction />} />
            <Route path="/model-comparison" element={<ModelComparison />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;