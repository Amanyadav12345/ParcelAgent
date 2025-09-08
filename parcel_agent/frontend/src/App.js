import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ParcelForm from './components/ParcelForm';
import ParcelResult from './components/ParcelResult';
import LoginPage from './components/LoginPage';
import authService from './services/authService';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [cities, setCities] = useState([]);
  const [materials, setMaterials] = useState([]);

  // Check authentication status on component mount
  useEffect(() => {
    const checkAuth = () => {
      const authenticated = authService.isAuthenticated();
      const user = authService.getCurrentUser();
      
      setIsAuthenticated(authenticated);
      setCurrentUser(user);
    };
    
    checkAuth();
  }, []);

  // Load available cities and materials when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const loadData = async () => {
        try {
          const [citiesResponse, materialsResponse] = await Promise.all([
            axios.get('/api/cities', {
              headers: authService.getAuthHeaders()
            }),
            axios.get('/api/materials', {
              headers: authService.getAuthHeaders()
            })
          ]);
          setCities(citiesResponse.data.cities || []);
          setMaterials(materialsResponse.data.materials || []);
        } catch (err) {
          console.error('Error loading data:', err);
          // Set fallback data
          setCities(['jaipur', 'kolkata']);
          setMaterials(['paint', 'chemicals']);
        }
      };
      
      loadData();
    }
  }, [isAuthenticated]);

  const handleLogin = async (loginData) => {
    setIsAuthenticated(true);
    setCurrentUser(loginData.user_record);
  };

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
    setCurrentUser(null);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (message) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post('/api/create-parcel', {
        message: message
      }, {
        headers: authService.getAuthHeaders()
      });

      if (response.data.success) {
        setResult(response.data);
      } else {
        setError('Failed to create parcel');
      }
    } catch (err) {
      console.error('Error creating parcel:', err);
      setError(err.response?.data?.detail || 'An error occurred while creating the parcel');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClarifyingResponse = async (clarifyingMessage) => {
    // Append the clarifying response to the previous context and resubmit
    await handleSubmit(clarifyingMessage);
  };

  const resetForm = () => {
    setResult(null);
    setError(null);
  };

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Parcel Agent</h1>
                <p className="text-sm text-gray-600">AI-powered parcel creation system</p>
              </div>
            </div>
            
            {/* User info and logout */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{currentUser?.name}</p>
                <p className="text-xs text-gray-500">{currentUser?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-medium text-blue-800">How to use</h3>
                <div className="text-sm text-blue-700 mt-1">
                  <p>Describe your parcel requirements in natural language. For example:</p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>"Create a parcel for ABC Company from Jaipur to Kolkata, 50kg paint"</li>
                    <li>"I want to create a parcel for Berger where route is Jaipur to Kolkata and size of parcel is 100kg and type of material like chemicals"</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Form */}
          <ParcelForm 
            onSubmit={handleSubmit} 
            isLoading={isLoading}
            cities={cities}
            materials={materials}
          />

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.98-.833-2.75 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <div>
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
              <div className="mt-4">
                <button
                  onClick={resetForm}
                  className="text-sm bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200 transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          )}

          {/* Result Display */}
          {result && (
            <ParcelResult 
              result={result} 
              onReset={resetForm}
              onClarifyingResponse={handleClarifyingResponse}
            />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            Powered by AI • Parcel Agent v1.0
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;