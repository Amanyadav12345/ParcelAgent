#!/usr/bin/env python3
"""
Parcel Agent - FastAPI Backend with React Frontend
"""

import os
import sys
import subprocess

def main():
    """Main entry point"""
    try:
        # Check if .env file exists
        if not os.path.exists('.env'):
            print("Warning: .env file not found!")
            print("Please copy .env.example to .env and fill in your API keys:")
            print("- GEMINI_API_KEY") 
            print("- PARCEL_API credentials and URLs")
            return
        
        print("Starting Parcel Agent Server...")
        print("React frontend will be available at: http://localhost:8000")
        print("API docs available at: http://localhost:8000/docs")
        
        # Start the FastAPI server
        import app
        
    except KeyboardInterrupt:
        print("\nShutting down Parcel Agent Server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


def dev():
    """Development mode - start both backend and frontend"""
    print("Starting Parcel Agent in Development Mode...")
    
    # Start backend
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "app:app",
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ])
    
    # Start frontend (if available)
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    if os.path.exists(frontend_dir):
        print("Starting React frontend...")
        try:
            frontend_process = subprocess.Popen([
                "npm", "start"
            ], cwd=frontend_dir)
        except (FileNotFoundError, OSError):
            print("Warning: npm not found. Frontend will not start automatically.")
            print("To start frontend manually: cd frontend && npm start")
            frontend_process = None
    
    try:
        # Wait for processes
        backend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down development servers...")
        backend_process.terminate()
        if 'frontend_process' in locals() and frontend_process is not None:
            frontend_process.terminate()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        dev()
    else:
        main()