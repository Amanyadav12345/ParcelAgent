import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from src.agents.parcel_agent import process_telegram_message

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ParcelTelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup telegram bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Message handler for parcel requests
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
Welcome to Parcel Agent Bot! 🚚

I can help you create parcels by processing your natural language requests.

Example message:
"Hi, I want to create a parcel for Berger where route is Jaipur to Kolkata and size of parcel is 100kg and type of material like paint"

Just send me a message with your parcel details and I'll create it for you!
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
How to use Parcel Agent Bot:

1. Send a message describing your parcel request
2. Include these details:
   - Company name (who the parcel is for)
   - Route (from city to city)
   - Weight/size of parcel
   - Material type

Example:
"Create a parcel for ABC Company from Jaipur to Kolkata, 50kg paint"

Available cities: Jaipur, Kolkata
Available materials: Paint

The bot will extract the information and create the parcel for you!
        """
        await update.message.reply_text(help_message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages and process parcel requests"""
        try:
            user_message = update.message.text
            logger.info(f"Received message: {user_message}")
            
            # Send initial processing message
            processing_message = await update.message.reply_text(
                "🔄 Processing your parcel request...\n⏳ This may take a moment while I fetch the latest data."
            )
            
            # Send typing indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing"
            )
            
            try:
                # Process the message with our agent (this will wait for APIs)
                response = await process_telegram_message(user_message)
                
                # Delete processing message and send final response
                await processing_message.delete()
                await update.message.reply_text(response)
                
            except Exception as processing_error:
                # Update processing message with error
                await processing_message.edit_text(
                    f"❌ Sorry, I encountered an error processing your request:\n{str(processing_error)}\n\nPlease try again or contact support."
                )
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await update.message.reply_text(
                f"❌ Sorry, I encountered an error processing your request: {str(e)}"
            )
    
    def run(self):
        """Run the bot"""
        logger.info("Starting Parcel Agent Bot...")
        try:
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True  # Drop any pending updates to avoid conflicts
            )
        except Exception as e:
            if "Conflict" in str(e):
                logger.error("❌ Bot conflict detected! Another instance might be running.")
                logger.error("💡 Solution: Stop all other bot instances and try again.")
                print("\n🚨 ERROR: Another bot instance is already running!")
                print("📝 To fix this:")
                print("   1. Close any other terminal windows running the bot")
                print("   2. Wait 30 seconds")
                print("   3. Try running the bot again")
                print("   4. If still failing, restart your terminal\n")
            else:
                logger.error(f"Bot error: {e}")
                print(f"❌ Bot error: {e}")
            raise


if __name__ == "__main__":
    bot = ParcelTelegramBot()
    bot.run()