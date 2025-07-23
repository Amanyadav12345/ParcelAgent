# Parcel Agent - CrewAI with Telegram & MCP

A simple AI agent system that processes parcel creation requests via Telegram using CrewAI, Gemini, and MCP protocol.

## Features

- 🤖 **CrewAI Agent**: Intelligent parcel processing agent
- 📱 **Telegram Bot**: Natural language parcel requests via Telegram
- 🔗 **MCP Integration**: Model Context Protocol for API interactions
- 🧠 **Gemini AI**: Google's Gemini for message understanding
- 🚚 **Parcel API**: Direct integration with parcel service API

## Architecture

```
Telegram Message → Gemini (NLP) → CrewAI Agent → MCP Server → Parcel API
```

## Setup

1. **Clone and install dependencies:**
```bash
cd parcel_agent
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Required API Keys:**
- `TELEGRAM_BOT_TOKEN`: Get from @BotFather on Telegram
- `GEMINI_API_KEY`: Get from Google AI Studio
- `PARCEL_API_BEARER_TOKEN`: Your parcel service bearer token

## Usage

1. **Start the bot:**
```bash
python main.py
```

2. **Send a message to your Telegram bot:**
```
Hi, I want to create a parcel for Berger where route is Jaipur to Kolkata and size of parcel is 100kg and type of material like paint
```

3. **The bot will:**
   - Parse your message with Gemini
   - Extract parcel details
   - Create parcel via MCP → API
   - Respond with confirmation

## Project Structure

```
parcel_agent/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── src/
│   ├── agents/
│   │   └── parcel_agent.py    # CrewAI agent
│   ├── telegram/
│   │   └── bot.py             # Telegram bot handler
│   └── parsers/
│       └── message_parser.py   # Message parsing utilities
└── mcp_server/
    └── parcel_mcp.py          # MCP server for API integration
```

## Supported Cities & Materials

**Cities:** Jaipur, Kolkata  
**Materials:** Paint

## Example Messages

- "Create a parcel for ABC Company from Jaipur to Kolkata, 50kg paint"
- "Hi, I want to create a parcel for Berger where route is Jaipur to Kolkata and size of parcel is 100kg and type of material like paint"
- "Make a parcel for XYZ Corp, route Kolkata to Jaipur, 25kg paint"