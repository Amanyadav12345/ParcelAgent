from pydantic import BaseModel
from typing import Optional
import re


class ParcelInfo(BaseModel):
    company: Optional[str] = None
    route_from: Optional[str] = None
    route_to: Optional[str] = None
    weight: Optional[str] = None
    material_type: Optional[str] = None
    raw_message: str


class MessageParser:
    def __init__(self):
        self.patterns = {
            'company': r'for\s+(\w+)',
            'route': r'route\s+is\s+(\w+)\s+to\s+(\w+)',
            'weight': r'size\s+of\s+parcel\s+is\s+(\d+\w+)',
            'material': r'type\s+of\s+material\s+like\s+(\w+)',
        }
    
    def parse_message(self, message: str) -> ParcelInfo:
        """Parse telegram message to extract parcel information"""
        message_lower = message.lower()
        
        # Extract company
        company_match = re.search(self.patterns['company'], message_lower)
        company = company_match.group(1) if company_match else None
        
        # Extract route
        route_match = re.search(self.patterns['route'], message_lower)
        route_from = route_match.group(1) if route_match else None
        route_to = route_match.group(2) if route_match else None
        
        # Extract weight
        weight_match = re.search(self.patterns['weight'], message_lower)
        weight = weight_match.group(1) if weight_match else None
        
        # Extract material type
        material_match = re.search(self.patterns['material'], message_lower)
        material_type = material_match.group(1) if material_match else None
        
        return ParcelInfo(
            company=company,
            route_from=route_from,
            route_to=route_to,
            weight=weight,
            material_type=material_type,
            raw_message=message
        )