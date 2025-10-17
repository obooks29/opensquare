/**
 * OpenSquare Frontend - Entry Point
 * Renders the React App into the DOM
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Get the root element from public/index.html
const root = ReactDOM.createRoot(document.getElementById('root'));

// Render the main App component
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
