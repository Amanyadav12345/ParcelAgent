import os
import json
import re
import asyncio
import logging
import traceback
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
from src.services.api_service import APIService

load_dotenv()

# Configure logging for this module
logger = logging.getLogger(__name__)


class ParcelAgent:
    def __init__(self, auth_token=None):
        logger.info("🤖 Initializing ParcelAgent...")
        logger.info(f"   Auth token provided: {'✓' if auth_token else '✗'}")
        
        try:
            genai_key = os.getenv("GEMINI_API_KEY")
            if not genai_key:
                logger.error("❌ GEMINI_API_KEY not found in environment")
                raise ValueError("GEMINI_API_KEY is required")
            
            logger.info("   🔧 Configuring Gemini AI...")
            genai.configure(api_key=genai_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("   ✅ Gemini AI configured successfully")
            
            logger.info("   🔧 Initializing API service...")
            self.api_service = APIService(auth_token=auth_token)
            logger.info("   ✅ API service initialized")
            
            logger.info("✅ ParcelAgent initialization completed")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ParcelAgent: {str(e)}")
            logger.error(f"   Stack trace: {traceback.format_exc()}")
            raise
    
    def extract_parcel_info(self, message: str) -> Dict[str, Any]:
        """Use Gemini to extract structured information from message"""
        logger.info(f"🧠 Extracting parcel info from message: {message[:100]}...")
        
        prompt = f"""
        Extract parcel information from this message: "{message}"
        
        Return ONLY a JSON object with these exact fields (no additional text):
        {{
            "company": "company name mentioned or 'Unknown'",
            "from_city": "origin city name or null if not clearly mentioned",
            "to_city": "destination city name or null if not clearly mentioned", 
            "weight": "weight number only (e.g., 100) or null if not mentioned",
            "weight_unit": "weight unit mentioned (kg, grams, tons, pounds, etc.) or null if not mentioned",
            "material": "material type mentioned or null if not mentioned",
            "price": "price/cost mentioned (number only) or null if not mentioned",
            "has_missing_info": true/false based on whether critical info is missing
        }}
        
        Examples of cities: jaipur, kolkata, mumbai, delhi, chennai, bangalore
        Examples of materials: electronics, furniture, textiles, food items, chemicals, machinery
        Examples of weight units: kg, grams, g, tons, tonnes, pounds, lbs, kilos
        
        IMPORTANT: 
        - Set "has_missing_info" to true if from_city, to_city, weight, or material are null/unclear
        - For weight, separate the number and unit (e.g., "50kg" -> weight: 50, weight_unit: "kg")
        - If no unit is mentioned, set weight_unit to null
        - Do NOT make assumptions - if something is not clearly stated, set it to null
        - For price, extract only the number if mentioned (e.g., "5000" from "cost is 5000 rupees")
        """
        
        try:
            logger.info("   📡 Sending request to Gemini AI...")
            response = self.model.generate_content(prompt)
            logger.info(f"   📨 Received response from Gemini: {response.text[:200]}...")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                logger.info("   ✅ Successfully parsed JSON from Gemini response")
                parsed_info = json.loads(json_match.group())
                logger.info(f"   📋 Extracted info: {parsed_info}")
                return parsed_info
            else:
                logger.warning("   ⚠️ No JSON found in Gemini response, using fallback parsing")
                return self._fallback_parse(message)
        except json.JSONDecodeError as e:
            logger.error(f"   ❌ JSON parsing error: {e}")
            logger.info("   🔄 Falling back to regex parsing")
            return self._fallback_parse(message)
        except Exception as e:
            logger.error(f"   ❌ Gemini extraction error: {str(e)}")
            logger.error(f"   Stack trace: {traceback.format_exc()}")
            logger.info("   🔄 Falling back to regex parsing")
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
        
        from_city, to_city = None, None
        for pattern in route_patterns:
            route_match = re.search(pattern, message_lower)
            if route_match:
                from_city = route_match.group(1)
                to_city = route_match.group(2)
                break
        
        # Extract weight and unit
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(kg|kgs|kilos?|grams?|g|tons?|tonnes?|pounds?|lbs?)?', message_lower)
        weight = None
        weight_unit = None
        if weight_match:
            weight = float(weight_match.group(1))
            unit = weight_match.group(2)
            if unit:
                weight_unit = unit.lower()
            # If no unit specified, don't assume anything
        
        # Extract material
        material_patterns = [
            r'material\s+like\s+(\w+)',
            r'type\s+of\s+material\s+like\s+(\w+)',
            r'material\s+(\w+)',
            r'(\w+)\s+material',
        ]
        
        material = None
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
        
        # Check if critical information is missing
        has_missing_info = not all([from_city, to_city, weight, material])
        
        return {
            "company": company,
            "from_city": from_city,
            "to_city": to_city,
            "weight": weight,
            "weight_unit": weight_unit,
            "material": material,
            "price": price,
            "has_missing_info": has_missing_info
        }
    
    def convert_weight_to_api_format(self, weight: float, weight_unit: str) -> tuple:
        """Convert weight and unit to API format (quantity, quantity_unit)"""
        if not weight_unit:
            # Default to kilograms if no unit specified
            return weight, "KILOGRAMS"
        
        unit_lower = weight_unit.lower()
        
        # Map common weight units to exact API format (based on actual API payload)
        unit_mapping = {
            'kg': 'KILOGRAMS',
            'kgs': 'KILOGRAMS', 
            'kilo': 'KILOGRAMS',
            'kilos': 'KILOGRAMS',
            'kilogram': 'KILOGRAMS',
            'kilograms': 'KILOGRAMS',
            'g': 'GRAMS',
            'gram': 'GRAMS',
            'grams': 'GRAMS',
            'ton': 'TONNES',
            'tons': 'TONNES',
            'tonne': 'TONNES',
            'tonnes': 'TONNES',
            'pound': 'POUNDS',
            'pounds': 'POUNDS',
            'lb': 'POUNDS',
            'lbs': 'POUNDS'
        }
        
        api_unit = unit_mapping.get(unit_lower, 'KILOGRAMS')  # Default to kg if unknown
        
        logger.info(f"   WEIGHT_CONVERT: Weight unit conversion: {weight_unit} -> {api_unit}")
        return weight, api_unit
    
    def convert_weight_to_kg(self, weight: float, weight_unit: str) -> float:
        """Convert weight to kilograms for cost calculation"""
        if not weight_unit:
            return weight  # Assume kg if no unit
            
        unit_lower = weight_unit.lower()
        
        # Convert to kg for cost calculation
        if unit_lower in ['g', 'gram', 'grams']:
            return weight / 1000
        elif unit_lower in ['ton', 'tons', 'tonne', 'tonnes']:
            return weight * 1000
        elif unit_lower in ['pound', 'pounds', 'lb', 'lbs']:
            return weight * 0.453592
        else:
            return weight  # Already in kg or unknown unit

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
        logger.info("📦 Starting parcel creation process...")
        logger.info(f"   Input parcel info: {parcel_info}")
        
        try:
            # Extract weight value and unit
            weight_value = parcel_info.get("weight")
            weight_unit = parcel_info.get("weight_unit")
            
            logger.info(f"   Weight: {weight_value} {weight_unit or 'no unit'}")
            
            if weight_value is None:
                logger.error("❌ Weight information is missing")
                return "Error: Weight information is missing"
            
            # Convert weight to API format
            api_weight, api_unit = self.convert_weight_to_api_format(weight_value, weight_unit)
            
            # Convert weight to kg for cost calculation
            weight_kg = self.convert_weight_to_kg(weight_value, weight_unit)
            
            print(f"Looking up IDs for:")
            print(f"   - From: {parcel_info['from_city']}")
            print(f"   - To: {parcel_info['to_city']}")
            print(f"   - Material: {parcel_info['material']}")
            print(f"   - Company: {parcel_info['company']}")
            print(f"   - Weight: {weight_value} {weight_unit or 'kg'} -> API: {api_weight} {api_unit}")
            
            # Get IDs dynamically
            print("Fetching city information...")
            from_city_id = await self.api_service.get_city_id(parcel_info['from_city'])
            to_city_id = await self.api_service.get_city_id(parcel_info['to_city'])
            
            print("Fetching material information...")
            material_id = await self.api_service.get_material_id(parcel_info['material'])
            
            # Use default company ID from environment instead of looking up
            logger.info("COMPANY: Using default company from environment")
            company_id = self.api_service.default_company_id
            
            logger.info(f"ID_LOOKUP: Found IDs:")
            logger.info(f"   - From City: {from_city_id}")
            logger.info(f"   - To City: {to_city_id}")
            logger.info(f"   - Material: {material_id}")
            logger.info(f"   - Company: {company_id} (default from env)")
            
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
            
            # STEP 1: Call trip API FIRST and get trip_id dynamically
            logger.info("WORKFLOW: STEP 1 - Calling Trip API to create trip and get trip_id")
            logger.info(f"WORKFLOW: Route: {from_city_id} → {to_city_id}")
            
            try:
                trip_id = await self.api_service.get_trip_by_route(from_city_id, to_city_id)
                logger.info(f"WORKFLOW: ✅ Trip API completed - Dynamic trip_id: {trip_id}")
            except Exception as e:
                logger.error(f"WORKFLOW: ❌ Trip API failed: {str(e)}")
                return f"Error: Failed to create trip for route {parcel_info['from_city']} to {parcel_info['to_city']}. Details: {str(e)}"
            
            if not trip_id:
                logger.error("WORKFLOW: ❌ No trip_id received from Trip API")
                return "Error: Trip API did not return a valid trip_id. Please check the trip API configuration."
            
            # Calculate dynamic cost using kg equivalent
            calculated_cost = self.get_dynamic_cost(parcel_info, weight_kg)
            print(f"DEBUG: Parcel info extracted: {parcel_info}")
            print(f"DEBUG: Weight for API: {api_weight} {api_unit}")
            print(f"DEBUG: Weight for cost calculation: {weight_kg}kg")
            print(f"DEBUG: Calculated cost: {calculated_cost}")
            
            # Create parcel payload
            payload = {
                "material_type": material_id,
                "quantity": api_weight,
                "quantity_unit": api_unit, 
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
                    "sender_person": self.api_service.created_by_id,
                    "sender_company": company_id,
                    "name": "Default Sender",
                    "gstin": None
                },
                "receiver": {
                    "receiver_person": self.api_service.created_by_id,
                    "receiver_company": company_id,
                    "name": "Default Receiver", 
                    "gstin": None
                },
                "created_by": self.api_service.created_by_id,
                "trip_id": trip_id,
                "verification": "Verified",
                "created_by_company": self.api_service.created_by_company_id
            }
            
            # STEP 2: Now create parcel using the dynamic trip_id from step 1
            logger.info("WORKFLOW: STEP 2 - Creating parcel with dynamic trip_id")
            logger.info(f"WORKFLOW: Using trip_id: {trip_id}")
            
            result = await self.api_service.create_parcel(payload)
            logger.info("WORKFLOW: ✅ Parcel API completed successfully")
            
            # Format weight display
            weight_display = f"{weight_value}{weight_unit or 'kg'}"
            
            return f"Parcel created successfully!\n\nDetails:\n- Company: {parcel_info['company']}\n- Route: {parcel_info['from_city'].title()} -> {parcel_info['to_city'].title()}\n- Weight: {weight_display}\n- Material: {parcel_info['material'].title()}\n\nParcel ID: {result.get('id', 'N/A')}\nCost: Rs.{calculated_cost}"
                
        except Exception as e:
            logger.error(f"❌ Error creating parcel: {str(e)}")
            logger.error(f"   Stack trace: {traceback.format_exc()}")
            return f"Error creating parcel: {str(e)}"
    
    def generate_clarifying_question(self, parcel_info: Dict[str, Any]) -> str:
        """Generate a clarifying question based on missing information"""
        missing_fields = []
        
        if not parcel_info.get('from_city'):
            missing_fields.append("origin city")
        if not parcel_info.get('to_city'):
            missing_fields.append("destination city")
        if not parcel_info.get('weight'):
            missing_fields.append("weight")
        if not parcel_info.get('material'):
            missing_fields.append("material type")
        
        if not missing_fields:
            return None
            
        # Create a friendly clarifying question
        if len(missing_fields) == 1:
            question = f"I need to know the {missing_fields[0]} to create your parcel. Could you please provide this information?"
        elif len(missing_fields) == 2:
            question = f"I need to know the {missing_fields[0]} and {missing_fields[1]} to create your parcel. Could you please provide these details?"
        else:
            question = f"I need a few more details to create your parcel: {', '.join(missing_fields[:-1])}, and {missing_fields[-1]}. Could you please provide this information?"
        
        # Add examples based on what's missing
        examples = []
        if "origin city" in missing_fields or "destination city" in missing_fields:
            examples.append("cities like Jaipur, Kolkata, Mumbai, Delhi")
        if "weight" in missing_fields:
            examples.append("weight like 5kg, 10kg, 2.5kg")
        if "material type" in missing_fields:
            examples.append("material like electronics, chemicals, furniture")
        
        if examples:
            question += f"\n\nFor example: {', '.join(examples)}"
        
        return question

    async def process_message(self, message: str) -> str:
        """Process natural language message and create parcel"""
        logger.info(f"💬 Processing message: {message[:100]}...")
        
        try:
            # Extract information using Gemini
            logger.info("   🧠 Extracting parcel information...")
            parcel_info = self.extract_parcel_info(message)
            logger.info(f"   📋 Extracted info: {parcel_info}")
            
            # Check if critical information is missing
            logger.info("   🔍 Checking for missing information...")
            if parcel_info.get('has_missing_info', False):
                logger.info("   ❓ Missing information detected, generating clarifying question")
                question = self.generate_clarifying_question(parcel_info)
                if question:
                    logger.info(f"   📝 Generated question: {question[:50]}...")
                    return f"❓ **Missing Information**\n\n{question}"
            
            # Validate that we have the minimum required information
            missing_validations = []
            
            if not parcel_info.get('from_city') or not parcel_info.get('to_city'):
                logger.warning("   ⚠️ Missing cities information")
                missing_validations.append("cities")
                return "❓ **Missing Cities**\n\nI need to know both the origin city (from where) and destination city (to where) to create your parcel. Please provide both cities.\n\nFor example: 'from Jaipur to Kolkata' or 'Jaipur to Mumbai'"
            
            if not parcel_info.get('weight'):
                logger.warning("   ⚠️ Missing weight information")
                missing_validations.append("weight")
                return "❓ **Missing Weight**\n\nI need to know the weight of your parcel. Please specify the weight with units.\n\nFor example: '5kg', '10kg', '2.5kg'"
            
            if not parcel_info.get('material'):
                logger.warning("   ⚠️ Missing material information")
                missing_validations.append("material")
                return "❓ **Missing Material**\n\nI need to know what type of material you're shipping. Please specify the material type.\n\nFor example: 'electronics', 'chemicals', 'furniture', 'textiles'"
            
            if not missing_validations:
                logger.info("   ✅ All required information present")
            
            # Create parcel using API service
            logger.info("   📦 All information available, creating parcel...")
            result = await self.create_parcel(parcel_info)
            logger.info(f"   ✅ Parcel processing completed: {result[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {str(e)}")
            logger.error(f"   Stack trace: {traceback.format_exc()}")
            return f"Error processing message: {str(e)}"