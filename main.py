import os
import logging
from dotenv import load_dotenv
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Command handlers
def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(
        f"👋 Hello {user.first_name}! Welcome to AutoSniper - your personal car deal hunter.\n\n"
        f"I scan multiple car listing sites to find vehicles priced significantly below market value, "
        f"giving you a competitive edge in spotting great deals before others.\n\n"
        f"Use /help to see available commands or /demo to see what car alerts look like!"
    )
    
    # Here we'd save user information to Google Sheets - we'll implement this in Task 4

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🔍 *AutoSniper Commands:*\n\n"
        "/start - Begin interaction with AutoSniper\n"
        "/help - Show this help message\n"
        "/demo - View sample car alerts\n\n"
        
        "🚗 *Coming Soon:*\n"
        "/setfilter - Set your car preferences\n"
        "/myfilter - View your current car preferences\n"
        "/subscribe - Upgrade to premium for more features\n\n"
        
        "Have questions? Contact us at support@autosniper.example.com"
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def demo_command(update: Update, context: CallbackContext) -> None:
    """Show sample car alerts when the command /demo is issued."""
    # Sample car alert
    demo_alert1 = (
        "🚨 *A+ DEAL ALERT!* 🚨\n\n"
        "🚗 *2018 BMW 3 Series 320d M Sport*\n"
        "💰 *Price: £14,500* (Market avg: £19,200)\n"
        "🔄 72,000 miles | ⛽ Diesel | 📍 Manchester\n"
        "📊 *Score: A+* (24% below market)\n\n"
        "➡️ [View Listing](https://example.com/listing)"
    )
    
    update.message.reply_text(demo_alert1, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    
    # Second sample alert
    demo_alert2 = (
        "🚨 *B DEAL ALERT!* 🚨\n\n"
        "🚗 *2020 Volkswagen Golf 1.5 TSI Life*\n"
        "💰 *Price: £17,995* (Market avg: £20,100)\n"
        "🔄 25,000 miles | ⛽ Petrol | 📍 Birmingham\n"
        "📊 *Score: B* (10% below market)\n\n"
        "➡️ [View Listing](https://example.com/listing)"
    )
    
    update.message.reply_text(demo_alert2, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    
    # Explanation text
    explanation = (
        "These are examples of the alerts you'll receive when AutoSniper finds good deals matching your criteria.\n\n"
        "Our scoring system ranges from A+ (exceptional value) to D (average deal).\n\n"
        "Ready to set up your car preferences? This feature will be available soon!"
    )
    
    update.message.reply_text(explanation)

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("demo", demo_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()