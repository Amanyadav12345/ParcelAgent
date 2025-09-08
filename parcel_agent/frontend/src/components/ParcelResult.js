import React, { useState } from 'react';

const ParcelResult = ({ result, onReset, onClarifyingResponse }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [clarifyingInput, setClarifyingInput] = useState('');

  if (!result) return null;

  const { success, message, parcel_info } = result;
  
  // Check if this is a clarifying question (starts with ❓)
  const isClarifyingQuestion = message.startsWith('❓');
  
  const handleClarifyingSubmit = () => {
    if (clarifyingInput.trim() && onClarifyingResponse) {
      onClarifyingResponse(clarifyingInput.trim());
      setClarifyingInput('');
    }
  };
  
  // Parse the message to extract parcel ID and cost
  const parcelIdMatch = message.match(/Parcel ID: ([^\n]+)/);
  const costMatch = message.match(/Cost: ₹([0-9,]+)/);
  
  const parcelId = parcelIdMatch ? parcelIdMatch[1] : 'N/A';
  const cost = costMatch ? costMatch[1] : '29997';

  // Handle clarifying questions differently
  if (isClarifyingQuestion) {
    return (
      <div className="result-card bg-white rounded-lg shadow-sm border border-amber-200 p-6">
        <div className="flex items-start space-x-3 mb-4">
          <div className="flex-shrink-0">
            <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">More Information Needed</h3>
            <div className="bg-amber-50 rounded-lg p-4 mb-4">
              <div className="text-sm text-gray-700 whitespace-pre-wrap">{message}</div>
            </div>
            
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                Please provide the missing information:
              </label>
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={clarifyingInput}
                  onChange={(e) => setClarifyingInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleClarifyingSubmit()}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Type your response here..."
                />
                <button
                  onClick={handleClarifyingSubmit}
                  disabled={!clarifyingInput.trim()}
                  className="px-4 py-2 bg-blue-500 text-white font-medium rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Submit
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex justify-start pt-4 border-t border-gray-200">
          <button
            onClick={onReset}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
          >
            ← Start Over
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="result-card bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              success ? 'bg-green-100' : 'bg-red-100'
            }`}>
              {success ? (
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {success ? 'Parcel Created Successfully!' : 'Parcel Creation Failed'}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {success ? 'Your parcel has been processed and created.' : 'There was an error creating your parcel.'}
            </p>
          </div>
        </div>
        <button
          onClick={onReset}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          title="Create another parcel"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {success && parcel_info && (
        <div className="space-y-4">
          {/* Quick Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="text-sm font-medium text-blue-900">Route</span>
              </div>
              <p className="text-lg font-semibold text-blue-900 mt-1">
                {parcel_info.from_city?.charAt(0).toUpperCase() + parcel_info.from_city?.slice(1)} → {parcel_info.to_city?.charAt(0).toUpperCase() + parcel_info.to_city?.slice(1)}
              </p>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v0M8 5a2 2 0 012-2h4a2 2 0 012 2v0" />
                </svg>
                <span className="text-sm font-medium text-green-900">Parcel ID</span>
              </div>
              <p className="text-sm font-mono font-semibold text-green-900 mt-1 break-all">
                {parcelId}
              </p>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
                <span className="text-sm font-medium text-purple-900">Cost</span>
              </div>
              <p className="text-lg font-semibold text-purple-900 mt-1">
                ₹{cost}
              </p>
            </div>
          </div>

          {/* Detailed Information */}
          <div className="border-t border-gray-200 pt-4">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
            >
              <span>Parcel Details</span>
              <svg
                className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showDetails && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Parcel Information</h4>
                  <dl className="space-y-2">
                    <div>
                      <dt className="text-xs font-medium text-gray-500">Company</dt>
                      <dd className="text-sm text-gray-900">{parcel_info.company}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium text-gray-500">Weight</dt>
                      <dd className="text-sm text-gray-900">{parcel_info.weight}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium text-gray-500">Material</dt>
                      <dd className="text-sm text-gray-900 capitalize">{parcel_info.material}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Status</h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-sm text-gray-700">Parcel Created</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-sm text-gray-700">Verified</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                      <span className="text-sm text-gray-500">Awaiting Pickup</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* AI Response */}
          <div className="bg-gray-50 rounded-lg p-4 mt-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center space-x-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span>AI Response</span>
            </h4>
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{message}</pre>
          </div>
        </div>
      )}

      {!success && (
        <div className="bg-red-50 rounded-lg p-4">
          <p className="text-sm text-red-700">{message}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
        <button
          onClick={onReset}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
        >
          Create Another Parcel
        </button>
        {success && (
          <button
            onClick={() => window.print()}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-500 border border-transparent rounded-md hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          >
            Print Details
          </button>
        )}
      </div>
    </div>
  );
};

export default ParcelResult;