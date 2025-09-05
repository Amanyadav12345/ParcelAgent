import React, { useState } from 'react';
import VoiceRecorder from './VoiceRecorder';

const ParcelForm = ({ onSubmit, isLoading, cities, materials }) => {
  const [message, setMessage] = useState('');
  const [useQuickForm, setUseQuickForm] = useState(false);
  const [quickFormData, setQuickFormData] = useState({
    company: '',
    fromCity: '',
    toCity: '',
    weight: '',
    material: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (useQuickForm) {
      // Convert quick form data to natural language message
      const { company, fromCity, toCity, weight, material } = quickFormData;
      const generatedMessage = `Create a parcel for ${company} from ${fromCity} to ${toCity}, ${weight}kg ${material}`;
      onSubmit(generatedMessage);
    } else {
      if (message.trim()) {
        onSubmit(message.trim());
      }
    }
  };

  const handleQuickFormChange = (field, value) => {
    setQuickFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleVoiceTranscription = (transcript) => {
    setMessage(transcript);
  };

  const isFormValid = useQuickForm 
    ? Object.values(quickFormData).every(value => value.trim() !== '')
    : message.trim() !== '';

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Create Parcel</h2>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Quick Form</span>
            <button
              type="button"
              onClick={() => setUseQuickForm(!useQuickForm)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                useQuickForm ? 'bg-primary-500' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  useQuickForm ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {useQuickForm ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Name *
              </label>
              <input
                type="text"
                value={quickFormData.company}
                onChange={(e) => handleQuickFormChange('company', e.target.value)}
                className="form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="e.g., ABC Company"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                From City *
              </label>
              <select
                value={quickFormData.fromCity}
                onChange={(e) => handleQuickFormChange('fromCity', e.target.value)}
                className="form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                required
              >
                <option value="">Select city</option>
                {cities.map(city => (
                  <option key={city} value={city}>
                    {city.charAt(0).toUpperCase() + city.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                To City *
              </label>
              <select
                value={quickFormData.toCity}
                onChange={(e) => handleQuickFormChange('toCity', e.target.value)}
                className="form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                required
              >
                <option value="">Select city</option>
                {cities.map(city => (
                  <option key={city} value={city}>
                    {city.charAt(0).toUpperCase() + city.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Weight (kg) *
              </label>
              <input
                type="number"
                value={quickFormData.weight}
                onChange={(e) => handleQuickFormChange('weight', e.target.value)}
                className="form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="e.g., 100"
                min="1"
                required
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Material Type *
              </label>
              <select
                value={quickFormData.material}
                onChange={(e) => handleQuickFormChange('material', e.target.value)}
                className="form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                required
              >
                <option value="">Select material</option>
                {materials.map(material => (
                  <option key={material} value={material}>
                    {material.charAt(0).toUpperCase() + material.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        ) : (
          <div>
            <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
              Parcel Request Message *
            </label>
            <textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="form-input w-full px-3 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows={4}
              placeholder="Describe your parcel requirements in natural language..."
              required
            />
            <p className="text-xs text-gray-500 mt-2">
              Example: "Create a parcel for ABC Company from Jaipur to Kolkata, 50kg paint"
            </p>
            
            {/* Voice Recording Section */}
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center mb-3">
                <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
                </svg>
                <h3 className="text-sm font-medium text-gray-700">Voice Input</h3>
              </div>
              <VoiceRecorder 
                onTranscriptionComplete={handleVoiceTranscription}
                disabled={isLoading}
              />
            </div>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!isFormValid || isLoading}
            className="btn-primary bg-primary-500 text-white px-6 py-2 rounded-md font-medium hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isLoading ? (
              <>
                <svg className="loading-spinner w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Creating Parcel...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <span>Create Parcel</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ParcelForm;