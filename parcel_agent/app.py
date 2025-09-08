#!/usr/bin/env python3
"""
Parcel Agent - FastAPI Backend with React Frontend
"""

import os
import asyncio
import logging
import traceback
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional
from src.agents.parcel_agent import ParcelAgent
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('parcel_agent.log', mode='a', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Parcel Agent API", version="1.0.0")

# Request/Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    # Log incoming request
    logger.info(f"REQUEST: {request.method} {request.url}")
    logger.info(f"   Headers: {dict(request.headers)}")
    
    # Get request body for POST/PUT requests
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                logger.info(f"   Body: {body.decode()[:500]}...")  # Limit body size in logs
        except Exception as e:
            logger.warning(f"   Could not read request body: {e}")
        
        # Reset body for processing
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    
    response = await call_next(request)
    
    # Log response
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"RESPONSE: {request.method} {request.url} - Status: {response.status_code} - Duration: {duration:.3f}s")
    
    return response

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
    logger.info("STARTUP: Starting Parcel Agent API...")
    logger.info(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"   Gemini API Key: {'[SET]' if os.getenv('GEMINI_API_KEY') else '[MISSING]'}")
    logger.info(f"   Parcel API Username: {'[SET]' if os.getenv('PARCEL_API_USERNAME') else '[MISSING]'}")
    
    try:
        if not default_parcel_agent.api_service.cities_cache:
            logger.info("CACHE: Initializing API cache...")
            await default_parcel_agent.api_service.initialize_cache()
            logger.info("CACHE: API cache initialization completed")
        else:
            logger.info("CACHE: API cache already initialized")
    except Exception as e:
        logger.error(f"ERROR: Failed to initialize API cache: {str(e)}")
        logger.error(f"   Stack trace: {traceback.format_exc()}")
    
    logger.info("STARTUP: Parcel Agent API startup completed")

@app.get("/")
async def root():
    return {"message": "Parcel Agent API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Parcel Agent API"}

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login and get auth token"""
    logger.info(f"LOGIN: Login attempt for username: {request.username}")
    
    try:
        # Create temporary agent to test login
        logger.info("   Creating temporary agent for login test...")
        temp_agent = ParcelAgent()
        
        # Test the credentials with API service
        logger.info("   Testing credentials with API service...")
        success = await temp_agent.api_service.test_login(request.username, request.password)
        
        if success:
            logger.info("LOGIN: Login successful - generating token")
            # For simplicity, we'll use base64 encoding of credentials as token
            import base64
            token = base64.b64encode(f"{request.username}:{request.password}".encode()).decode()
            
            return LoginResponse(
                success=True,
                message="Login successful",
                token=token
            )
        else:
            logger.warning("LOGIN: Login failed - invalid credentials")
            return LoginResponse(
                success=False,
                message="Invalid credentials"
            )
            
    except Exception as e:
        logger.error(f"LOGIN_ERROR: Login error: {str(e)}")
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return LoginResponse(
            success=False,
            message=f"Login failed: {str(e)}"
        )

@app.get("/api/debug/city/{city_name}")
async def debug_city_lookup(city_name: str):
    """Debug endpoint to test city lookup"""
    try:
        print(f"\\nDEBUG: Testing city lookup for '{city_name}'")
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
    logger.info(f"PARCEL: Creating parcel from message: {request.message[:100]}...")
    
    try:
        if not request.message or not request.message.strip():
            logger.error("PARCEL_ERROR: Empty message provided")
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"   Message length: {len(request.message)} characters")
        logger.info(f"   Auth token present: {'[YES]' if auth_token else '[NO]'}")
        
        # Use parcel agent with auth token
        if auth_token:
            logger.info("   Decoding auth token...")
            # Decode the token to get credentials
            import base64
            try:
                credentials = base64.b64decode(auth_token.encode()).decode()
                logger.info("   AUTH: Token decoded successfully")
                parcel_agent = ParcelAgent(auth_token=credentials)
            except Exception as e:
                logger.warning(f"   AUTH_WARNING: Token decode failed: {e}, using default agent")
                parcel_agent = ParcelAgent()
        else:
            logger.info("   Using default parcel agent (no auth)")
            parcel_agent = default_parcel_agent
        
        # Initialize cache if needed
        logger.info("   Checking API cache status...")
        if not parcel_agent.api_service.cities_cache:
            logger.info("   CACHE: Initializing API cache...")
            await parcel_agent.api_service.initialize_cache()
            logger.info("   CACHE: Cache initialized")
        else:
            logger.info("   CACHE: Cache already available")
        
        # Process the message with our agent
        logger.info("   AI: Processing message with AI agent...")
        result = await parcel_agent.process_message(request.message.strip())
        logger.info(f"   AI: Processing result: {result[:150]}...")
        
        # Extract parcel info for response
        logger.info("   EXTRACT: Extracting parcel information...")
        parcel_info = parcel_agent.extract_parcel_info(request.message.strip())
        logger.info(f"   EXTRACT: Extracted info: {parcel_info}")
        
        # Determine success based on result content - if successful, create trip and parcel
        is_success = not result.startswith("?") and not result.startswith("Error")
        logger.info(f"   RESULT: Parcel creation {'successful' if is_success else 'needs clarification/failed'}")
        
        if is_success and parcel_info:
            logger.info("   TRIP: Creating trip first...")
            # First create a trip
            trip_id = await parcel_agent.api_service.create_trip()
            logger.info(f"   TRIP: Trip created with ID: {trip_id}")
            
            if trip_id:
                logger.info("   PARCEL: Creating parcel with trip ID...")
                # Then create the parcel with the trip_id
                parcel_result = await parcel_agent.api_service.create_parcel_with_trip(parcel_info, trip_id)
                logger.info(f"   PARCEL: Parcel creation result: {parcel_result}")
                
                if parcel_result:
                    # Update the parcel_info with the actual creation results
                    parcel_info.update({
                        'trip_id': trip_id,
                        'parcel_id': parcel_result.get('_id'),
                        'created': parcel_result.get('_created'),
                        'status': 'created_successfully'
                    })
        
        return ParcelResponse(
            success=is_success,
            message=result,
            parcel_info=parcel_info
        )
        
    except HTTPException as e:
        logger.error(f"PARCEL_HTTP_ERROR: HTTP Exception: {e.detail}")
        raise e
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"PARCEL_ERROR: Unexpected error processing parcel request: {str(e)}")
        logger.error(f"   Full traceback: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing parcel request: {str(e)}"
        )

@app.post("/api/ask-question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest, auth_token: str = Depends(get_auth_token)):
    """
    Handle questions when data is missing or needs clarification
    """
    try:
        # Use parcel agent with auth token
        if auth_token:
            import base64
            try:
                credentials = base64.b64decode(auth_token.encode()).decode()
                parcel_agent = ParcelAgent(auth_token=credentials)
            except:
                parcel_agent = ParcelAgent()
        else:
            parcel_agent = default_parcel_agent
        
        question = request.question.strip().lower()
        context = request.context or {}
        
        # Handle different types of questions
        if "city" in question or "from" in question or "to" in question:
            # Try to find city from the question
            city_id = await parcel_agent.api_service.get_city_id(question)
            if city_id:
                return QuestionResponse(
                    success=True,
                    message=f"Found city: {question}",
                    data={"city": question, "city_id": city_id, "type": "city_found"}
                )
            else:
                return QuestionResponse(
                    success=False,
                    message="Could not find matching city. Please be more specific.",
                    needs_input=True,
                    question="Please provide the exact city name:"
                )
        
        elif "material" in question or "item" in question or "product" in question:
            # Try to find material from the question
            material_id = await parcel_agent.api_service.get_material_id(question)
            if material_id and material_id != parcel_agent.api_service.default_material_id:
                return QuestionResponse(
                    success=True,
                    message=f"Found material: {question}",
                    data={"material": question, "material_id": material_id, "type": "material_found"}
                )
            else:
                return QuestionResponse(
                    success=False,
                    message="Could not find matching material. Please be more specific.",
                    needs_input=True,
                    question="Please provide the exact material type:"
                )
        
        elif "weight" in question:
            return QuestionResponse(
                success=True,
                message="Please specify the weight",
                needs_input=True,
                question="What is the weight of the parcel (e.g., 5kg, 2.5kg)?"
            )
        
        else:
            # Generic question handling
            return QuestionResponse(
                success=True,
                message="Please provide more details",
                needs_input=True,
                question="Can you provide more specific information?"
            )
            
    except Exception as e:
        print(f"Error handling question: {e}")
        return QuestionResponse(
            success=False,
            message=f"Error processing question: {str(e)}"
        )

@app.get("/api/cities")
async def get_cities(auth_token: str = Depends(get_auth_token)):
    """Get available cities from the API"""
    logger.info("CITIES: Fetching available cities...")
    
    try:
        # Create agent with auth token for this request
        logger.info(f"   Auth token present: {'[YES]' if auth_token else '[NO]'}")
        
        if auth_token:
            import base64
            try:
                credentials = base64.b64decode(auth_token.encode()).decode()
                parcel_agent = ParcelAgent(auth_token=credentials)
                logger.info("   AUTH: Using authenticated agent")
            except Exception as e:
                logger.warning(f"   AUTH_WARNING: Token decode failed: {e}, using default")
                parcel_agent = ParcelAgent()
        else:
            parcel_agent = ParcelAgent()
            logger.info("   Using default agent")
        
        # Get first few characters from each available city
        logger.info("   API: Fetching cities from API...")
        cities_cache = await parcel_agent.api_service.fetch_cities()
        
        if cities_cache:
            logger.info(f"   CITIES: Found {len(cities_cache)} cities in cache")
            return {"cities": list(cities_cache.keys()), "count": len(cities_cache)}
        else:
            logger.warning("   CITIES_WARNING: No cities in cache, trying sample prefixes...")
            # Fetch sample cities by querying for common prefixes
            sample_cities = []
            prefixes = ['ja', 'ko', 'mu', 'de', 'ch', 'ba', 'pu', 'ah', 'su', 'ka']
            
            for prefix in prefixes:
                try:
                    logger.info(f"     Trying prefix: {prefix}")
                    city_id = await parcel_agent.api_service.get_city_id(prefix + "zzz")  # Non-existent suffix
                    if city_id:
                        sample_cities.append(prefix)
                        logger.info(f"     CITIES: Found match for {prefix}")
                except Exception as e:
                    logger.debug(f"     CITIES: No match for {prefix}: {e}")
                    continue
            
            logger.info(f"   CITIES: Returning {len(sample_cities)} sample cities")
            return {"cities": sample_cities if sample_cities else ["jaipur", "kolkata"], "note": "Sample cities - type to search"}
            
    except Exception as e:
        logger.error(f"CITIES_ERROR: Error fetching cities: {str(e)}")
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {"cities": ["jaipur", "kolkata"], "note": "Using fallback cities"}

@app.get("/api/materials") 
async def get_materials(auth_token: str = Depends(get_auth_token)):
    """Get available materials from the API"""
    try:
        # Create agent with auth token for this request
        if auth_token:
            import base64
            try:
                credentials = base64.b64decode(auth_token.encode()).decode()
                parcel_agent = ParcelAgent(auth_token=credentials)
            except:
                parcel_agent = ParcelAgent()
        else:
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
async def search_cities(q: str, auth_token: str = Depends(get_auth_token)):
    """Search for cities by query"""
    if not q or len(q) < 2:
        return {"cities": [], "message": "Query too short"}
    
    try:
        # Create agent with auth token for this request
        if auth_token:
            import base64
            try:
                credentials = base64.b64decode(auth_token.encode()).decode()
                parcel_agent = ParcelAgent(auth_token=credentials)
            except:
                parcel_agent = ParcelAgent()
        else:
            parcel_agent = ParcelAgent()
            
        city_id = await parcel_agent.api_service.get_city_id(q)
        if city_id:
            return {"cities": [q.lower()], "found": True}
        else:
            return {"cities": [], "found": False, "message": f"No cities found matching '{q}'"}
    except Exception as e:
        return {"cities": [], "error": str(e)}

@app.get("/api/search/materials")
async def search_materials(q: str, auth_token: str = Depends(get_auth_token)):
    """Search for materials by query"""
    if not q or len(q) < 2:
        return {"materials": [], "message": "Query too short"}
    
    try:
        # Create agent with auth token for this request
        if auth_token:
            import base64
            try:
                credentials = base64.b64decode(auth_token.encode()).decode()
                parcel_agent = ParcelAgent(auth_token=credentials)
            except:
                parcel_agent = ParcelAgent()
        else:
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