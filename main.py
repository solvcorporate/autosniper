import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from sheets import get_sheets_manager
from conversations import get_car_preferences_conversation
from scraper_manager import get_scraper_manager
from scheduler import get_scheduler
from alerts import AlertEngine
from payments import get_payment_manager
from subscription import get_subscription_manager, SUBSCRIPTION_FEATURES

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
    
    # Check if this is a deep link with a specific parameter
    deep_link = context.args[0] if context.args else None
    
    if deep_link == "payment_success":
        # Handle successful payment
        subscription_manager = get_subscription_manager()
        current_tier = subscription_manager.get_user_tier(user.id)
        
        await update.message.reply_text(
            f"🎉 *Payment Successful!* 🎉\n\n"
            f"Your {current_tier} subscription has been activated. Thank you for supporting AutoSniper!\n\n"
            f"Use /managesubscription to view your subscription details.",
            parse_mode="MARKDOWN"
        )
        return
    
    elif deep_link == "payment_cancel":
        # Handle cancelled payment
        await update.message.reply_text(
            "Your payment was cancelled.\n\n"
            "If you encountered any issues or have questions, feel free to try again or contact support.\n\n"
            "Use /subscribe to view subscription options.",
            parse_mode="MARKDOWN"
        )
        return
    
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
        "/subscribe - View subscription options\n"
        "/subscribe_basic - Subscribe to Basic plan (€10/month)\n"
        "/subscribe_premium - Subscribe to Premium plan (€20/month)\n"
        "/managesubscription - View and manage your current subscription\n"
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
        "Use the /mycars command to set up your preferences!"
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
        "A: We offer two tiers: Basic (€10/month) and Premium (€20/month). Premium subscribers get access to additional features, priority alerts, and exclusive content not available to Basic users.\n\n"
        
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
    # Get subscription manager
    subscription_manager = get_subscription_manager()
    
    # Get user's current subscription tier
    user_id = update.effective_user.id
    current_tier = subscription_manager.get_user_tier(user_id)
    
    # Check if user already has an active subscription
    if current_tier in ['Basic', 'Premium']:
        await update.message.reply_text(
            f"You currently have an active *{current_tier}* subscription.\n\n"
            f"To upgrade or manage your subscription, please use /managesubscription.",
            parse_mode="MARKDOWN"
        )
        return
    
    # Show subscription options
    basic_features = "\n".join([f"• {feature}" for feature in SUBSCRIPTION_FEATURES['Basic']['features']])
    premium_features = "\n".join([f"• {feature}" for feature in SUBSCRIPTION_FEATURES['Premium']['features']])
    
    subscribe_text = (
        "*AutoSniper Subscription Options*\n\n"
        f"{SUBSCRIPTION_FEATURES['Basic']['emoji']} *{SUBSCRIPTION_FEATURES['Basic']['name']}: {SUBSCRIPTION_FEATURES['Basic']['price']}*\n"
        f"{basic_features}\n\n"
        f"{SUBSCRIPTION_FEATURES['Premium']['emoji']} *{SUBSCRIPTION_FEATURES['Premium']['name']}: {SUBSCRIPTION_FEATURES['Premium']['price']}*\n"
        f"{premium_features}\n\n"
        "To subscribe, use one of these commands:\n"
        "/subscribe_basic - Subscribe to the Basic Plan\n"
        "/subscribe_premium - Subscribe to the Premium Plan"
    )
    await update.message.reply_text(subscribe_text, parse_mode="MARKDOWN")

async def subscribe_basic_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /subscribe_basic command to subscribe to the Basic plan."""
    await process_subscription(update, context, 'Basic')

async def subscribe_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /subscribe_premium command to subscribe to the Premium plan."""
    await process_subscription(update, context, 'Premium')

