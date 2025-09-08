import asyncio
import json
import os
from typing import Any, Dict
import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequestParams,
    EmbeddedResource,
    TextContent,
    Tool,
)
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class ParcelPayload(BaseModel):
    material_type: str
    quantity: int
    quantity_unit: str = "KILOGRAMS"
    description: str = None
    cost: int
    part_load: bool = False
    pickup_postal_address: Dict[str, Any]
    unload_postal_address: Dict[str, Any]
    sender: Dict[str, Any]
    receiver: Dict[str, Any]
    created_by: str
    trip_id: str
    verification: str = "Verified"
    created_by_company: str


class ParcelMCPServer:
    def __init__(self):
        self.server = Server("parcel-server")
        self.api_url = os.getenv("PARCEL_API_URL")
        self.bearer_token = os.getenv("PARCEL_API_BEARER_TOKEN")
        
        # City and material type mappings (you'll need to populate these)
        self.city_ids = {
            "jaipur": "61b9dbed91248f261f80f824",
            "kolkata": "61f925c6a721cdc7bfde1435",
        }
        
        self.material_type_ids = {
            "paint": "61547b0b988da3862e52daaa",
        }
        
        self.setup_tools()
    
    def setup_tools(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="create_parcel",
                    description="Create a new parcel with the provided details",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "company": {"type": "string"},
                            "from_city": {"type": "string"},
                            "to_city": {"type": "string"},
                            "weight": {"type": "string"},
                            "material": {"type": "string"},
                            "cost": {"type": "integer"}
                        },
                        "required": ["company", "from_city", "to_city", "weight", "material"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            if name == "create_parcel":
                return await self.create_parcel(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def create_parcel(self, params: dict) -> list[TextContent]:
        try:
            # Extract weight value
            weight_str = params.get("weight", "100kg")
            weight_value = int(''.join(filter(str.isdigit, weight_str)))
            
            # Map cities and material types
            from_city_id = self.city_ids.get(params["from_city"].lower())
            to_city_id = self.city_ids.get(params["to_city"].lower())
            material_id = self.material_type_ids.get(params["material"].lower())
            
            if not from_city_id or not to_city_id or not material_id:
                return [TextContent(
                    type="text",
                    text=f"Error: Could not map city or material type. Available cities: {list(self.city_ids.keys())}, materials: {list(self.material_type_ids.keys())}"
                )]
            
            payload = {
                "material_type": material_id,
                "quantity": weight_value,
                "quantity_unit": "KILOGRAMS",
                "description": f"Parcel for {params['company']}",
                "cost": params.get("cost", 29997),
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
                    "sender_company": params["company"],
                    "name": None,
                    "gstin": None
                },
                "receiver": {
                    "receiver_person": None,
                    "receiver_company": None,
                    "name": None,
                    "gstin": None
                },
                "created_by": "6257f1d75b42235a2ae4ab34",
                # "trip_id": "688062304b74ba99e30075d6",
                "verification": "Verified",
                "created_by_company": "62d66794e54f47829a886a1d"
            }
            
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                return [TextContent(
                    type="text",
                    text=f"Parcel created successfully! Response: {json.dumps(result, indent=2)}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error creating parcel: {str(e)}"
            )]
    
    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="parcel-server",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


if __name__ == "__main__":
    server = ParcelMCPServer()
    asyncio.run(server.run())