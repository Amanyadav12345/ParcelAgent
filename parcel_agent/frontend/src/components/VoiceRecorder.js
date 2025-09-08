import React, { useState, useEffect, useRef } from 'react';

const VoiceRecorder = ({ onTranscriptionComplete, disabled = false }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState('');
  const [isSupported, setIsSupported] = useState(true);
  const recognitionRef = useRef(null);
  const silenceTimeoutRef = useRef(null);

  useEffect(() => {
    // Check if Speech Recognition is supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setIsSupported(false);
      setError('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    // Initialize Speech Recognition
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;
    
    // Enhanced settings for better long-form speech recognition
    if (recognition.serviceURI) {
      recognition.serviceURI = 'wss://api.wit.ai/speech'; // Fallback if needed
    }

    recognition.onstart = () => {
      setIsRecording(true);
      setError('');
    };

    recognition.onresult = (event) => {
      let newFinalTranscript = '';
      let newInterimTranscript = '';

      // Process all results from the recognition event
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const currentTranscript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          newFinalTranscript += currentTranscript;
        } else {
          newInterimTranscript += currentTranscript;
        }
      }

      // Update state with cumulative transcripts
      setFinalTranscript(prev => prev + newFinalTranscript);
      setInterimTranscript(newInterimTranscript);
      
      // Update the combined transcript for display
      const combinedTranscript = (finalTranscript + newFinalTranscript + newInterimTranscript).trim();
      setTranscript(combinedTranscript);

      // Clear any existing silence timeout and set a new one
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      
      // Auto-restart recognition if it stops unexpectedly during long speech
      silenceTimeoutRef.current = setTimeout(() => {
        if (isRecording && recognitionRef.current) {
          try {
            recognitionRef.current.start();
          } catch (e) {
            // Recognition might already be running
            console.log('Recognition restart attempted:', e.message);
          }
        }
      }, 3000); // Wait 3 seconds of silence before potential restart
    };

    recognition.onerror = (event) => {
      setError(`Speech recognition error: ${event.error}`);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
      
      // Clear any pending silence timeout
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
      
      // Send the complete final transcript to parent component
      const completeTranscript = (finalTranscript + interimTranscript).trim();
      if (completeTranscript) {
        onTranscriptionComplete(completeTranscript);
        setTranscript(completeTranscript);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognition) {
        recognition.stop();
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
    };
  }, [onTranscriptionComplete]);

  const startRecording = () => {
    if (!isSupported || !recognitionRef.current) {
      return;
    }

    // Reset all transcript states for a fresh start
    setTranscript('');
    setFinalTranscript('');
    setInterimTranscript('');
    setError('');
    
    // Clear any existing timeout
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    
    try {
      recognitionRef.current.start();
    } catch (error) {
      setError('Failed to start recording. Please try again.');
      console.error('Recording start error:', error);
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
    }
  };

  if (!isSupported) {
    return (
      <div className="text-center p-4">
        <div className="text-red-600 text-sm">{error}</div>
      </div>
    );
  }

  return (
    <div className="voice-recorder">
      <div className="flex items-center space-x-3">
        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          disabled={disabled}
          className={`p-2 rounded-full transition-all duration-200 ${
            isRecording 
              ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse' 
              : 'bg-blue-500 text-white hover:bg-blue-600'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          title={isRecording ? 'Stop recording' : 'Start voice recording'}
        >
          {isRecording ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 6h12v12H6z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
            </svg>
          )}
        </button>
        
        <div className="flex-1">
          {isRecording && (
            <div className="flex items-center space-x-2">
              <div className="animate-pulse text-red-500 text-sm font-medium">Recording...</div>
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          )}
          
          {!isRecording && transcript && (
            <div className="text-sm text-gray-600">
              <strong>Last recording:</strong> {transcript.length > 150 ? transcript.substring(0, 150) + '...' : transcript}
            </div>
          )}
          
          {!isRecording && !transcript && (
            <div className="text-sm text-gray-500">
              Click the microphone to start recording
            </div>
          )}
        </div>
      </div>
      
      {error && (
        <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
          {error}
        </div>
      )}
      
      {transcript && (
        <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-sm font-medium text-blue-800 mb-2 flex items-center justify-between">
            <span>Live Transcription:</span>
            <span className="text-xs text-blue-600">
              {transcript.length} characters
            </span>
          </div>
          <div className="text-sm text-blue-900 max-h-32 overflow-y-auto leading-relaxed">
            {isRecording ? (
              <span>
                {finalTranscript}
                <span className="text-blue-600 bg-blue-100 px-1 rounded">
                  {interimTranscript}
                </span>
                <span className="animate-pulse">|</span>
              </span>
            ) : (
              transcript
            )}
          </div>
          {transcript.length > 200 && (
            <div className="mt-2 text-xs text-blue-600">
              💡 Long text detected - perfect for detailed parcel requests!
            </div>
          )}
          {!isRecording && transcript && (
            <div className="mt-3 flex justify-end">
              <button
                type="button"
                onClick={() => onTranscriptionComplete(transcript)}
                className="px-4 py-2 bg-blue-500 text-white text-sm font-medium rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 transition-colors duration-200 flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                <span>Send to Chat</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VoiceRecorder;