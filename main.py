import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from sheets import get_sheets_manager
from conversations import get_car_preferences_conversation

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Google Sheets manager
sheets_manager = get_sheets_manager()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcoming and engaging introduction when the command /start is issued."""
    user = update.effective_user
    welcome_message = (
        f"👋 *Welcome to AutoSniper, {user.first_name}!*\n\n"
        f"🚗 I'm your personal car deal hunter that never sleeps.\n\n"
        f"I continuously scan across the top auto marketplaces to find vehicles priced significantly below market value, "
        f"giving you a competitive edge to spot exceptional deals before anyone else.\n\n"
        f"*How it works:*\n"
        f"1️⃣ Tell me what cars you're interested in\n"
        f"2️⃣ I'll scan multiple auto listings 24/7\n"
        f"3️⃣ Get instant alerts when great deals appear\n"
        f"4️⃣ Be the first to contact sellers and secure the best prices\n\n"
        f"Try these commands:\n"
        f"• /help - See all available commands\n"
        f"• /demo - View sample car alerts\n\n"
        f"Ready to start finding amazing car deals? Use /mycars to set up your preferences!"
    )
    
    await update.message.reply_text(welcome_message, parse_mode="MARKDOWN")
    
    # Store user information in Google Sheets
    if sheets_manager:
        user_added = sheets_manager.add_user(
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username
        )
        if user_added:
            logger.info(f"User saved to Google Sheets: {user.first_name} {user.last_name} (ID: {user.id})")
        else:
            logger.error(f"Failed to save user to Google Sheets: {user.id}")
    else:
        logger.warning("Google Sheets integration not available. User not saved.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🔍 *AutoSniper Commands:*\n\n"
        "/start - Begin interaction with AutoSniper\n"
        "/help - Show this help message\n"
        "/demo - View sample car alerts\n"
        "/faq - Frequently asked questions\n"
        "/mycars - View and manage your car preferences\n"
        "/subscribe - Choose between Basic (€10) and Premium (€25) tiers\n"
        "/dealsofweek - View this week's top deals (Premium only)\n\n"
        
        "You can cancel any ongoing setup process by typing 'cancel' at any point.\n\n"
        
        "🚗 *Coming Soon:*\n"
        "• WhatsApp integration\n"
        "• Referral program\n\n"
        
        "Have questions? Contact us at solvcorporate@gmail.com"
    )
    await update.message.reply_text(help_text, parse_mode="MARKDOWN")

async def demo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show realistic sample car alerts with explanation of the scoring system."""
    
    # Introduction to demo
    intro_message = (
        "*📊 AutoSniper Advanced Deal Scoring System 📊*\n\n"
        "Our comprehensive scoring analyzes multiple factors:\n"
        "• Price comparison to market average\n"
        "• Mileage and vehicle condition\n"
        "• Documentation completeness (tax, NCT, service history)\n"
        "• Listing quality (photos, description detail)\n"
        "• Seller responsiveness and history\n\n"
        "Deals are rated from A+ to D:\n"
        "• *A+*: Exceptional all-around value\n"
        "• *A*: Great deal with strong positives\n"
        "• *B*: Good deal with some advantages\n"
        "• *C*: Fair deal with minor benefits\n"
        "• *D*: Standard market offering\n\n"
        "Here are some sample alerts you'd receive:"
    )
    
    await update.message.reply_text(intro_message, parse_mode="MARKDOWN")
    
    # First sample alert - A+ deal
    demo_alert1 = (
        "🚨 *A+ DEAL ALERT!* 🚨\n\n"
        "🚗 *2018 BMW 3 Series 320d M Sport*\n"
        "💰 *Price: £14,500* (Market avg: £19,200)\n"
        "🔄 72,000 miles | ⛽ Diesel | 📍 Manchester\n"
        "🛡️ Full service history | ✅ Valid road tax & NCT\n"
        "🖼️ 12 high-quality photos | 🧰 2 previous owners\n"
        "📊 *Score: A+* (Price: 24% below market + Complete docs + Excellent listing)\n\n"
        "💬 Suggested message: \"Hi, is your BMW 3 Series still available? I can view it today and pay in cash if we agree on a price.\"\n\n"
        "➡️ [View Listing](https://example.com/listing)"
    )
    
    await update.message.reply_text(demo_alert1, parse_mode="MARKDOWN", disable_web_page_preview=True)
    
    # Second sample alert - B deal
    demo_alert2 = (
        "🚨 *B DEAL ALERT!* 🚨\n\n"
        "🚗 *2020 Volkswagen Golf 1.5 TSI Life*\n"
        "💰 *Price: £17,995* (Market avg: £20,100)\n"
        "🔄 25,000 miles | ⛽ Petrol | 📍 Birmingham\n"
        "🛡️ Warranty until 2023 | ✅ Valid road tax\n"
        "🖼️ 6 photos | 🧰 1 previous owner\n"
        "📊 *Score: B* (Price: 10% below market + Low mileage + Good documentation)\n\n"
        "💬 Suggested message: \"Hello, I'm interested in your VW Golf. Is it still for sale? I'd like to arrange a viewing this week.\"\n\n"
        "➡️ [View Listing](https://example.com/listing)"
    )
    
    await update.message.reply_text(demo_alert2, parse_mode="MARKDOWN", disable_web_page_preview=True)
    
    # Third sample alert - A deal from another source
    demo_alert3 = (
        "🚨 *A DEAL ALERT!* 🚨\n\n"
        "🚗 *2019 Audi A4 2.0 TDI S Line*\n"
        "💰 *Price: £16,750* (Market avg: £19,900)\n"
        "🔄 45,000 miles | ⛽ Diesel | 📍 London\n"
        "🛡️ Approved used | ✅ Full NCT | ✅ Road tax until Dec\n"
        "🖼️ 9 high-quality photos | 🧰 1 previous owner\n"
        "📊 *Score: A* (Price: 16% below market + Complete documentation + Dealer certified)\n\n"
        "💬 Suggested message: \"Hi there, I'm very interested in your Audi A4. Is it still available for viewing?\"\n\n"
        "➡️ [View Listing](https://example.com/listing)"
    )
    
    await update.message.reply_text(demo_alert3, parse_mode="MARKDOWN", disable_web_page_preview=True)
    
    # Call-to-action and explanation
    cta_message = (
        "*Ready to find your next car at an unbeatable price?*\n\n"
        "AutoSniper continuously monitors multiple platforms to find deals like these matching your criteria.\n\n"
        "Use the /mycars command to set up your preferences now!"
    )
    
    await update.message.reply_text(cta_message, parse_mode="MARKDOWN")

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display frequently asked questions and their answers."""
    
    faq_text = (
        "*❓ Frequently Asked Questions ❓*\n\n"
        
        "*Q: How does AutoSniper find better deals than I could find myself?*\n"
        "A: We monitor multiple car listing sites 24/7 and use a sophisticated algorithm to compare prices against market averages. We spot deals the moment they appear, giving you a competitive advantage.\n\n"
        
        "*Q: What car listing sites do you monitor?*\n"
        "A: We currently monitor AutoTrader, Gumtree, Facebook Marketplace, and DoneDeal, with more platforms coming soon.\n\n"
        
        "*Q: What subscription options are available?*\n"
        "A: We offer two tiers: Basic (€10/month) and Premium (€25/month). Premium subscribers get access to additional features, priority alerts, and exclusive content not available to Basic users.\n\n"
        
        "*Q: How do I tell AutoSniper what cars I'm looking for?*\n"
        "A: Simply chat with the bot! Tell it what make, model, price range, and other details you're interested in. The bot will guide you through a simple conversation to collect your preferences.\n\n"
        
        "*Q: How accurate is your scoring system?*\n"
        "A: Our scoring system analyzes multiple factors beyond just price - including mileage, documentation (tax, NCT), photos, and listing quality. Each car is compared against thousands of similar vehicles to provide an accurate assessment from A+ to D.\n\n"
        
        "*Q: What is \"Deals of the Week\"?*\n"
        "A: Deals of the Week is our premium feature that provides a curated list of the absolute best deals across all categories. Our algorithm identifies exceptional value opportunities even outside your specific preferences, so you never miss an amazing deal.\n\n"
        
        "*Q: What happens if I find a great deal through AutoSniper?*\n"
        "A: We provide a direct link to the original listing and even suggest an initial message to send the seller. From there, you'll interact directly with the seller as you normally would.\n\n"
        
        "Have another question? Contact us at solvcorporate@gmail.com"
    )
    
    await update.message.reply_text(faq_text, parse_mode="MARKDOWN")

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /subscribe command to manage subscription tiers."""
    subscribe_text = (
        "*AutoSniper Subscription Options*\n\n"
        "🔹 *Basic Plan: €10/month*\n"
        "• Multiple car listings monitored\n"
        "• Regular deal alerts\n"
        "• Custom car preferences\n\n"
        
        "🔸 *Premium Plan: €25/month*\n"
        "• All Basic features\n"
        "• Priority alerts for new deals\n"
        "• Access to all monitored platforms\n"
        "• Exclusive Deals of the Week\n"
        "• Advanced filtering options\n\n"
        
        "Payment system coming soon. Stay tuned!"
    )
    await update.message.reply_text(subscribe_text, parse_mode="MARKDOWN")
    
