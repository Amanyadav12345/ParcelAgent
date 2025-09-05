# Parcel Agent - React UI with FastAPI Backend

A modern AI-powered parcel creation system with React frontend and FastAPI backend, using CrewAI, Gemini AI, and direct API integration.

## Features

- 🎨 **Modern React UI**: Clean, responsive interface with Tailwind CSS
- ⚡ **FastAPI Backend**: High-performance async API server
- 🤖 **CrewAI Agent**: Intelligent parcel processing agent
- 🧠 **Gemini AI**: Google's Gemini for natural language understanding
- 🚚 **Direct API Integration**: Real-time parcel service API integration
- 📱 **Dual Input Modes**: Natural language or structured form input

## Architecture

```
React Frontend ↔ FastAPI Backend ↔ Gemini AI ↔ CrewAI Agent ↔ Parcel API
```

## Setup

### Backend Setup

1. **Install Python dependencies:**
```bash
cd parcel_agent
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Required API Keys:**
- `GEMINI_API_KEY`: Get from Google AI Studio
- `PARCEL_API_USERNAME/PASSWORD`: Your parcel service credentials
- API endpoints for cities, materials, and parcel creation

### Frontend Setup

1. **Install Node.js dependencies:**
```bash
cd frontend
npm install
```

## Usage

### Development Mode (Recommended)
Start both backend and frontend with hot reload:
```bash
python main.py dev
```
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### Production Mode
1. **Build the React frontend:**
```bash
cd frontend
npm run build
```

2. **Start the server:**
```bash
python app.py
```
- Application: http://localhost:8000

### Using the Application

1. **Open your browser** and navigate to the application
2. **Choose input method:**
   - **Natural Language**: Type your parcel request in plain English
   - **Quick Form**: Use the structured form with dropdowns
3. **Example natural language input:**
   ```
   "Create a parcel for ABC Company from Jaipur to Kolkata, 50kg paint"
   ```
4. **The system will:**
   - Parse your request with Gemini AI
   - Extract structured parcel details
   - Look up city/material IDs from APIs
   - Create the parcel via API
   - Display confirmation with tracking details

## Project Structure

```
parcel_agent/
├── app.py                     # FastAPI backend server
├── main.py                    # Entry point & dev server
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── src/
│   ├── agents/
│   │   └── parcel_agent.py    # AI agent with Gemini integration
│   ├── services/
│   │   └── api_service.py     # API integration service
│   └── parsers/
│       └── message_parser.py   # Message parsing utilities
├── frontend/                  # React frontend
│   ├── package.json          # Node.js dependencies
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   ├── components/
│   │   │   ├── ParcelForm.js  # Parcel creation form
│   │   │   └── ParcelResult.js # Result display
│   │   └── index.js          # React entry point
│   └── public/
└── mcp_server/
    └── parcel_mcp.py         # MCP server (legacy)
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/create-parcel` - Create parcel from natural language
- `GET /api/cities` - Get available cities
- `GET /api/materials` - Get available materials
- `GET /docs` - Interactive API documentation

## Supported Cities & Materials

**Cities:** Dynamic from API (fallback: Jaipur, Kolkata)  
**Materials:** Dynamic from API (fallback: Paint, Chemicals)

## Example Usage

### Natural Language Examples
- "Create a parcel for ABC Company from Jaipur to Kolkata, 50kg paint"
- "I want to create a parcel for Berger where route is Jaipur to Kolkata and size of parcel is 100kg and type of material like chemicals"
- "Make a parcel for XYZ Corp, route Kolkata to Jaipur, 25kg paint"

### Quick Form
Use the toggle in the UI to switch to structured form input with dropdowns for cities, materials, and other fields.