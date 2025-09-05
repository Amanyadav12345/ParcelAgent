#!/usr/bin/env python3
"""
Parcel Agent - FastAPI Backend with React Frontend
"""

import os
import asyncio
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional
from src.agents.parcel_agent import ParcelAgent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Parcel Agent API", version="1.0.0")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the parcel agent (will be recreated with auth token for each request)
default_parcel_agent = ParcelAgent()

class ParcelRequest(BaseModel):
    message: str

class ParcelResponse(BaseModel):
    success: bool
    message: str
    parcel_info: Dict[str, Any] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: str = None

class QuestionRequest(BaseModel):
    question: str
    context: Dict[str, Any] = None

class QuestionResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = None
    needs_input: bool = False
    question: str = None


def get_auth_token(authorization: Optional[str] = Header(None)):
    """Extract auth token from Authorization header"""
    if authorization and authorization.startswith('Bearer '):
        return authorization[7:]  # Remove 'Bearer ' prefix
    elif authorization:
        return authorization
    return None

@app.on_event("startup")
async def startup_event():
    """Initialize API cache on startup"""
    if not default_parcel_agent.api_service.cities_cache:
        await default_parcel_agent.api_service.initialize_cache()

@app.get("/")
async def root():
    return {"message": "Parcel Agent API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Parcel Agent API"}

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login and get auth token"""
    try:
        # Create temporary agent to test login
        temp_agent = ParcelAgent()
        
        # Test the credentials with API service
        success = await temp_agent.api_service.test_login(request.username, request.password)
        
        if success:
            # For simplicity, we'll use base64 encoding of credentials as token
            import base64
            token = base64.b64encode(f"{request.username}:{request.password}".encode()).decode()
            
            return LoginResponse(
                success=True,
                message="Login successful",
                token=token
            )
        else:
            return LoginResponse(
                success=False,
                message="Invalid credentials"
            )
            
    except Exception as e:
        print(f"Login error: {e}")
        return LoginResponse(
            success=False,
            message=f"Login failed: {str(e)}"
        )

@app.get("/api/debug/city/{city_name}")
async def debug_city_lookup(city_name: str):
    """Debug endpoint to test city lookup"""
    try:
        print(f"\nDEBUG: Testing city lookup for '{city_name}'")
        city_id = await default_parcel_agent.api_service.get_city_id(city_name)
        
        return {
            "query": city_name,
            "city_id": city_id,
            "found": bool(city_id),
            "cache": default_parcel_agent.api_service.cities_cache
        }
    except Exception as e:
        return {"error": str(e), "query": city_name}

@app.post("/api/create-parcel", response_model=ParcelResponse)
async def create_parcel(request: ParcelRequest, auth_token: str = Depends(get_auth_token)):
    """
    Create a parcel from natural language message
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        print(f"Received parcel request: {request.message}")
        
        # Use default parcel agent without auth token
        
        # Use parcel agent with auth token
        if auth_token:
            # Decode the token to get credentials
            import base64
            try:
                credentials = base64.b64decode(auth_token.encode()).decode()
                parcel_agent = ParcelAgent(auth_token=credentials)
            except:
                parcel_agent = ParcelAgent()
        else:
            parcel_agent = default_parcel_agent
        
        # Initialize cache if needed
        if not parcel_agent.api_service.cities_cache:
            await parcel_agent.api_service.initialize_cache()
        
        # Process the message with our agent
        result = await parcel_agent.process_message(request.message.strip())
        
        # Extract parcel info for response
        parcel_info = parcel_agent.extract_parcel_info(request.message.strip())
        
        return ParcelResponse(
            success=True,
            message=result,
            parcel_info=parcel_info
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing parcel request: {str(e)}")
        print(f"Full traceback: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing parcel request: {str(e)}"
        )

@app.get("/api/cities")
async def get_cities():
    """Get available cities from the API"""
    try:
        # Create agent without auth token for localhost
        parcel_agent = ParcelAgent()
        
        # Get first few characters from each available city
        cities_cache = await parcel_agent.api_service.fetch_cities()
        if cities_cache:
            return {"cities": list(cities_cache.keys()), "count": len(cities_cache)}
        else:
            # Fetch sample cities by querying for common prefixes
            sample_cities = []
            prefixes = ['ja', 'ko', 'mu', 'de', 'ch', 'ba', 'pu', 'ah', 'su', 'ka']
            
            for prefix in prefixes:
                try:
                    # Use the same method as get_city_id but with different prefixes
                    city_id = await parcel_agent.api_service.get_city_id(prefix + "zzz")  # Non-existent suffix
                    if city_id:
                        sample_cities.append(prefix)
                except:
                    continue
            
            return {"cities": sample_cities if sample_cities else ["jaipur", "kolkata"], "note": "Sample cities - type to search"}
    except Exception as e:
        print(f"Error fetching cities: {e}")
        return {"cities": ["jaipur", "kolkata"], "note": "Using fallback cities"}

@app.get("/api/materials") 
async def get_materials():
    """Get available materials from the API"""
    try:
        # Create agent without auth token for localhost
        parcel_agent = ParcelAgent()
        
        # Get first few characters from each available material
        materials_cache = await parcel_agent.api_service.fetch_materials()
        if materials_cache:
            return {"materials": list(materials_cache.keys()), "count": len(materials_cache)}
        else:
            # Fetch sample materials by querying for common prefixes
            sample_materials = []
            prefixes = ['pa', 'ch', 'el', 'fu', 'te', 'fo', 'ma', 'pl', 'me', 'wo']
            
            for prefix in prefixes:
                try:
                    # Use the same method as get_material_id but with different prefixes  
                    material_id = await parcel_agent.api_service.get_material_id(prefix + "zzz")  # Non-existent suffix
                    if material_id and material_id != parcel_agent.api_service.default_material_id:
                        sample_materials.append(prefix)
                except:
                    continue
                    
            return {"materials": sample_materials if sample_materials else ["paint", "chemicals"], "note": "Sample materials - type to search"}
    except Exception as e:
        print(f"Error fetching materials: {e}")
        return {"materials": ["paint", "chemicals"], "note": "Using fallback materials"}

@app.get("/api/search/cities")
async def search_cities(q: str):
    """Search for cities by query"""
    if not q or len(q) < 2:
        return {"cities": [], "message": "Query too short"}
    
    try:
        # Create agent without auth token for localhost
        parcel_agent = ParcelAgent()
        city_id = await parcel_agent.api_service.get_city_id(q)
        if city_id:
            return {"cities": [q.lower()], "found": True}
        else:
            return {"cities": [], "found": False, "message": f"No cities found matching '{q}'"}
    except Exception as e:
        return {"cities": [], "error": str(e)}

@app.get("/api/search/materials")
async def search_materials(q: str):
    """Search for materials by query"""
    if not q or len(q) < 2:
        return {"materials": [], "message": "Query too short"}
    
    try:
        # Create agent without auth token for localhost
        parcel_agent = ParcelAgent()
        material_id = await parcel_agent.api_service.get_material_id(q)
        if material_id and material_id != parcel_agent.api_service.default_material_id:
            return {"materials": [q.lower()], "found": True}
        else:
            return {"materials": [], "found": False, "message": f"No materials found matching '{q}'"}
    except Exception as e:
        return {"materials": [], "error": str(e)}

# Serve React build files (for production)
if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
    app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    print("Starting Parcel Agent API Server...")
    print("React frontend will be available at: http://localhost:8000")
    print("API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )