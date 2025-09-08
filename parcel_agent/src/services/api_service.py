import os
import base64
import httpx
import asyncio
import json
import urllib.parse
import logging
import traceback
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

# Configure logging for this module
logger = logging.getLogger(__name__)


class APIService:
    def __init__(self, auth_token=None):
        logger.info("API_SERVICE: Initializing APIService...")
        
        self.username = os.getenv("PARCEL_API_USERNAME")
        self.password = os.getenv("PARCEL_API_PASSWORD")
        self.auth_token = auth_token
        
        logger.info(f"   Username: {'[SET]' if self.username else '[MISSING]'}")
        logger.info(f"   Password: {'[SET]' if self.password else '[MISSING]'}")
        logger.info(f"   Auth token: {'[PROVIDED]' if auth_token else '[NOT_PROVIDED]'}")
        
        # API URLs
        self.cities_api_url = os.getenv("GET_CITIES_API_URL")
        self.materials_api_url = os.getenv("GET_MATERIALS_API_URL")
        self.companies_api_url = os.getenv("GET_COMPANIES_API_URL")
        self.parcels_api_url = os.getenv("PARCEL_API_URL")
        self.trips_api_url = os.getenv("TRIP_API_URL")
        
        logger.info(f"   Cities API: {'[SET]' if self.cities_api_url else '[MISSING]'}")
        logger.info(f"   Materials API: {'[SET]' if self.materials_api_url else '[MISSING]'}")
        logger.info(f"   Companies API: {'[SET]' if self.companies_api_url else '[MISSING]'}")
        logger.info(f"   Parcels API: {'[SET]' if self.parcels_api_url else '[MISSING]'}")
        logger.info(f"   Trips API: {'[SET]' if self.trips_api_url else '[MISSING]'}")
        
        # Static IDs from env
        self.created_by_id = os.getenv("CREATED_BY_ID")
        self.trip_id = os.getenv("TRIP_ID")
        self.created_by_company_id = os.getenv("CREATED_BY_COMPANY_ID")
        self.default_company_id = os.getenv("DEFAULT_COMPANY_ID")
        self.default_material_id = os.getenv("DEFAULT_MATERIAL_ID")
        
        logger.info(f"   Created By ID: {'[SET]' if self.created_by_id else '[MISSING]'}")
        logger.info(f"   Default Company ID: {'[SET]' if self.default_company_id else '[MISSING]'}")
        logger.info(f"   Default Material ID: {'[SET]' if self.default_material_id else '[MISSING]'}")
        
        # Cache for API responses
        self.cities_cache = {}
        self.materials_cache = {}
        self.companies_cache = {}
        
        logger.info("API_SERVICE: APIService initialization completed")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Generate Auth headers - prioritize token over Basic Auth"""
        if self.auth_token:
            # If auth_token is provided, use it directly
            return {
                "Authorization": self.auth_token,
                "Content-Type": "application/json"
            }
        else:
            # Fallback to Basic Auth
            credentials = f"{self.username}:{self.password}"
            credentials_b64 = base64.b64encode(credentials.encode()).decode()
            return {
                "Authorization": f"Basic {credentials_b64}",
                "Content-Type": "application/json"
            }
    
    async def test_login(self, username: str, password: str) -> bool:
        """Test login credentials with the API"""
        try:
            if not self.cities_api_url:
                return False
                
            # Create Basic Auth header for testing
            credentials = f"{username}:{password}"
            credentials_b64 = base64.b64encode(credentials.encode()).decode()
            headers = {
                "Authorization": f"Basic {credentials_b64}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(verify=False, timeout=10) as client:
                # Test with a simple API call (cities endpoint)
                response = await client.get(
                    self.cities_api_url + "?search=test",
                    headers=headers
                )
                
                # If we get a 401, credentials are wrong
                if response.status_code == 401:
                    return False
                    
                # If we get 200 or other non-auth error, credentials are likely correct
                return response.status_code != 401
                
        except Exception as e:
            print(f"Login test error: {e}")
            return False
    
    async def fetch_cities(self) -> Dict[str, str]:
        """Fetch cities from API and return name -> id mapping"""
        logger.info("CITIES_API: Fetching cities from API...")
        
        if self.cities_cache:
            logger.info(f"   CACHE: Using cached cities: {len(self.cities_cache)} items")
            return self.cities_cache
        
        if not self.cities_api_url:
            logger.error("   ERROR: Cities API URL not configured")
            return {}
            
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = self.get_auth_headers()
            logger.info(f"   HTTP: Making request to: {self.cities_api_url}")
            logger.debug(f"   AUTH: Headers: {headers}")
            
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(self.cities_api_url, headers=headers)
                logger.info(f"   HTTP: Response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"   ERROR: API request failed: {response.status_code} - {response.text[:200]}")
                    response.raise_for_status()
                
                cities_data = response.json()
                data_type = type(cities_data).__name__
                data_length = len(cities_data) if isinstance(cities_data, (list, dict)) else 'N/A'
                logger.info(f"   DATA: Received {data_length} cities from API (type: {data_type})")
                logger.debug(f"   DATA: First few cities: {str(cities_data)[:200]}...")
                
                # Handle different response formats
                if isinstance(cities_data, list):
                    for city in cities_data:
                        # Use "name" field as you specified
                        city_name = city.get('name', '').strip()
                        city_id = city.get('id') or city.get('_id', '')
                        
                        if city_name and city_id:
                            # Clean the city name (remove extra spaces)
                            clean_city_name = city_name.lower().strip()
                            self.cities_cache[clean_city_name] = str(city_id)
                            print(f"   Cached: {city_name} -> {city_id}")
                elif isinstance(cities_data, dict):
                    # Handle dict response format
                    for key, value in cities_data.items():
                        if isinstance(value, dict):
                            city_name = value.get('name') or key
                            city_id = value.get('id') or value.get('_id', key)
                            if city_name and city_id:
                                self.cities_cache[city_name.lower().strip()] = str(city_id)
                
                # Ensure minimum 5 second wait
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed < 5.0:
                    await asyncio.sleep(5.0 - elapsed)
                        
                print(f" Cities cached: {list(self.cities_cache.keys())}")
                return self.cities_cache
                
        except Exception as e:
            logger.error(f"   ERROR: Error fetching cities: {str(e)}")
            logger.error(f"   Stack trace: {traceback.format_exc()}")
            
            # Ensure minimum wait even on error
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining_wait = 5.0 - elapsed
            if remaining_wait > 0:
                logger.info(f"   WAIT: Waiting {remaining_wait:.1f}s to respect API timing...")
                await asyncio.sleep(remaining_wait)
            
            # Return fallback values
            fallback_cities = {
                "jaipur": "61b9dbed91248f261f80f824",
                "kolkata": "61f925c6a721cdc7bfde1435"
            }
            self.cities_cache.update(fallback_cities)
            logger.warning(f"   FALLBACK: Using fallback cities: {list(fallback_cities.keys())}")
            return self.cities_cache
    
    async def fetch_materials(self) -> Dict[str, str]:
        """Fetch materials from API and return name -> id mapping"""
        if self.materials_cache:
            return self.materials_cache
            
        print(" Fetching materials from API...")
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = self.get_auth_headers()
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(self.materials_api_url, headers=headers)
                response.raise_for_status()
                
                materials_data = response.json()
                print(f" Received {len(materials_data) if isinstance(materials_data, list) else 'N/A'} materials from API")
                
                # Handle different response formats
                if isinstance(materials_data, list):
                    for material in materials_data:
                        # Use "name" field as you specified
                        material_name = material.get('name', '').strip()
                        material_id = material.get('id') or material.get('_id', '')
                        
                        if material_name and material_id:
                            # Clean the material name (remove extra spaces)
                            clean_material_name = material_name.lower().strip()
                            self.materials_cache[clean_material_name] = str(material_id)
                            print(f"   Cached: {material_name} -> {material_id}")
                elif isinstance(materials_data, dict):
                    # Handle dict response format
                    for key, value in materials_data.items():
                        if isinstance(value, dict):
                            material_name = value.get('name') or key
                            material_id = value.get('id') or value.get('_id', key)
                            if material_name and material_id:
                                self.materials_cache[material_name.lower().strip()] = str(material_id)
                
                # Ensure minimum 5 second wait
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed < 5.0:
                    await asyncio.sleep(5.0 - elapsed)
                        
                print(f" Materials cached: {list(self.materials_cache.keys())}")
                return self.materials_cache
                
        except Exception as e:
            print(f" Error fetching materials: {e}")
            
            # Ensure minimum wait even on error
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed < 5.0:
                await asyncio.sleep(5.0 - elapsed)
            
            # Return fallback values
            fallback_materials = {
                "paint": "61547b0b988da3862e52daaa"
            }
            self.materials_cache.update(fallback_materials)
            return self.materials_cache
    
    async def fetch_companies(self) -> Dict[str, str]:
        """Fetch companies from API and return name -> id mapping"""
        if self.companies_cache:
            return self.companies_cache
            
        try:
            headers = self.get_auth_headers()
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                response = await client.get(self.companies_api_url, headers=headers)
                response.raise_for_status()
                
                companies_data = response.json()
                
                # Assuming API returns list of companies with 'name' and 'id' fields
                for company in companies_data:
                    company_name = company.get('name', '').lower()
                    company_id = company.get('id', '')
                    if company_name and company_id:
                        self.companies_cache[company_name] = company_id
                        
                return self.companies_cache
                
        except Exception as e:
            print(f"Error fetching companies: {e}")
            # Return empty dict - will use default company ID
            return {}
    
    async def get_city_id(self, city_name: str) -> Optional[str]:
        """Get city ID by name using direct API query with WHERE clause"""
        try:
            # First try to get from cache
            if city_name.lower() in self.cities_cache:
                return self.cities_cache[city_name.lower()]
            
            print(f" Searching for city: {city_name}")
            start_time = asyncio.get_event_loop().time()
            
            headers = self.get_auth_headers()
            
            # Use MongoDB-style WHERE clause for exact name matching
            # Create query for exact match: {"name": "Jaipur"}
            where_query = {
                "name": city_name.title()  # Try title case first (Jaipur)
            }
            
            # URL encode the JSON query
            where_param = urllib.parse.quote(json.dumps(where_query))
            
            # Build the full URL with the where parameter
            url_with_params = f"{self.cities_api_url}?where={where_param}"
            print(f" Query URL: {url_with_params}")
            
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(
                    url_with_params,
                    headers=headers
                )
                response.raise_for_status()
                
                cities_data = response.json()
                print(f" Received response for city '{city_name}': {cities_data}")
                
                # Handle response - API returns {"_items": [...], "_meta": {...}}
                city_id = None
                if isinstance(cities_data, dict) and "_items" in cities_data:
                    items = cities_data["_items"]
                    print(f" Found {len(items)} city items")
                    
                    # Look for exact name match
                    for city in items:
                        city_name_from_api = city.get('name', '').strip()
                        city_id_from_api = city.get('_id', '')
                        
                        print(f"   Checking: '{city_name_from_api}' vs '{city_name}'")
                        
                        # Exact match (case insensitive)
                        if city_name_from_api.lower() == city_name.lower():
                            city_id = city_id_from_api
                            # Cache the result
                            self.cities_cache[city_name_from_api.lower()] = str(city_id)
                            self.cities_cache[city_name.lower()] = str(city_id)
                            print(f" Exact match found: {city_name_from_api} -> ID: {city_id}")
                            break
                    
                    if not city_id and items:
                        print(f" No exact match found for '{city_name}'. Available cities:")
                        for city in items:
                            print(f"    - {city.get('name', '')}")
                
                # Ensure minimum 5 second wait
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed < 5.0:
                    await asyncio.sleep(5.0 - elapsed)
                
                return str(city_id) if city_id else None
                
        except Exception as e:
            print(f" Error searching for city '{city_name}': {e}")
            
            # Ensure minimum wait even on error
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed < 5.0:
                await asyncio.sleep(5.0 - elapsed)
            
            # Try fallback from full cities list
            cities = await self.fetch_cities()
            return cities.get(city_name.lower())
    
    async def get_material_id(self, material_name: str) -> Optional[str]:
        """Get material ID by name using direct API query with WHERE clause"""
        try:
            # First try to get from cache
            if material_name.lower() in self.materials_cache:
                return self.materials_cache[material_name.lower()]
            
            print(f" Searching for material: {material_name}")
            start_time = asyncio.get_event_loop().time()
            
            headers = self.get_auth_headers()
            
            # Use MongoDB-style WHERE clause exactly as provided in your example
            # Create query: {"$or": [{"name": {"$regex": "^materialname", "$options": "-i"}}]}
            where_query = {
                "$or": [
                    {
                        "name": {
                            "$regex": f"^{material_name}",
                            "$options": "-i"  # case insensitive with -i flag
                        }
                    }
                ]
            }
            
            # URL encode the JSON query
            where_param = urllib.parse.quote(json.dumps(where_query))
            
            # Build the full URL with the where parameter
            url_with_params = f"{self.materials_api_url}?where={where_param}"
            print(f" Query URL: {url_with_params}")
            
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(
                    url_with_params,
                    headers=headers
                )
                response.raise_for_status()
                
                materials_data = response.json()
                print(f" Received response for material '{material_name}': {materials_data}")
                
                # Handle response - API returns {"_items": [...], "_meta": {...}}
                material_id = None
                if isinstance(materials_data, dict) and "_items" in materials_data:
                    items = materials_data["_items"]
                    print(f" Found {len(items)} material items")
                    
                    # Look for exact name match
                    for material in items:
                        material_name_from_api = material.get('name', '').strip()
                        material_id_from_api = material.get('_id', '')
                        
                        print(f"   Checking: '{material_name_from_api}' vs '{material_name}'")
                        
                        # Exact match (case insensitive)
                        if material_name_from_api.lower() == material_name.lower():
                            material_id = material_id_from_api
                            # Cache the result
                            self.materials_cache[material_name_from_api.lower()] = str(material_id)
                            self.materials_cache[material_name.lower()] = str(material_id)
                            print(f" Exact match found: {material_name_from_api} -> ID: {material_id}")
                            break
                    
                    if not material_id and items:
                        print(f" No exact match found for '{material_name}'. Available materials:")
                        for material in items:
                            print(f"    - {material.get('name', '')}")
                
                # Ensure minimum 5 second wait
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed < 5.0:
                    await asyncio.sleep(5.0 - elapsed)
                
                return str(material_id) if material_id else self.default_material_id
                
        except Exception as e:
            print(f" Error searching for material '{material_name}': {e}")
            
            # Ensure minimum wait even on error
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed < 5.0:
                await asyncio.sleep(5.0 - elapsed)
            
            # Try fallback from full materials list
            materials = await self.fetch_materials()
            material_id = materials.get(material_name.lower())
            
            # If still not found, use default material ID
            if not material_id:
                material_id = self.default_material_id
                print(f" Using default material ID: {material_id}")
            
            return material_id
    
    async def get_company_id(self, company_name: str) -> Optional[str]:
        """Get company ID by name"""
        companies = await self.fetch_companies()
        company_id = companies.get(company_name.lower())
        
        # If not found, return default company ID
        if not company_id:
            company_id = self.default_company_id
            
        return company_id
    
    async def get_trip_by_route(self, from_city_id: str, to_city_id: str) -> str:
        """ALWAYS create trip first, then return trip ID for parcel creation"""
        logger.info(f"TRIP_REQUIRED: Must create/find trip FIRST from {from_city_id} to {to_city_id}")
        
        # STEP 1: Always try to create a trip first (this is the required order)
        if self.trips_api_url:
            logger.info("TRIP_CREATE: Creating trip FIRST as required by API...")
            try:
                trip_id = await self.create_trip_for_route(from_city_id, to_city_id)
                if trip_id:
                    logger.info(f"TRIP_SUCCESS: Trip created successfully: {trip_id}")
                    return trip_id
            except Exception as e:
                logger.error(f"TRIP_CREATE_FAILED: Failed to create trip: {str(e)}")
                
                # STEP 2: If creation failed, try to search for existing trips
                logger.info("TRIP_FALLBACK: Trip creation failed, searching for existing trips...")
                try:
                    search_url = f"{self.trips_api_url}?where={{\"pickup_postal_address.city\":\"{from_city_id}\",\"unload_postal_address.city\":\"{to_city_id}\"}}"
                    logger.info(f"   TRIP_SEARCH: {search_url}")
                    
                    headers = self.get_auth_headers()
                    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                        response = await client.get(search_url, headers=headers)
                        
                        if response.status_code == 200:
                            trips_data = response.json()
                            if trips_data.get('_items') and len(trips_data['_items']) > 0:
                                trip_id = trips_data['_items'][0].get('_id')
                                logger.info(f"   TRIP_FOUND: Using existing trip: {trip_id}")
                                return trip_id
                        
                except Exception as search_error:
                    logger.error(f"TRIP_SEARCH_FAILED: {str(search_error)}")
        
        # STEP 3: Final fallback to environment trip ID (with warning)
        if self.trip_id:
            logger.warning(f"TRIP_ENV_FALLBACK: Using environment trip ID: {self.trip_id}")
            logger.warning("TRIP_WARNING: This may fail if trip doesn't exist in database")
            return self.trip_id
        
        # STEP 4: No options left
        logger.error("TRIP_FATAL_ERROR: Cannot create, find, or use any trip ID")
        raise Exception("No valid trip ID available - API requires trip to exist before parcel creation")
    
    async def create_trip_for_route(self, from_city_id: str, to_city_id: str) -> str:
        """Create a new trip using the exact API payload format and extract _id"""
        logger.info(f"TRIP_API_CALL: Calling trips API - https://35.244.19.78:8042/trips")
        logger.info(f"TRIP_ROUTE: From {from_city_id} to {to_city_id}")
        
        # Use the hardcoded trips API URL as specified
        trips_api_url = "https://35.244.19.78:8042/trips"
        
        try:
            headers = self.get_auth_headers()
            
            # Use the exact payload format you specified
            trip_payload = {
                "specific_vehicle_requirements": {
                    "number_of_wheels": None,
                    "vehicle_body_type": None,
                    "axle_type": None,
                    "expected_price": None
                },
                "handled_by": "61421a01de5cb316d9ba4b16",
                "created_by": "6257f1d75b42235a2ae4ab34",
                "created_by_company": "62d66794e54f47829a886a1d"
            }
            
            logger.info(f"TRIP_PAYLOAD: Sending to {trips_api_url}")
            logger.info(f"TRIP_PAYLOAD: {json.dumps(trip_payload, indent=2)}")
            
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                logger.info("TRIP_HTTP: Making POST request to trip API...")
                response = await client.post(
                    trips_api_url,
                    json=trip_payload,
                    headers=headers
                )
                
                logger.info(f"TRIP_HTTP: Response status: {response.status_code}")
                logger.debug(f"TRIP_HTTP: Response headers: {dict(response.headers)}")
                
                if response.status_code in [200, 201]:
                    # Successfully created trip - now extract trip_id from response
                    result = response.json()
                    logger.info(f"TRIP_RESPONSE: {json.dumps(result, indent=2)}")
                    
                    # Extract trip_id from the API response dynamically
                    trip_id = None
                    if isinstance(result, dict):
                        # Try common field names for trip ID
                        trip_id = result.get('_id') or result.get('id') or result.get('trip_id')
                        
                        if not trip_id:
                            # Log available fields to help debug
                            available_fields = list(result.keys())
                            logger.warning(f"TRIP_ID_EXTRACT: trip_id not found in response fields: {available_fields}")
                            
                            # Try to find any field that might contain the trip ID
                            for field, value in result.items():
                                if 'id' in field.lower() and isinstance(value, str) and len(value) > 10:
                                    trip_id = value
                                    logger.info(f"TRIP_ID_EXTRACT: Using field '{field}' as trip_id: {trip_id}")
                                    break
                    
                    if trip_id:
                        logger.info(f"TRIP_SUCCESS: Dynamically extracted trip_id: {trip_id}")
                        return trip_id
                    else:
                        logger.error(f"TRIP_ID_ERROR: Could not extract trip_id from response: {result}")
                        raise Exception(f"Trip created but could not extract trip_id from response: {result}")
                        
                else:
                    logger.error(f"TRIP_API_ERROR: Trip API failed with status: {response.status_code}")
                    logger.error(f"TRIP_API_ERROR: Response body: {response.text}")
                    raise Exception(f"Trip API request failed with status {response.status_code}: {response.text}")
                        
        except httpx.HTTPStatusError as e:
            logger.error(f"TRIP_HTTP_ERROR: HTTP error calling trip API: {e.response.status_code}")
            logger.error(f"TRIP_HTTP_ERROR: Error response: {e.response.text}")
            raise Exception(f"Trip API HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"TRIP_ERROR: Error calling trip API: {str(e)}")
            logger.error(f"TRIP_ERROR: Stack trace: {traceback.format_exc()}")
            raise Exception(f"Failed to create trip: {str(e)}")
    
    async def create_parcel(self, parcel_payload: Dict) -> Dict:
        """Create parcel using the parcels API"""
        logger.info("PARCEL_API: Creating parcel via API...")
        logger.info(f"   URL: API URL: {self.parcels_api_url}")
        logger.info(f"   PAYLOAD: {json.dumps(parcel_payload, indent=2)}")
        
        try:
            if not self.parcels_api_url:
                logger.error("   ERROR: Parcels API URL not configured")
                raise Exception("Parcels API URL not configured")
            
            headers = self.get_auth_headers()
            logger.debug(f"   AUTH: Headers: {headers}")
            
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                logger.info("   HTTP: Sending POST request to parcels API...")
                response = await client.post(
                    self.parcels_api_url,
                    json=parcel_payload,
                    headers=headers
                )
                
                logger.info(f"   HTTP: Response status: {response.status_code}")
                logger.debug(f"   HTTP: Response headers: {dict(response.headers)}")
                
                if response.status_code != 200:
                    logger.error(f"   ERROR: API request failed: {response.status_code}")
                    logger.error(f"   ERROR: Response body: {response.text}")
                    response.raise_for_status()
                
                result = response.json()
                logger.info(f"   SUCCESS: Parcel created successfully")
                logger.info(f"   RESPONSE: {json.dumps(result, indent=2)}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"   HTTP_ERROR: HTTP error creating parcel: {e.response.status_code}")
            logger.error(f"   HTTP_ERROR: Error response: {e.response.text}")
            raise Exception(f"API request failed with status {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"   ERROR: Error creating parcel: {str(e)}")
            logger.error(f"   Stack trace: {traceback.format_exc()}")
            raise Exception(f"Error creating parcel: {str(e)}")
    
    async def create_trip(self) -> str:
        """Create a trip using the trips API without requiring city IDs"""
        logger.info("TRIP_API: Creating trip via API...")
        
        # Use the hardcoded trips API URL as specified
        trips_api_url = "https://35.244.19.78:8042/trips"
        
        try:
            headers = self.get_auth_headers()
            
            # Use the exact payload format as specified
            trip_payload = {
                "specific_vehicle_requirements": {
                    "number_of_wheels": None,
                    "vehicle_body_type": None,
                    "axle_type": None,
                    "expected_price": None
                },
                "handled_by": "61421a01de5cb316d9ba4b16",
                "created_by": "6257f1d75b42235a2ae4ab34",
                "created_by_company": "62d66794e54f47829a886a1d"
            }
            
            logger.info(f"TRIP_PAYLOAD: Sending to {trips_api_url}")
            logger.info(f"TRIP_PAYLOAD: {json.dumps(trip_payload, indent=2)}")
            
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                logger.info("TRIP_HTTP: Making POST request to trip API...")
                response = await client.post(
                    trips_api_url,
                    json=trip_payload,
                    headers=headers
                )
                
                logger.info(f"TRIP_HTTP: Response status: {response.status_code}")
                logger.debug(f"TRIP_HTTP: Response headers: {dict(response.headers)}")
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"TRIP_RESPONSE: {json.dumps(result, indent=2)}")
                    
                    # Extract _id from the response
                    trip_id = result.get('_id')
                    if trip_id:
                        logger.info(f"TRIP_SUCCESS: Trip created with ID: {trip_id}")
                        return trip_id
                    else:
                        logger.error(f"TRIP_ID_ERROR: Could not extract _id from response: {result}")
                        raise Exception(f"Trip created but could not extract _id from response")
                        
                else:
                    logger.error(f"TRIP_API_ERROR: Trip API failed with status: {response.status_code}")
                    logger.error(f"TRIP_API_ERROR: Response body: {response.text}")
                    raise Exception(f"Trip API request failed with status {response.status_code}: {response.text}")
                        
        except httpx.HTTPStatusError as e:
            logger.error(f"TRIP_HTTP_ERROR: HTTP error calling trip API: {e.response.status_code}")
            logger.error(f"TRIP_HTTP_ERROR: Error response: {e.response.text}")
            raise Exception(f"Trip API HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"TRIP_ERROR: Error calling trip API: {str(e)}")
            logger.error(f"TRIP_ERROR: Stack trace: {traceback.format_exc()}")
            raise Exception(f"Failed to create trip: {str(e)}")
    
    async def create_parcel_with_trip(self, parcel_info: Dict, trip_id: str) -> Dict:
        """Create parcel using the parcels API with a specific trip_id"""
        logger.info(f"PARCEL_WITH_TRIP: Creating parcel with trip ID: {trip_id}")
        
        # Use the hardcoded parcels API URL as specified  
        parcels_api_url = "https://35.244.19.78:8042/parcels"
        
        try:
            headers = self.get_auth_headers()
            
            # Build parcel payload using dynamic data from parcel_info
            parcel_payload = {
                "material_type": parcel_info.get('material_id', "619c925ee86624fb2a8f410e"),
                "quantity": parcel_info.get('weight', 22),
                "quantity_unit": "TONNES",
                "description": parcel_info.get('description'),
                "cost": parcel_info.get('weight', 22),
                "part_load": False,
                "pickup_postal_address": {
                    "address_line_1": parcel_info.get('pickup_address', "Default pickup address"),
                    "address_line_2": None,
                    "pin": parcel_info.get('pickup_pin', "490026"),
                    "city": parcel_info.get('from_city_id', "61421aa4de5cb316d9ba569e"),
                    "no_entry_zone": None
                },
                "unload_postal_address": {
                    "address_line_1": parcel_info.get('delivery_address', "Default delivery address"),
                    "address_line_2": None,
                    "pin": parcel_info.get('delivery_pin', "302013"),
                    "city": parcel_info.get('to_city_id', "61421aa1de5cb316d9ba55c0"),
                    "no_entry_zone": None
                },
                "sender": {
                    "sender_person": "652eda4a8e7383db25404c9d",
                    "sender_company": parcel_info.get('company_id', "66976a703eb59f3a8776b7ba"),
                    "name": parcel_info.get('company_name', "Default Company"),
                    "gstin": parcel_info.get('sender_gstin', "22AAACB7092E1Z1")
                },
                "receiver": {
                    "receiver_person": "64ca11882b28dbd864e9e8b6",
                    "receiver_company": "654160760e415d44ff3e93ff",
                    "name": parcel_info.get('receiver_name', "Default Receiver"),
                    "gstin": parcel_info.get('receiver_gstin', "08AABCR1634F1ZO")
                },
                "created_by": "6257f1d75b42235a2ae4ab34",
                "trip_id": trip_id,
                "verification": "Verified",
                "created_by_company": "62d66794e54f47829a886a1d"
            }
            logger.info(f"PARCEL_PAYLOAD: Sending to {parcels_api_url}")
            logger.info(f"PARCEL_PAYLOAD: {json.dumps(parcel_payload, indent=2)}")
            
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                logger.info("PARCEL_HTTP: Making POST request to parcels API...")
                response = await client.post(
                    parcels_api_url,
                    json=parcel_payload,
                    headers=headers
                )
                
                logger.info(f"PARCEL_HTTP: Response status: {response.status_code}")
                logger.debug(f"PARCEL_HTTP: Response headers: {dict(response.headers)}")
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"PARCEL_RESPONSE: {json.dumps(result, indent=2)}")
                    logger.info(f"PARCEL_SUCCESS: Parcel created successfully")
                    return result
                else:
                    logger.error(f"PARCEL_API_ERROR: Parcels API failed with status: {response.status_code}")
                    logger.error(f"PARCEL_API_ERROR: Response body: {response.text}")
                    raise Exception(f"Parcels API request failed with status {response.status_code}: {response.text}")
                        
        except httpx.HTTPStatusError as e:
            logger.error(f"PARCEL_HTTP_ERROR: HTTP error calling parcels API: {e.response.status_code}")
            logger.error(f"PARCEL_HTTP_ERROR: Error response: {e.response.text}")
            raise Exception(f"Parcels API HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"PARCEL_ERROR: Error calling parcels API: {str(e)}")
            logger.error(f"PARCEL_ERROR: Stack trace: {traceback.format_exc()}")
            raise Exception(f"Failed to create parcel: {str(e)}")
    
    async def initialize_cache(self):
        """Initialize all caches by fetching data from APIs"""
        logger.info("CACHE_INIT: Initializing API cache...")
        start_time = asyncio.get_event_loop().time()
        
        # Fetch all data sequentially to respect timing requirements
        try:
            logger.info("   FETCH: Fetching cities...")
            await self.fetch_cities()
            
            logger.info("   FETCH: Fetching materials...")
            await self.fetch_materials() 
            
            if self.companies_api_url and self.companies_api_url != "your_get_companies_api_url_here":
                logger.info("   FETCH: Fetching companies...")
                await self.fetch_companies()
            else:
                logger.info("   SKIP: Skipping companies fetch (URL not configured)")
                
        except Exception as e:
            logger.warning(f"   WARNING: Some API calls failed: {str(e)}")
            logger.error(f"   Stack trace: {traceback.format_exc()}")
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"CACHE_COMPLETE: Cache initialized in {elapsed:.1f} seconds:")
        logger.info(f"   - Cities: {len(self.cities_cache)} items")
        logger.info(f"   - Materials: {len(self.materials_cache)} items")
        logger.info(f"   - Companies: {len(self.companies_cache)} items")
