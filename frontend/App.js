/**
 * OpenSquare Main React Application
 * Conversational AI interface for financial transparency
 */

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Upload, Home, MessageSquare, FileText, AlertCircle } from 'lucide-react';
import './App.css';

// API base URL - adjust if backend is on different server
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function App() {
  // State management
  const [currentPage, setCurrentPage] = useState('home'); // home, chat, documents
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [apiStatus, setApiStatus] = useState('checking');
  const messagesEndRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check API health on load
  useEffect(() => {
    checkApiHealth();
    loadDocuments();
  }, []);

  // Check if backend is running
  const checkApiHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      if (response.data.status === 'success') {
        setApiStatus('online');
      }
    } catch (error) {
      setApiStatus('offline');
      console.error('API Health Check Failed:', error);
    }
  };

  // Load documents from backend
  const loadDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`);
      if (response.data.status === 'success') {
        setDocuments(response.data.documents);
      }
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  // Handle chat message send
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;

    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages([...messages, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Send query to backend
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        query: inputValue
      });

      // Add AI response
      const aiMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      // Show error message
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Error: Could not connect to backend. Please check if the server is running.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle file upload
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('organization', 'Sample Organization');
    formData.append('doc_type', 'Financial Document');
    formData.append('year', new Date().getFullYear());

    setIsLoading(true);
    setUploadProgress(0);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentComplete = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentComplete);
        }
      });

      if (response.data.status === 'success') {
        // Add success message to chat
        const successMessage = {
          id: Date.now(),
          type: 'success',
          content: `✅ ${response.data.filename} uploaded successfully (${response.data.size})`,
          timestamp: new Date()
        };
        setMessages([...messages, successMessage]);
        loadDocuments();
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now(),
        type: 'error',
        content: `Error uploading file: ${error.response?.data?.message || error.message}`,
        timestamp: new Date()
      };
      setMessages([...messages, errorMessage]);
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  // Load sample documents for demo
  const loadSampleData = async () => {
    try {
      await axios.post(`${API_BASE_URL}/init`);
      loadDocuments();
      const msg = {
        id: Date.now(),
        type: 'success',
        content: '✅ Sample documents loaded! Try asking about "COVID relief", "healthcare spending", or "education budget"',
        timestamp: new Date()
      };
      setMessages([...messages, msg]);
    } catch (error) {
      console.error('Error loading sample data:', error);
    }
  };

  // Render chat page
  const renderChat = () => (
    <div className="chat-container">
      <div className="chat-header">
        <div>
          <h1>OpenSquare AI Assistant</h1>
          <p>Ask questions about public spending and financial data</p>
        </div>
        <div className="status-indicator" style={{ color: apiStatus === 'online' ? '#10b981' : '#ef4444' }}>
          {apiStatus === 'online' ? '🟢 Online' : '🔴 Offline'}
        </div>
      </div>

      <div className="messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <MessageSquare size={48} />
            <h2>Start Exploring Financial Data</h2>
            <p>Upload documents or ask questions about public spending</p>
            <button className="btn-primary" onClick={loadSampleData}>
              Load Sample Data
            </button>
          </div>
        )}
        
        {messages.map(message => (
          <div key={message.id} className={`message message-${message.type}`}>
            <div className="message-content">
              {message.content}
              {message.sources && (
                <div className="sources">
                  <strong>Sources:</strong>
                  {message.sources.map((source, idx) => (
                    <div key={idx} className="source">
                      📄 {source.title} ({source.organization})
                    </div>
                  ))}
                </div>
              )}
            </div>
            <span className="message-time">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
        ))}
        
        {isLoading && (
          <div className="message message-loading">
            <div className="spinner"></div>
            <span>Thinking...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <form onSubmit={handleSendMessage} className="chat-form">
          <label className="file-upload">
            <Upload size={20} />
            <input 
              type="file" 
              onChange={handleFileUpload}
              accept=".pdf,.xlsx,.xls,.csv"
              disabled={isLoading}
            />
          </label>
          
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about spending, budgets, organizations..."
            disabled={isLoading || apiStatus === 'offline'}
          />
          
          <button 
            type="submit" 
            disabled={isLoading || !inputValue.trim() || apiStatus === 'offline'}
            className="btn-send"
          >
            <Send size={20} />
          </button>
        </form>
        
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="upload-progress">
            <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
            <span>{uploadProgress}%</span>
          </div>
        )}
      </div>
    </div>
  );

  // Render documents page
  const renderDocuments = () => (
    <div className="documents-container">
      <div className="documents-header">
        <h1>Uploaded Documents</h1>
        <p>Total: {documents.length} documents indexed</p>
      </div>

      <div className="documents-grid">
        {documents.length === 0 ? (
          <div className="empty-state">
            <FileText size={48} />
            <h2>No Documents Yet</h2>
            <p>Upload financial documents to get started</p>
            <button className="btn-primary" onClick={() => setCurrentPage('chat')}>
              Go to Chat
            </button>
          </div>
        ) : (
          documents.map(doc => (
            <div key={doc.id} className="document-card">
              <h3>{doc.title}</h3>
              <p><strong>Organization:</strong> {doc.organization}</p>
              <p><strong>Type:</strong> {doc.doc_type}</p>
              <p><strong>Year:</strong> {doc.year}</p>
              <p className="text-sm text-gray">
                Uploaded: {new Date(doc.uploaded_at).toLocaleDateString()}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );

  // Render home page
  const renderHome = () => (
    <div className="home-container">
      <div className="hero">
        <h1>🔐 OpenSquare</h1>
        <p className="tagline">No Hidden Space for Financial Misappropriation</p>
        <p className="description">
          AI-powered platform making public spending transparent and understandable
        </p>
        
        <div className="features">
          <div className="feature">
            <MessageSquare size={32} />
            <h3>Conversational AI</h3>
            <p>Ask questions about spending in plain language</p>
          </div>
          <div className="feature">
            <FileText size={32} />
            <h3>Upload Documents</h3>
            <p>Upload PDFs, Excel files, and CSV documents</p>
          </div>
          <div className="feature">
            <AlertCircle size={32} />
            <h3>Smart Alerts</h3>
            <p>Get notified about suspicious spending patterns</p>
          </div>
        </div>

        <button className="btn-primary btn-large" onClick={() => setCurrentPage('chat')}>
          Start Exploring
        </button>
      </div>

      {apiStatus === 'offline' && (
        <div className="warning">
          <AlertCircle />
          <p>⚠️ Backend API is offline. Please start the Flask server.</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-brand">
          <h2>OpenSquare</h2>
        </div>
        <div className="nav-buttons">
          <button 
            className={currentPage === 'home' ? 'active' : ''}
            onClick={() => setCurrentPage('home')}
          >
            <Home size={20} /> Home
          </button>
          <button 
            className={currentPage === 'chat' ? 'active' : ''}
            onClick={() => setCurrentPage('chat')}
          >
            <MessageSquare size={20} /> Chat
          </button>
          <button 
            className={currentPage === 'documents' ? 'active' : ''}
            onClick={() => setCurrentPage('documents')}
          >
            <FileText size={20} /> Docs
          </button>
        </div>
      </nav>

      <main className="main-content">
        {currentPage === 'home' && renderHome()}
        {currentPage === 'chat' && renderChat()}
        {currentPage === 'documents' && renderDocuments()}
      </main>
    </div>
  );
}

export default App;
