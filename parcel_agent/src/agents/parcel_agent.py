import os
import json
import re
import asyncio
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
from src.services.api_service import APIService

load_dotenv()


class ParcelAgent:
    def __init__(self, auth_token=None):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.api_service = APIService(auth_token=auth_token)
    
    def extract_parcel_info(self, message: str) -> Dict[str, Any]:
        """Use Gemini to extract structured information from message"""
        prompt = f"""
        Extract parcel information from this message: "{message}"
        
        Return ONLY a JSON object with these exact fields (no additional text):
        {{
            "company": "company name mentioned or 'Unknown'",
            "from_city": "origin city name",
            "to_city": "destination city name", 
            "weight": "weight with unit like '100kg'",
            "material": "material type mentioned",
            "price": "price/cost mentioned (number only) or null if not mentioned"
        }}
        
        Examples of cities: jaipur, kolkata, mumbai, delhi, chennai, bangalore
        Examples of materials: electronics, furniture, textiles, food items, chemicals, machinery
        
        IMPORTANT: 
        - Do NOT use "paint" as material type. Extract the actual material type mentioned.
        - For price, extract only the number if mentioned (e.g., "5000" from "cost is 5000 rupees")
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return self._fallback_parse(message)
        except Exception as e:
            print(f"Gemini extraction error: {e}")
            return self._fallback_parse(message)
    
    def _fallback_parse(self, message: str) -> Dict[str, Any]:
        """Fallback parsing using regex"""
        message_lower = message.lower()
        
        # Extract company
        company_match = re.search(r'for\s+(\w+)', message_lower)
        company = company_match.group(1) if company_match else "Unknown"
        
        # Extract route - look for "from X to Y" or "X to Y"
        route_patterns = [
            r'from\s+(\w+)\s+to\s+(\w+)',
            r'route\s+is\s+(\w+)\s+to\s+(\w+)',
            r'(\w+)\s+to\s+(\w+)'
        ]
        
        from_city, to_city = "jaipur", "kolkata"  # defaults
        for pattern in route_patterns:
            route_match = re.search(pattern, message_lower)
            if route_match:
                from_city = route_match.group(1)
                to_city = route_match.group(2)
                break
        
        # Extract weight
        weight_match = re.search(r'(\d+\w*)', message_lower)
        weight = weight_match.group(1) + "kg" if weight_match else "100kg"
        
        # Extract material
        material_patterns = [
            r'material\s+like\s+(\w+)',
            r'type\s+of\s+material\s+like\s+(\w+)',
            r'material\s+(\w+)',
        ]
        
        material = "chemicals"  # default - not "paint"
        for pattern in material_patterns:
            material_match = re.search(pattern, message_lower)
            if material_match:
                material = material_match.group(1)
                break
        
        # Extract price/cost
        price_patterns = [
            r'cost[\s:]+(?:rs\.?\s*|rupees?\s*)?([\d,]+)',
            r'price[\s:]+(?:rs\.?\s*|rupees?\s*)?([\d,]+)',
            r'(?:rs\.?\s*|rupees?\s*)([\d,]+)',
            r'([\d,]+)\s*(?:rs|rupees?)'
        ]
        
        price = None
        for pattern in price_patterns:
            price_match = re.search(pattern, message_lower)
            if price_match:
                price = int(price_match.group(1).replace(',', ''))
                break
        
        return {
            "company": company,
            "from_city": from_city,
            "to_city": to_city,
            "weight": weight,
            "material": material,
            "price": price
        }
    
    def get_dynamic_cost(self, parcel_info: Dict[str, Any], weight_kg: float) -> int:
        """Get dynamic cost based on user input or calculation"""
        # If price is explicitly mentioned, use it
        if parcel_info.get('price'):
            return int(parcel_info['price'])
        
        # Simple calculation based on weight and material
        base_cost = weight_kg * 150  # Rs 150 per kg
        
        # Material multiplier
        material_multipliers = {
            'electronics': 1.5,
            'chemicals': 2.0,
            'machinery': 1.8,
            'furniture': 1.2,
        }
        
        material = parcel_info.get('material', '').lower()
        multiplier = material_multipliers.get(material, 1.0)
        
        final_cost = int(base_cost * multiplier)
        return max(final_cost, 500)  # Minimum Rs 500
    
    async def create_parcel(self, parcel_info: Dict[str, Any]) -> str:
        """Create parcel using API service with dynamic ID fetching"""
        try:
            # Extract weight value
            weight_str = parcel_info.get("weight", "100kg")
            weight_value = float(re.search(r'(\d+)', weight_str).group(1))
            
            print(f"Looking up IDs for:")
            print(f"   - From: {parcel_info['from_city']}")
            print(f"   - To: {parcel_info['to_city']}")
            print(f"   - Material: {parcel_info['material']}")
            print(f"   - Company: {parcel_info['company']}")
            
            # Get IDs dynamically
            print("Fetching city information...")
            from_city_id = await self.api_service.get_city_id(parcel_info['from_city'])
            to_city_id = await self.api_service.get_city_id(parcel_info['to_city'])
            
            print("Fetching material information...")
            material_id = await self.api_service.get_material_id(parcel_info['material'])
            
            print("Fetching company information...")
            company_id = await self.api_service.get_company_id(parcel_info['company'])
            
            print(f"Found IDs:")
            print(f"   - From City: {from_city_id}")
            print(f"   - To City: {to_city_id}")
            print(f"   - Material: {material_id}")
            print(f"   - Company: {company_id}")
            
            # Verify required IDs are found
            missing_ids = []
            if not from_city_id:
                missing_ids.append(f"city '{parcel_info['from_city']}'")
            if not to_city_id:
                missing_ids.append(f"city '{parcel_info['to_city']}'")
            
            if missing_ids:
                return f"Error: Could not find IDs for: {', '.join(missing_ids)}.\nPlease check the spelling or contact support."
            
            # Material ID will always have a value (either found or default fallback)
            if not material_id:
                material_id = self.api_service.default_material_id
                print(f"Warning: No material found, using default: {material_id}")
            
            # Get or create trip for this route
            print("Managing trip for route...")
            trip_id = await self.api_service.get_trip_by_route(from_city_id, to_city_id)
            print(f"   - Trip ID: {trip_id}")
            
            # Calculate dynamic cost
            calculated_cost = self.get_dynamic_cost(parcel_info, weight_value)
            print(f"DEBUG: Parcel info extracted: {parcel_info}")
            print(f"DEBUG: Weight value: {weight_value}")
            print(f"DEBUG: Calculated cost: {calculated_cost}")
            
            # Create parcel payload
            payload = {
                "material_type": material_id,
                "quantity": weight_value,
                "quantity_unit": "KILOGRAMS", 
                "description": None,
                "cost": calculated_cost,
                "part_load": False,
                "pickup_postal_address": {
                    "address_line_1": None,
                    "address_line_2": None,
                    "pin": None,
                    "city": from_city_id,
                    "no_entry_zone": None
                },
                "unload_postal_address": {
                    "address_line_1": None,
                    "address_line_2": None,
                    "pin": None,
                    "city": to_city_id,
                    "no_entry_zone": None
                },
                "sender": {
                    "sender_person": None,
                    "sender_company": None,
                    "name": None,
                    "gstin": None
                },
                "receiver": {
                    "receiver_person": None,
                    "receiver_company": None,
                    "name": None,
                    "gstin": None
                },
                "created_by": self.api_service.created_by_id,
                "trip_id": trip_id,
                "verification": "Verified",
                "created_by_company": self.api_service.created_by_company_id
            }
            
            print("Creating parcel...")
            result = await self.api_service.create_parcel(payload)
            
            return f"Parcel created successfully!\n\nDetails:\n- Company: {parcel_info['company']}\n- Route: {parcel_info['from_city'].title()} -> {parcel_info['to_city'].title()}\n- Weight: {parcel_info['weight']}\n- Material: {parcel_info['material'].title()}\n\nParcel ID: {result.get('id', 'N/A')}\nCost: Rs.{calculated_cost}"
                
        except Exception as e:
            return f"Error creating parcel: {str(e)}"
    
    async def process_message(self, message: str) -> str:
        """Process natural language message and create parcel"""
        try:
            print(f"Processing message: {message}")
            
            # Extract information using Gemini
            parcel_info = self.extract_parcel_info(message)
            print(f"Extracted info: {parcel_info}")
            
            # Create parcel using API service
            result = await self.create_parcel(parcel_info)
            return result
            
        except Exception as e:
            return f"Error processing message: {str(e)}"