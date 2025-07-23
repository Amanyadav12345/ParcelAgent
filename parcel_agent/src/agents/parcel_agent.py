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
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
        self.api_service = APIService()
    
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
            "material": "material type mentioned"
        }}
        
        Examples of cities: jaipur, kolkata, mumbai, delhi, chennai, bangalore
        Examples of materials: electronics, furniture, textiles, food items, chemicals, machinery
        
        IMPORTANT: Do NOT use "paint" as material type. Extract the actual material type mentioned.
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
        
        return {
            "company": company,
            "from_city": from_city,
            "to_city": to_city,
            "weight": weight,
            "material": material
        }
    
    async def create_parcel(self, parcel_info: Dict[str, Any]) -> str:
        """Create parcel using API service with dynamic ID fetching"""
        try:
            # Extract weight value
            weight_str = parcel_info.get("weight", "100kg")
            weight_value = int(''.join(filter(str.isdigit, weight_str)))
            
            print(f"🔍 Looking up IDs for:")
            print(f"   - From City: {parcel_info['from_city']}")
            print(f"   - To City: {parcel_info['to_city']}")
            print(f"   - Material: {parcel_info['material']}")
            print(f"   - Company: {parcel_info['company']}")
            
            # Fetch IDs from APIs (these will wait at least 5 seconds each if needed)
            print("🏙️ Fetching city information...")
            from_city_id = await self.api_service.get_city_id(parcel_info["from_city"])
            to_city_id = await self.api_service.get_city_id(parcel_info["to_city"])
            
            print("🎨 Fetching material information...")
            material_id = await self.api_service.get_material_id(parcel_info["material"])
            
            print("🏢 Fetching company information...")
            company_id = await self.api_service.get_company_id(parcel_info["company"])
            
            print(f"📋 Found IDs:")
            print(f"   - From City ID: {from_city_id}")
            print(f"   - To City ID: {to_city_id}")
            print(f"   - Material ID: {material_id}")
            print(f"   - Company ID: {company_id}")
            
            # Check if required city IDs are found (material has fallback)
            missing_ids = []
            if not from_city_id:
                missing_ids.append(f"city '{parcel_info['from_city']}'")
            if not to_city_id:
                missing_ids.append(f"city '{parcel_info['to_city']}'")
            
            if missing_ids:
                return f"❌ Error: Could not find IDs for: {', '.join(missing_ids)}.\nPlease check the spelling or contact support."
            
            # Material ID will always have a value (either found or default fallback)
            if not material_id:
                material_id = self.api_service.default_material_id
                print(f"⚠️ No material found, using default: {material_id}")
            
            # Create parcel payload
            payload = {
                "material_type": material_id,
                "quantity": weight_value,
                "quantity_unit": "KILOGRAMS",
                "description": f"Parcel for {parcel_info['company']} - {parcel_info['material']}",
                "cost": 29997,
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
                    "sender_company": company_id if company_id else parcel_info["company"],
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
                "trip_id": self.api_service.trip_id,
                "verification": "Verified",
                "created_by_company": self.api_service.created_by_company_id
            }
            
            print("📦 Creating parcel...")
            result = await self.api_service.create_parcel(payload)
            
            return f"✅ Parcel created successfully!\n\n📦 Details:\n- Company: {parcel_info['company']}\n- Route: {parcel_info['from_city'].title()} → {parcel_info['to_city'].title()}\n- Weight: {parcel_info['weight']}\n- Material: {parcel_info['material'].title()}\n\n🆔 Parcel ID: {result.get('id', 'N/A')}\n💰 Cost: ₹{result.get('cost', '29997')}"
                
        except Exception as e:
            return f"❌ Error creating parcel: {str(e)}"
    
    async def process_message(self, message: str) -> str:
        """Main function to process telegram message"""
        try:
            print(f"📨 Processing message: {message}")
            
            # Extract information using Gemini
            parcel_info = self.extract_parcel_info(message)
            print(f"🧠 Extracted info: {parcel_info}")
            
            # Create parcel using API service
            result = await self.create_parcel(parcel_info)
            
            return result
            
        except Exception as e:
            return f"❌ Error processing message: {str(e)}"


# Simplified function for telegram integration
async def process_telegram_message(message: str) -> str:
    """Process telegram message and create parcel"""
    agent = ParcelAgent()
    
    # Initialize API cache on first use
    if not agent.api_service.cities_cache:
        await agent.api_service.initialize_cache()
    
    return await agent.process_message(message)