#!/usr/bin/env python3
"""Debug script to test price extraction"""

import asyncio
from src.agents.parcel_agent import ParcelAgent

async def test_price_extraction():
    agent = ParcelAgent()
    
    # Test messages with price
    test_messages = [
        "Create parcel for ABC company from jaipur to kolkata with weight 200kg of electronics material for cost 5000 rupees",
        "Create parcel from jaipur to kolkata with 200kg electronics cost 3000",
        "Send parcel ABC company from jaipur to kolkata 200kg electronics price 4000 rs",
        "Parcel for ABC from jaipur to kolkata 200kg electronics Rs 2500"
    ]
    
    for message in test_messages:
        print(f"\nTesting message: {message}")
        parcel_info = agent.extract_parcel_info(message)
        print(f"Extracted info: {parcel_info}")
        
        # Test cost calculation
        weight_kg = float(parcel_info.get('weight', '200kg').replace('kg', ''))
        calculated_cost = agent.get_dynamic_cost(parcel_info, weight_kg)
        print(f"Calculated cost: {calculated_cost}")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(test_price_extraction())