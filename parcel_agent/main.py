#!/usr/bin/env python3
"""
Parcel Agent - CrewAI Agent with Telegram Bot and MCP Integration
"""

import asyncio
import sys
import os
from src.telegram.bot import ParcelTelegramBot


def main():
    """Main entry point"""
    try:
        # Check if .env file exists
        if not os.path.exists('.env'):
            print("⚠️  .env file not found!")
            print("Please copy .env.example to .env and fill in your API keys:")
            print("- TELEGRAM_BOT_TOKEN")
            print("- GEMINI_API_KEY") 
            print("- PARCEL_API_BEARER_TOKEN")
            return
        
        print("🚀 Starting Parcel Agent Bot...")
        
        # Start the telegram bot
        bot = ParcelTelegramBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down Parcel Agent Bot...")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()