async def process_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, tier: str) -> None:
    """Process subscription for a specific tier."""
    user = update.effective_user
    
    # Get payment manager
    payment_manager = get_payment_manager()
    
    # Send initial message
    message = await update.message.reply_text(
        f"Creating your {tier} subscription checkout... One moment please."
    )
    
    try:
        # Create a Stripe checkout session
        # For testing, use your bot's username
        success_url = "https://t.me/autosniper_bot?start=payment_success"
        cancel_url = "https://t.me/autosniper_bot?start=payment_cancel"
        
        checkout_url = payment_manager.create_checkout_session(
            user_id=user.id,
            tier=tier,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if not checkout_url:
            await message.edit_text(
                "Sorry, there was an error creating your checkout session. Please try again later."
            )
            return
        
        # Create an inline keyboard with the payment link
        keyboard = [[InlineKeyboardButton(f"Pay {SUBSCRIPTION_FEATURES[tier]['price']}", url=checkout_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send payment link
        await message.edit_text(
            f"Great! Click the button below to complete your {tier} subscription payment.\n\n"
            f"Once completed, you'll have access to all {tier} features!",
            reply_markup=reply_markup
        )
    
    except Exception as e:
        logger.error(f"Error processing subscription: {e}")
        await message.edit_text(
            "Sorry, there was an error processing your subscription request. Please try again later."
        )

async def managesubscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /managesubscription command to view and manage subscription."""
    user_id = update.effective_user.id
    
    # Get subscription manager
    subscription_manager = get_subscription_manager()
    
    # Get user's subscription details
    subscription = subscription_manager.get_subscription_details(user_id)
    
    # Format the details for display
    tier = subscription.get('tier', 'None')
    is_active = subscription.get('active', False)
    expiration_date = subscription.get('expiration_date', 'Unknown')
    
    if tier == 'None' or not is_active:
        # User has no active subscription
        await update.message.reply_text(
            "You don't have an active subscription.\n\n"
            "Use /subscribe to view available subscription options.",
            parse_mode="MARKDOWN"
        )
        return
    
    # Display subscription details
    message = (
        f"*Your {tier} Subscription*\n\n"
        f"Status: {'Active' if is_active else 'Inactive'}\n"
        f"Expires: {expiration_date}\n\n"
    )
    
    # Add tier-specific features
    if tier in SUBSCRIPTION_FEATURES:
        features = "\n".join([f"• {feature}" for feature in SUBSCRIPTION_FEATURES[tier]['features']])
        message += f"Your features include:\n{features}\n\n"
    
    # Add management options
    if tier == 'Basic':
        message += "Want more features? Use /subscribe_premium to upgrade to Premium!"
    
    await update.message.reply_text(
        message,
        parse_mode="MARKDOWN"
    )

async def dealsofweek_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /dealsofweek command to show the best deals (Premium only)."""
    user_id = update.effective_user.id
    
    # Check if user has premium subscription
    subscription_manager = get_subscription_manager()
    is_premium = subscription_manager.is_user_premium(user_id)
    
    if not is_premium:
        await update.message.reply_text(
            "*Deals of the Week - Premium Feature*\n\n"
            "This premium feature provides a curated list of the absolute best deals across all categories.\n\n"
            "Premium subscription required to access this feature.\n\n"
            "Use /subscribe to learn about our subscription options.",
            parse_mode="MARKDOWN"
        )
        return
    
    # If user is premium, show them the deals
    await update.message.reply_text(
        "*Deals of the Week*\n\n"
        "Here are this week's top car deals, curated especially for our premium subscribers:\n\n"
        "1. *2019 BMW 3 Series* - €21,500 (15% below market) - A+ Deal\n"
        "2. *2020 Audi A4* - €24,750 (12% below market) - A Deal\n"
        "3. *2018 Mercedes C-Class* - €19,900 (10% below market) - B+ Deal\n\n"
        "For full details and more premium deals, check back weekly for updates!",
        parse_mode="MARKDOWN"
    )

async def run_scrapers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger the scrapers to run (admin only)."""
    user = update.effective_user
    
    # Check if user is admin (for now, just a simple check - you might want to improve this)
    is_admin = user.id == 1566446879  # Replace with your actual Telegram ID
    
    if not is_admin:
        await update.message.reply_text(
            "Sorry, this command is for administrators only."
        )
        return
    
    # Send initial message
    status_message = await update.message.reply_text(
        "🔄 Starting scraper job...\n\n"
        "This may take a few minutes. I'll update you when it's done."
    )
    
    # Get the scraper manager
    scraper_manager = get_scraper_manager()
    
    # Run the scraper job in a way that doesn't block the bot
    context.application.create_task(
        run_scraper_job_background(update, context, status_message, scraper_manager)
    )

# Add this new function for the alert system
async def send_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger the alert system to send notifications (admin only)."""
    user = update.effective_user
    
    # Check if user is admin (for now, just a simple check - you might want to improve this)
    is_admin = user.id == 1566446879  # Replace with your actual Telegram ID
    
    if not is_admin:
        await update.message.reply_text(
            "Sorry, this command is for administrators only."
        )
        return
    
    # Send initial message
    status_message = await update.message.reply_text(
        "🔄 Starting to process alerts...\n\n"
        "This may take a few minutes. I'll update you when it's done."
    )
    
    # Get the scraper manager
    scraper_manager = get_scraper_manager()
    
    # Run the scraper job in a way that doesn't block the bot
    context.application.create_task(
        process_alerts_background(update, context, status_message, scraper_manager)
    )

# Add this function to process alerts in the background
async def process_alerts_background(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   status_message: "Message", scraper_manager) -> None:
    """Process alert notifications in the background and update the status message."""
    try:
        # Get preferences from sheets
        preferences = scraper_manager.get_preferences_from_sheets()
        if not preferences:
            await status_message.edit_text(
                "❌ No user preferences found. Cannot process alerts."
            )
            return
        
        # Get all recent listings from sheets (implementation depends on your sheets structure)
        # This is a placeholder - you'll need to implement this in your sheets_manager
        listings = []
        if scraper_manager.sheets_manager:
            # Assuming a get_recent_listings method exists
            try:
                listings = scraper_manager.sheets_manager.get_recent_listings(days=1)
            except Exception as e:
                logger.error(f"Error getting listings from sheets: {e}")
        
        if not listings:
            # Run scrapers to get listings if none in sheets
            listings = scraper_manager.run_scrapers(preferences)
        
        if not listings:
            await status_message.edit_text(
                "❌ No listings found. Cannot process alerts."
            )
            return
        
        # Match listings to preferences
        matches = scraper_manager.match_listings_to_preferences(listings, preferences)
        
        if not matches:
            await status_message.edit_text(
                "ℹ️ No matches found between listings and user preferences."
            )
            return
        
        # Initialize the alert engine
        alert_engine = AlertEngine(context.bot)
        
        # Process matches and send alerts
        alert_stats = await alert_engine.process_matches(
            matches, 
            sheets_manager=scraper_manager.sheets_manager
        )
        
        # Update the status message with the results
        await status_message.edit_text(
            "✅ Alert processing completed!\n\n"
            f"📊 Statistics:\n"
            f"• {alert_stats['total_users']} users had matching listings\n"
            f"• {alert_stats['total_matches']} total matches were found\n" 
            f"• {alert_stats['alerts_sent']} alerts were sent successfully\n"
            f"• {alert_stats['users_notified']} users received notifications\n"
            f"• {alert_stats['failures']} failures occurred\n\n"
            f"The system will automatically process alerts on the next scraper run."
        )
    except Exception as e:
        logger.error(f"Error processing alerts: {e}")
        await status_message.edit_text(
            "❌ Error processing alerts.\n\n"
            f"Error details: {str(e)}\n\n"
            "Please check the logs for more information."
        )

# Update this function to include alert processing
async def run_scraper_job_background(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   status_message: "Message", scraper_manager) -> None:
    """Run the scraper job in the background and update the status message."""
    try:
        # Run the scraper job
        stats = scraper_manager.run_scraper_job()
        
        # Process alerts if matches were found
        matches_found = False
        alert_stats = {
            "total_users": 0,
            "total_matches": 0,
            "alerts_sent": 0,
            "users_notified": 0,
            "failures": 0
        }
        
        # Check if there are matches to process
        if stats.get("matches", 0) > 0:
            # Initialize the alert engine
            alert_engine = AlertEngine(context.bot)
            
            # Get matches from the most recent scraper run (implementation depends on your structure)
            matches = {}  # This should be populated with actual matches
            
            if matches:
                # Process matches and send alerts
                alert_stats = await alert_engine.process_matches(
                    matches, 
                    sheets_manager=scraper_manager.sheets_manager
                )
                matches_found = True
        
        # Update the status message with the results
        result_message = (
            "✅ Scraper job completed!\n\n"
            f"📊 Statistics:\n"
            f"• Processed {stats['preferences']} preferences\n"
            f"• Found {stats['listings']} listings\n"
            f"• Saved {stats['saved']} new listings\n"
        )
        
        if 'matches' in stats:
            result_message += f"• Matched {stats['matches']} listings to users\n"
        
        if 'grades' in stats:
            grade_counts = stats['grades']
            grades_text = ", ".join([f"{grade}: {count}" for grade, count in grade_counts.items() if count > 0])
            result_message += f"• Grades: {grades_text}\n"
        
        result_message += f"• Took {stats['duration_seconds']:.1f} seconds\n"
        
        if matches_found:
            result_message += "\n📨 Alert Processing:\n"
            result_message += f"• {alert_stats['alerts_sent']} alerts sent to {alert_stats['users_notified']} users\n"
            
            if alert_stats['failures'] > 0:
                result_message += f"• {alert_stats['failures']} failures occurred\n"
        
        await status_message.edit_text(result_message)
    except Exception as e:
        logger.error(f"Error running scraper job: {e}")
        await status_message.edit_text(
            "❌ Error running scraper job.\n\n"
            f"Error details: {str(e)}\n\n"
            "Please check the logs for more information."
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
    application.add_handler(CommandHandler("subscribe_basic", subscribe_basic_command))
    application.add_handler(CommandHandler("subscribe_premium", subscribe_premium_command))
    application.add_handler(CommandHandler("managesubscription", managesubscription_command))
    application.add_handler(CommandHandler("dealsofweek", dealsofweek_command))
    # Register admin commands
    application.add_handler(CommandHandler("runscraper", run_scrapers_command))
    application.add_handler(CommandHandler("sendalerts", send_alerts_command))
    
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

    # Start the scheduler
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Scheduler started")
    
    # Start the Bot - using a different approach that works better in cloud environments
    application.run_polling()

if __name__ == '__main__':
    main()
