import os
import base64
import httpx
import asyncio
import json
import urllib.parse
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()


class APIService:
    def __init__(self):
        self.username = os.getenv("PARCEL_API_USERNAME")
        self.password = os.getenv("PARCEL_API_PASSWORD")
        
        # API URLs
        self.cities_api_url = os.getenv("GET_CITIES_API_URL")
        self.materials_api_url = os.getenv("GET_MATERIALS_API_URL")
        self.companies_api_url = os.getenv("GET_COMPANIES_API_URL")
        self.parcels_api_url = os.getenv("PARCEL_API_URL")
        
        # Static IDs from env
        self.created_by_id = os.getenv("CREATED_BY_ID")
        self.trip_id = os.getenv("TRIP_ID")
        self.created_by_company_id = os.getenv("CREATED_BY_COMPANY_ID")
        self.default_company_id = os.getenv("DEFAULT_COMPANY_ID")
        self.default_material_id = os.getenv("DEFAULT_MATERIAL_ID")
        
        # Cache for API responses
        self.cities_cache = {}
        self.materials_cache = {}
        self.companies_cache = {}
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Generate Basic Auth headers"""
        credentials = f"{self.username}:{self.password}"
        credentials_b64 = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {credentials_b64}",
            "Content-Type": "application/json"
        }
    
    async def fetch_cities(self) -> Dict[str, str]:
        """Fetch cities from API and return name -> id mapping"""
        if self.cities_cache:
            return self.cities_cache
            
        print("🏙️ Fetching cities from API...")
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = self.get_auth_headers()
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(self.cities_api_url, headers=headers)
                response.raise_for_status()
                
                cities_data = response.json()
                print(f"📊 Received {len(cities_data) if isinstance(cities_data, list) else 'N/A'} cities from API")
                
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
                            print(f"  ✓ Cached: {city_name} -> {city_id}")
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
                        
                print(f"✅ Cities cached: {list(self.cities_cache.keys())}")
                return self.cities_cache
                
        except Exception as e:
            print(f"❌ Error fetching cities: {e}")
            
            # Ensure minimum wait even on error
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed < 5.0:
                await asyncio.sleep(5.0 - elapsed)
            
            # Return fallback values
            fallback_cities = {
                "jaipur": "61b9dbed91248f261f80f824",
                "kolkata": "61f925c6a721cdc7bfde1435"
            }
            self.cities_cache.update(fallback_cities)
            return self.cities_cache
    
    async def fetch_materials(self) -> Dict[str, str]:
        """Fetch materials from API and return name -> id mapping"""
        if self.materials_cache:
            return self.materials_cache
            
        print("🎨 Fetching materials from API...")
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = self.get_auth_headers()
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(self.materials_api_url, headers=headers)
                response.raise_for_status()
                
                materials_data = response.json()
                print(f"📊 Received {len(materials_data) if isinstance(materials_data, list) else 'N/A'} materials from API")
                
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
                            print(f"  ✓ Cached: {material_name} -> {material_id}")
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
                        
                print(f"✅ Materials cached: {list(self.materials_cache.keys())}")
                return self.materials_cache
                
        except Exception as e:
            print(f"❌ Error fetching materials: {e}")
            
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
            
            print(f"🔍 Searching for city: {city_name}")
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
            print(f"🔗 Query URL: {url_with_params}")
            
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(
                    url_with_params,
                    headers=headers
                )
                response.raise_for_status()
                
                cities_data = response.json()
                print(f"📊 Received response for city '{city_name}': {cities_data}")
                
                # Handle response - API returns {"_items": [...], "_meta": {...}}
                city_id = None
                if isinstance(cities_data, dict) and "_items" in cities_data:
                    items = cities_data["_items"]
                    print(f"📋 Found {len(items)} city items")
                    
                    # Look for exact name match
                    for city in items:
                        city_name_from_api = city.get('name', '').strip()
                        city_id_from_api = city.get('_id', '')
                        
                        print(f"  🔍 Checking: '{city_name_from_api}' vs '{city_name}'")
                        
                        # Exact match (case insensitive)
                        if city_name_from_api.lower() == city_name.lower():
                            city_id = city_id_from_api
                            # Cache the result
                            self.cities_cache[city_name_from_api.lower()] = str(city_id)
                            self.cities_cache[city_name.lower()] = str(city_id)
                            print(f"✅ Exact match found: {city_name_from_api} -> ID: {city_id}")
                            break
                    
                    if not city_id and items:
                        print(f"⚠️ No exact match found for '{city_name}'. Available cities:")
                        for city in items:
                            print(f"    - {city.get('name', '')}")
                
                # Ensure minimum 5 second wait
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed < 5.0:
                    await asyncio.sleep(5.0 - elapsed)
                
                return str(city_id) if city_id else None
                
        except Exception as e:
            print(f"❌ Error searching for city '{city_name}': {e}")
            
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
            
            print(f"🔍 Searching for material: {material_name}")
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
            print(f"🔗 Query URL: {url_with_params}")
            
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(
                    url_with_params,
                    headers=headers
                )
                response.raise_for_status()
                
                materials_data = response.json()
                print(f"📊 Received response for material '{material_name}': {materials_data}")
                
                # Handle response - API returns {"_items": [...], "_meta": {...}}
                material_id = None
                if isinstance(materials_data, dict) and "_items" in materials_data:
                    items = materials_data["_items"]
                    print(f"📋 Found {len(items)} material items")
                    
                    # Look for exact name match
                    for material in items:
                        material_name_from_api = material.get('name', '').strip()
                        material_id_from_api = material.get('_id', '')
                        
                        print(f"  🔍 Checking: '{material_name_from_api}' vs '{material_name}'")
                        
                        # Exact match (case insensitive)
                        if material_name_from_api.lower() == material_name.lower():
                            material_id = material_id_from_api
                            # Cache the result
                            self.materials_cache[material_name_from_api.lower()] = str(material_id)
                            self.materials_cache[material_name.lower()] = str(material_id)
                            print(f"✅ Exact match found: {material_name_from_api} -> ID: {material_id}")
                            break
                    
                    if not material_id and items:
                        print(f"⚠️ No exact match found for '{material_name}'. Available materials:")
                        for material in items:
                            print(f"    - {material.get('name', '')}")
                
                # Ensure minimum 5 second wait
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed < 5.0:
                    await asyncio.sleep(5.0 - elapsed)
                
                return str(material_id) if material_id else self.default_material_id
                
        except Exception as e:
            print(f"❌ Error searching for material '{material_name}': {e}")
            
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
                print(f"⚠️ Using default material ID: {material_id}")
            
            return material_id
    
    async def get_company_id(self, company_name: str) -> Optional[str]:
        """Get company ID by name"""
        companies = await self.fetch_companies()
        company_id = companies.get(company_name.lower())
        
        # If not found, return default company ID
        if not company_id:
            company_id = self.default_company_id
            
        return company_id
    
    async def create_parcel(self, parcel_payload: Dict) -> Dict:
        """Create parcel using the parcels API"""
        try:
            headers = self.get_auth_headers()
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                response = await client.post(
                    self.parcels_api_url,
                    json=parcel_payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise Exception(f"Error creating parcel: {str(e)}")
    
    async def initialize_cache(self):
        """Initialize all caches by fetching data from APIs"""
        print("🔄 Initializing API cache... This may take a moment...")
        start_time = asyncio.get_event_loop().time()
        
        # Fetch all data sequentially to respect timing requirements
        try:
            await self.fetch_cities()
            await self.fetch_materials() 
            if self.companies_api_url and self.companies_api_url != "your_get_companies_api_url_here":
                await self.fetch_companies()
        except Exception as e:
            print(f"⚠️ Some API calls failed: {e}")
        
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"✅ Cache initialized in {elapsed:.1f} seconds:")
        print(f"   - Cities: {len(self.cities_cache)} items")
        print(f"   - Materials: {len(self.materials_cache)} items")
        print(f"   - Companies: {len(self.companies_cache)} items")