async def dealsofweek_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /dealsofweek command to show the best deals (Premium only)."""
    await update.message.reply_text(
        "*Deals of the Week*\n\n"
        "This premium feature provides a curated list of the absolute best deals across all categories.\n\n"
        "Premium subscription required to access this feature.\n\n"
        "Use /subscribe to learn more about our subscription options.",
        parse_mode="MARKDOWN"
    )

def main():
    """Start the bot without using asyncio.run() which can cause issues in some environments"""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Store sheets_manager in bot_data for access in conversation handlers
    if sheets_manager:
        application.bot_data['sheets_manager'] = sheets_manager
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("demo", demo_command))
    application.add_handler(CommandHandler("faq", faq_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("dealsofweek", dealsofweek_command))
    
    # Register conversation handler for car preferences
    if sheets_manager:
        car_conversation = get_car_preferences_conversation(sheets_manager)
        application.add_handler(car_conversation)
    else:
        logger.error("Google Sheets integration not available. Car preferences conversation disabled.")
        
        # Add a basic handler for /mycars when sheets is not available
        async def mycars_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "Sorry, the car preferences feature is not available right now. Please try again later."
            )
        application.add_handler(CommandHandler("mycars", mycars_fallback))

    # Start the Bot - using a different approach that works better in cloud environments
    application.run_polling()

if __name__ == '__main__':
    main()
