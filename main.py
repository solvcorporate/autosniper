# Changes summary:
# 1. Fixed syntax error at line 1021 (removed duplicate elif block)
# 2. Fixed indentation issue in handle_start_buttons function
# 3. Removed redundant code - consolidated duplicated elif blocks
# 4. Fixed formatting and alignment issues

import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, 
    filters, CallbackQueryHandler, ConversationHandler
)

from sheets import get_sheets_manager
from conversations import get_car_preferences_conversation
from scraper_manager import get_scraper_manager
from scheduler import get_scheduler
from alerts import AlertEngine
from payments import get_payment_manager
from subscription import get_subscription_manager, SUBSCRIPTION_FEATURES
from middleware import get_subscription_middleware
from tutorials import get_tutorial_manager

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

# Initialize subscription middleware
subscription_middleware = get_subscription_middleware()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcoming and engaging introduction when the command /start is issued."""
    user = update.effective_user
    
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
    
    # Check if this is a deep link with a specific parameter
    deep_link = context.args[0] if context.args else None
    
    # Handle deep link parameters
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
        # Continue with onboarding after payment
        context.user_data['onboarding_step'] = 'post_payment'
        
    elif deep_link == "payment_cancel":
        # Handle cancelled payment
        await update.message.reply_text(
            "Your payment was cancelled.\n\n"
            "If you encountered any issues or have questions, feel free to try again or contact support.\n\n"
            "Use /subscribe to view subscription options.",
            parse_mode="MARKDOWN"
        )
        return
    
    # Check if this is a returning user
    if sheets_manager and sheets_manager.user_exists(user.id):
        # Get basic user stats
        car_preferences = sheets_manager.get_car_preferences(user.id) if sheets_manager else []
        preference_count = len(car_preferences)
        
        # Create keyboard for returning users
        keyboard = [
            [InlineKeyboardButton("🚗 My Car Preferences", callback_data="my_cars")],
            [InlineKeyboardButton("🔍 See Sample Alerts", callback_data="sample_alerts")]
        ]
        
        # Add subscription button based on current status
        subscription_manager = get_subscription_manager()
        current_tier = subscription_manager.get_user_tier(user.id)
        
        if current_tier in ['Basic', 'Premium']:
            keyboard.append([InlineKeyboardButton("💳 Manage Subscription", callback_data="manage_subscription")])
        else:
            keyboard.append([InlineKeyboardButton("✨ Upgrade to Premium", callback_data="view_subscription")])
        
        # Add tutorial button
        keyboard.append([InlineKeyboardButton("📚 Tutorials & Guides", callback_data="tutorial_list")])
        
        # Add help button
        keyboard.append([InlineKeyboardButton("❓ Help & FAQ", callback_data="view_help")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_back_message = (
            f"👋 *Welcome back to AutoSniper, {user.first_name}!*\n\n"
            f"You currently have {preference_count} active car preference{'s' if preference_count != 1 else ''}.\n\n"
            f"What would you like to do today?"
        )
        
        await update.message.reply_text(
            welcome_back_message,
            parse_mode="MARKDOWN",
            reply_markup=reply_markup
        )
    
    else:
        # New user - start the onboarding sequence
        context.user_data['onboarding_step'] = 'welcome'
        
        # Create keyboard for new users
        keyboard = [
            [InlineKeyboardButton("🚗 How It Works", callback_data="onboard_how_it_works")],
            [InlineKeyboardButton("👀 See Sample Alerts", callback_data="onboard_sample_alerts")],
            [InlineKeyboardButton("🏁 Set Up My First Car", callback_data="onboard_setup_car")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = (
            f"👋 *Welcome to AutoSniper, {user.first_name}!*\n\n"
            f"*I scan car websites 24/7 to find you exceptional deals before anyone else.*\n\n"
            f"I'll alert you when cars matching your criteria are listed at prices *significantly below market value*.\n\n"
            f"Car enthusiasts and resellers use AutoSniper to:\n"
            f"• Find incredible bargains worth £1000s\n"
            f"• Be first to contact sellers for the best deals\n"
            f"• Save hours of manual searching daily\n\n"
            f"Ready to find your perfect car deal? Choose an option below to get started!"
        )
        
        await update.message.reply_text(
            welcome_message,
            parse_mode="MARKDOWN",
            reply_markup=reply_markup
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user_id = update.effective_user.id
    
    # Get user's subscription status
    subscription_manager = get_subscription_manager()
    is_premium = subscription_manager.is_user_premium(user_id)
    has_subscription = subscription_manager.has_active_subscription(user_id)
    
    # Base commands
    base_commands = (
        "🔍 *AutoSniper Commands:*\n\n"
        "/start - Begin interaction with AutoSniper\n"
        "/help - Show this help message\n"
        "/demo - View sample car alerts\n"
        "/faq - Frequently asked questions\n"
        "/tutorial - Access interactive tutorials and guides\n"
        "/mycars - View and manage your car preferences\n"
        "/subscribe - View subscription options\n"
        "/subscribe_basic - Subscribe to Basic plan (€10/month)\n"
        "/subscribe_premium - Subscribe to Premium plan (€20/month)\n"
        "/managesubscription - View and manage your current subscription\n"
    )
    
    # Premium commands - format differently based on user's subscription
    premium_commands = ""
    if is_premium:
        premium_commands = (
            "*Premium Commands:* ✨\n"
            "/dealsofweek - View this week's top deals\n"
            "/car_details [number] - Get detailed information about a specific deal\n\n"
        )
    else:
        premium_commands = (
            "*Premium Commands:* 🔒\n"
            "/dealsofweek - View this week's top deals (Premium only)\n"
            "/car_details [number] - Get detailed information about a specific deal (Premium only)\n\n"
        )
    
    # Additional info
    additional_info = (
        "You can cancel any ongoing setup process by typing 'cancel' at any point.\n\n"
        "📚 Use /tutorial to access interactive tutorials and guides.\n\n"
        "🚗 *Coming Soon:*\n"
        "• WhatsApp integration\n"
        "• Referral program\n\n"
    )
    
    # Subscription status
    subscription_status = ""
    if is_premium:
        subscription_status = "🔸 *Your Status:* Premium Subscriber\n\n"
    elif has_subscription:
        subscription_status = "🔹 *Your Status:* Basic Subscriber\n\n"
    else:
        subscription_status = "⚪ *Your Status:* Free User\n\n"
    
    # Support info
    support_info = "Have questions? Contact us at solvcorporate@gmail.com"
    
    # Combine all sections
    help_text = base_commands + "\n" + premium_commands + subscription_status + additional_info + support_info
    
    # Add tutorial suggestion button
    keyboard = [
        [InlineKeyboardButton("📚 View Tutorials", callback_data="tutorial_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, parse_mode="MARKDOWN", reply_markup=reply_markup)

async def tutorial_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available tutorials."""
    # Get the tutorial manager
    tutorial_manager = get_tutorial_manager(sheets_manager)
    
    # Check if a specific tutorial was requested
    if context.args and len(context.args) > 0:
        # Try to match the argument to a tutorial
        requested_tutorial = context.args[0].lower()
        
        # Map common arguments to tutorial IDs
        tutorial_map = {
            "start": "getting_started",
            "begin": "getting_started",
            "premium": "premium_features",
            "advanced": "advanced_search",
            "search": "advanced_search",
            "help": "troubleshooting",
            "troubleshoot": "troubleshooting",
            "faq": "troubleshooting"
        }
        
        # Get the tutorial ID if it matches
        tutorial_id = None
        if requested_tutorial in tutorial_map:
            tutorial_id = tutorial_map[requested_tutorial]
        
        # If we found a matching tutorial, start it
        if tutorial_id:
            await tutorial_manager.start_tutorial(update, context, tutorial_id)
            return
    
    # If no specific tutorial was requested or found, show the list
    await tutorial_manager.show_tutorial_list(update, context)

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
    
    # Create keyboard for next steps
    keyboard = [
        [InlineKeyboardButton("🏁 Set Up My First Car", callback_data="onboard_setup_car")],
        [InlineKeyboardButton("💰 View Subscription Options", callback_data="view_subscription")],
        [InlineKeyboardButton("📚 View Tutorials", callback_data="tutorial_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(cta_message, parse_mode="MARKDOWN", reply_markup=reply_markup)

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
        
        "*Q: I need help setting up my preferences. What should I do?*\n"
        "A: Use the /mycars command to start the guided setup process. If you run into any issues, you can type 'cancel' at any point and start over. We also have tutorials available via the /tutorial command.\n\n"
        
        "*Q: How many car preferences can I have active at once?*\n"
        "A: Free users can have 1 active preference, Basic subscribers can have up to 3, and Premium subscribers get unlimited preferences.\n\n"
        
        "*Q: What if I need to cancel my subscription?*\n"
        "A: You can manage your subscription at any time using the /managesubscription command. Cancellation takes effect at the end of your current billing period.\n\n"
        
        "Have another question? Contact us at solvcorporate@gmail.com"
    )
    
    # Add tutorial button
    keyboard = [
        [InlineKeyboardButton("📚 View Tutorials", callback_data="tutorial_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(faq_text, parse_mode="MARKDOWN", reply_markup=reply_markup)

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
    
    # Create keyboard for subscription options
    keyboard = [
        [InlineKeyboardButton("Subscribe to Basic", callback_data="subscribe_basic")],
        [InlineKeyboardButton("Subscribe to Premium", callback_data="subscribe_premium")],
        [InlineKeyboardButton("📚 Learn More About Premium", callback_data="start_tutorial_premium_features")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(subscribe_text, parse_mode="MARKDOWN", reply_markup=reply_markup)

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
        success_url = "https://t.me/autosniprbot?start=payment_success"
        cancel_url = "https://t.me/autosniprbot?start=payment_cancel"
        
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
        # Create keyboard for upgrading
        keyboard = [
            [InlineKeyboardButton("Upgrade to Premium", callback_data="subscribe_premium")],
            [InlineKeyboardButton("📚 View Premium Features Tutorial", callback_data="start_tutorial_premium_features")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message += "Want more features? Upgrade to Premium for unlimited alerts and exclusive features!"
        
        await update.message.reply_text(
            message,
            parse_mode="MARKDOWN",
            reply_markup=reply_markup
        )
    else:
        # Create keyboard for premium users
        keyboard = [
            [InlineKeyboardButton("📚 Premium Features Tutorial", callback_data="start_tutorial_premium_features")],
            [InlineKeyboardButton("🔍 Advanced Search Tutorial", callback_data="start_tutorial_advanced_search")],
            [InlineKeyboardButton("❓ Troubleshooting Guide", callback_data="start_tutorial_troubleshooting")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode="MARKDOWN",
            reply_markup=reply_markup
        )

@subscription_middleware.premium_required
async def dealsofweek_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /dealsofweek command to show the best deals (Premium only)."""
    user_id = update.effective_user.id
    
    # If user is premium, show them the deals
    # Send a loading message
    loading_message = await update.message.reply_text(
        "🔍 *Finding this week's best deals...*",
        parse_mode="MARKDOWN"
    )
    
    try:
        # Get the deals manager
        from dealsofweek import get_deals_of_week_manager
        from sheets import get_sheets_manager
        
        sheets_manager = get_sheets_manager()
        deals_manager = get_deals_of_week_manager(sheets_manager)
        
        # Get the top deals (limited to 10)
        top_deals = deals_manager.get_deals_of_week(max_deals=10)
        
        # Format the deals as a message
        deals_message = deals_manager.format_deals_of_week_message(top_deals)
        
        # Store the deals in context for later reference
        if 'deals_of_week' not in context.bot_data:
            context.bot_data['deals_of_week'] = {}
        context.bot_data['deals_of_week'][user_id] = top_deals
        
        # Update the loading message with the deals
        await loading_message.edit_text(
            deals_message,
            parse_mode="MARKDOWN",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error getting deals of the week: {e}")
        await loading_message.edit_text(
            "*Deals of the Week*\n\n"
            "We're currently updating our deals database. Please check back in a few minutes.\n\n"
            "In the meantime, you can use /mycars to manage your car preferences or /help to see all available commands.",
            parse_mode="MARKDOWN"
        )

@subscription_middleware.premium_required
async def car_details_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /car_details command to show detailed information about a specific deal."""
    user_id = update.effective_user.id
    
    # Check if user provided an index
    if not context.args:
        await update.message.reply_text(
            "Please provide the number of the car you want details for.\n"
            "Example: /car_details 1",
            parse_mode="MARKDOWN"
        )
        return
    
    try:
        # Parse the index
        index = int(context.args[0]) - 1  # Convert to 0-based index
        
        # Get the deals for this user
        if 'deals_of_week' not in context.bot_data or user_id not in context.bot_data['deals_of_week']:
            await update.message.reply_text(
                "Please use /dealsofweek first to see the current deals.",
                parse_mode="MARKDOWN"
            )
            return
        
        deals = context.bot_data['deals_of_week'][user_id]
        
        # Check if index is valid
        if index < 0 or index >= len(deals):
            await update.message.reply_text(
                f"Invalid car number. Please provide a number between 1 and {len(deals)}.",
                parse_mode="MARKDOWN"
            )
            return
        
        # Get the deal
        deal = deals[index]
        
        # Get the deals manager to format the message
        from dealsofweek import get_deals_of_week_manager
        deals_manager = get_deals_of_week_manager()
        
        # Format the deal details
        details_message = deals_manager.format_deal_details(deal)
        
        # Send the details
        await update.message.reply_text(
            details_message,
            parse_mode="MARKDOWN",
            disable_web_page_preview=True
        )
    except ValueError:
        await update.message.reply_text(
            "Please provide a valid number.\n"
            "Example: /car_details 1",
            parse_mode="MARKDOWN"
        )
    except Exception as e:
        logger.error(f"Error getting car details: {e}")
        await update.message.reply_text(
            "Sorry, there was an error retrieving the car details. Please try again later.",
            parse_mode="MARKDOWN"
        )

async def run_scrapers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger the scrapers to run (admin only)."""
    user = update.effective_user
    
    # Check if user is admin
    admin_id = 1566446879  # Replace with your actual Telegram ID
    
    if user.id != admin_id:
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

async def send_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger the alert system to send notifications (admin only)."""
    user = update.effective_user
    
    # Check if user is admin
    admin_id = 1566446879  # Replace with your actual Telegram ID
    is_admin = user.id == admin_id
    
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

async def handle_start_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Handle button clicks from the start message."""
   query = update.callback_query
   await query.answer()
   
   # Extract the callback data
   callback_data = query.data
   
   if callback_data == "my_cars":
       # Redirect to the /mycars command
       await query.message.delete()
       new_update = Update(update_id=update.update_id, message=query.message)
       await mycars(new_update, context)
   
   elif callback_data == "sample_alerts":
       # Show sample alerts
       await query.edit_message_text(
           text="*Loading sample alerts...*",
           parse_mode="MARKDOWN"
       )
       # Create a new update with the message from the callback query
       new_update = Update(update_id=update.update_id, message=query.message)
       await demo_command(new_update, context)
   
   elif callback_data == "manage_subscription":
       # Redirect to subscription management
       await query.edit_message_text(
           text="*Loading your subscription details...*",
           parse_mode="MARKDOWN"
       )
       new_update = Update(update_id=update.update_id, message=query.message)
       await managesubscription_command(new_update, context)
   
   elif callback_data == "view_subscription" or callback_data == "subscribe_basic" or callback_data == "subscribe_premium":
       # Show subscription options or process subscription
       if callback_data == "subscribe_basic":
           tier = "Basic"
           await process_subscription(update, context, tier)
       elif callback_data == "subscribe_premium":
           tier = "Premium"
           await process_subscription(update, context, tier)
       else:
           # Just show the options
           await query.edit_message_text(
               text="*Loading subscription options...*",
               parse_mode="MARKDOWN"
           )
           new_update = Update(update_id=update.update_id, message=query.message)
           await subscribe_command(new_update, context)
   
   elif callback_data == "view_help":
       # Show help and FAQ
       await query.edit_message_text(
           text="*Loading help & FAQ...*",
           parse_mode="MARKDOWN"
       )
       new_update = Update(update_id=update.update_id, message=query.message)
       await help_command(new_update, context)
   
   # Handle onboarding flow buttons
   elif callback_data == "onboard_how_it_works":
       await onboard_how_it_works(update, context)
   
   elif callback_data == "onboard_sample_alerts":
       await onboard_sample_alerts(update, context)
   
   elif callback_data == "onboard_setup_car":
       await onboard_setup_car(update, context)
   
   elif callback_data == "start_car_setup":
       await start_car_setup_from_callback(update, context)
       
   # Tutorial-related callbacks
   elif callback_data.startswith("tutorial_"):
       # Get the tutorial manager
       tutorial_manager = get_tutorial_manager(sheets_manager)
       
       # Handle tutorial buttons
       if callback_data == "tutorial_list":
           await tutorial_manager.show_tutorial_list(update, context)
       else:
           await tutorial_manager.handle_tutorial_button(update, context)
           
           # Track tutorial interaction in analytics if available
           try:
               if sheets_manager:
                   user_id = update.effective_user.id
                   tutorial_id = context.user_data.get('tutorial', {}).get('id')
                   if tutorial_id:
                       # Could add analytics tracking here when implemented
                       # sheets_manager.track_tutorial_interaction(user_id, tutorial_id, callback_data)
                       pass
           except Exception as e:
               logger.error(f"Error tracking tutorial interaction: {e}")

   elif callback_data.startswith("start_tutorial_"):
       # Get the tutorial manager
       tutorial_manager = get_tutorial_manager(sheets_manager)
       
       # Handle tutorial selection
       await tutorial_manager.handle_tutorial_selection(update, context)
       
       # Track tutorial start in analytics if available
       try:
           if sheets_manager:
               user_id = update.effective_user.id
               tutorial_id = callback_data.split('_')[2]
               # Could add analytics tracking here when implemented
               # sheets_manager.track_tutorial_start(user_id, tutorial_id)
               pass
       except Exception as e:
           logger.error(f"Error tracking tutorial start: {e}")

async def onboard_how_it_works(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Show new users how AutoSniper works."""
   query = update.callback_query
   
   # Update user's onboarding step
   context.user_data['onboarding_step'] = 'how_it_works'
   
   # Create keyboard for next steps
   keyboard = [
       [InlineKeyboardButton("👀 See Sample Alerts", callback_data="onboard_sample_alerts")],
       [InlineKeyboardButton("🏁 Set Up My First Car", callback_data="onboard_setup_car")],
       [InlineKeyboardButton("📚 View Detailed Tutorial", callback_data="start_tutorial_getting_started")]
   ]
   reply_markup = InlineKeyboardMarkup(keyboard)
   
   how_it_works = (
       "*How AutoSniper Works*\n\n"
       "1️⃣ *You tell me what cars you're looking for*\n"
       "Set your preferences: make, model, price range, location, etc.\n\n"
       "2️⃣ *I scan multiple websites 24/7*\n"
       "AutoTrader, Gumtree, Facebook Marketplace, and more\n\n"
       "3️⃣ *My algorithm identifies exceptional deals*\n"
       "Cars priced significantly below market value get priority\n\n"
       "4️⃣ *You receive instant Telegram alerts*\n"
       "With direct links to listings and suggested messages to sellers\n\n"
       "5️⃣ *You contact sellers before anyone else*\n"
       "Being first gives you the best chance to secure great deals\n\n"
       "Ready for the next step?"
   )
   
   await query.edit_message_text(
       text=how_it_works,
       parse_mode="MARKDOWN",
       reply_markup=reply_markup
   )

async def onboard_sample_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Show new users sample alerts."""
   query = update.callback_query
   
   # Update user's onboarding step
   context.user_data['onboarding_step'] = 'sample_alerts'
   
   # First update the message to indicate loading
   await query.edit_message_text(
       text="*Loading sample alerts...*",
       parse_mode="MARKDOWN"
   )
   
   # Create keyboard for next steps
   keyboard = [
       [InlineKeyboardButton("🚗 Set Up My First Car", callback_data="onboard_setup_car")],
       [InlineKeyboardButton("💰 View Premium Features", callback_data="view_subscription")]
   ]
   reply_markup = InlineKeyboardMarkup(keyboard)
   
   # Sample alert message
   sample_alert = (
       "*Here's an example of the alerts you'll receive:*\n\n"
       "🚨 *A+ DEAL ALERT!* 🚨\n\n"
       "🚗 *2018 BMW 3 Series 320d M Sport*\n"
       "💰 *Price: £14,500* (Market avg: £19,200)\n"
       "🔄 72,000 miles | ⛽ Diesel | 📍 Manchester\n"
       "🛡️ Full service history | ✅ Valid road tax & NCT\n"
       "📊 *Score: A+* (24% below market)\n\n"
       "➡️ [View Listing](https://example.com/listing)\n\n"
       "Ready to set up your first car preference?"
   )
   
   await query.message.reply_text(
       text=sample_alert,
       parse_mode="MARKDOWN",
       disable_web_page_preview=True,
       reply_markup=reply_markup
   )

async def onboard_setup_car(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Guide the user to set up their first car preference."""
   query = update.callback_query
   
   # Update user's onboarding step
   context.user_data['onboarding_step'] = 'setup_car'
   
   # First update the message to indicate loading
   await query.edit_message_text(
       text="*Setting up your first car preference...*",
       parse_mode="MARKDOWN"
   )
   
   setup_guide = (
       "*Let's set up your first car search*\n\n"
       "I'll help you create your first car preference to start finding deals.\n\n"
       "In the next steps, you'll tell me:\n"
       "• What make and model you're looking for\n"
       "• Your price range\n"
       "• Year range\n"
       "• Location preference\n"
       "• Optional details like fuel type\n\n"
       "Just tap the button below to begin!"
   )
   
   # Create keyboard for starting car setup
   keyboard = [
       [InlineKeyboardButton("🏁 Start Car Setup", callback_data="start_car_setup")]
   ]
   reply_markup = InlineKeyboardMarkup(keyboard)
   
   await query.message.reply_text(
       text=setup_guide,
       parse_mode="MARKDOWN",
       reply_markup=reply_markup
   )

async def start_car_setup_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Start the car setup process from a callback query."""
   query = update.callback_query
   await query.answer()
   
   if query.data == "start_car_setup":
       # Create a new Update object pointing to the original message
       # This allows us to call the existing mycars function
       new_update = Update(
           update_id=update.update_id,
           message=query.message
       )
       
       # Delete the button message
       await context.bot.delete_message(
           chat_id=query.message.chat_id,
           message_id=query.message.message_id
       )
       
       # Call the existing mycars command handler - reusing the /mycars command
       await mycars(new_update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Handle errors in a user-friendly way."""
   # Log the error
   logger.error(f"Error: {context.error} - Update: {update}")
   
   # Check if we have an update object (might be None in some errors)
   if update is None:
       return
   
   # Get the chat ID if possible
   chat_id = None
   if update.effective_chat:
       chat_id = update.effective_chat.id
   elif update.callback_query:
       chat_id = update.callback_query.message.chat_id
   
   if not chat_id:
       return  # Can't send a message without chat_id
   
   # Create a user-friendly error message
   error_message = (
       "😔 *Something went wrong*\n\n"
       "I encountered an unexpected issue. Don't worry, I've already notified our team about it.\n\n"
       "In the meantime, you can:\n"
       "• Try again in a few moments\n"
       "• Start over with the /start command\n"
       "• Contact support at solvcorporate@gmail.com\n\n"
       "Thank you for your patience!"
   )
   
   # Check if the error occurred in a tutorial
   if update.callback_query and update.callback_query.data.startswith("tutorial_"):
       try:
           # Add suggestion to view troubleshooting tutorial
           keyboard = [
               [InlineKeyboardButton("View Troubleshooting Guide", callback_data="start_tutorial_troubleshooting")]
           ]
           reply_markup = InlineKeyboardMarkup(keyboard)
           
           # Add troubleshooting suggestion to error message
           error_message += "\n\nWould you like to view our troubleshooting guide?"
           
           # Use reply_markup with the error message
           if 'reply_markup' not in locals():
               reply_markup = None
       except Exception:
           # If we hit an error while handling an error, just ignore it
           pass
   
   # Try to send the error message
   try:
       # If the error occurred in a callback query, edit the message if possible
       if update.callback_query:
           await context.bot.edit_message_text(
               chat_id=chat_id,
               message_id=update.callback_query.message.message_id,
               text=error_message,
               parse_mode="MARKDOWN"
           )
       else:
           # Otherwise, send a new message
           await context.bot.send_message(
               chat_id=chat_id,
               text=error_message,
               parse_mode="MARKDOWN"
           )
   except Exception as e:
       logger.error(f"Error sending error message: {e}")

async def mycars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Forward to the car preferences conversation handler."""
   # This is just a forwarding function to the conversation handler
   # The actual implementation is in the conversation handler in conversations.py
   await update.message.reply_text(
       "*Setting up your car preferences...*\n\n"
       "Let's find the perfect car deals for you. I'll ask you a series of questions about what you're looking for.",
       parse_mode="MARKDOWN"
   )
   
   # The conversation handler will take over from here

async def suggest_relevant_tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE, situation: str) -> None:
    """Suggest a relevant tutorial based on the user's situation.
    
    Args:
        update: Update object
        context: Context object
        situation: String describing the user's situation or need
    """
    # Get the tutorial manager
    tutorial_manager = get_tutorial_manager(sheets_manager)
    
    # Map situations to tutorial IDs
    situation_map = {
        "start": "getting_started",
        "welcome": "getting_started",
        "new_user": "getting_started",
        "premium": "premium_features",
        "subscription": "premium_features",
        "search": "advanced_search",
        "advanced": "advanced_search",
        "error": "troubleshooting",
        "problem": "troubleshooting",
        "help": "troubleshooting"
    }
    
    # Get the tutorial ID if it matches
    tutorial_id = None
    situation = situation.lower()
    
    for key, value in situation_map.items():
        if key in situation:
            tutorial_id = value
            break
    
    # Default to getting started
    if not tutorial_id:
        tutorial_id = "getting_started"
    
    # Get the tutorial
    from tutorials import TUTORIALS
    tutorial = TUTORIALS.get(tutorial_id)
    if not tutorial:
        return  # Invalid tutorial ID
    
    # Create keyboard with tutorial option
    keyboard = [
        [InlineKeyboardButton(f"View {tutorial['title']} Tutorial", callback_data=f"start_tutorial_{tutorial_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Personalize the message based on the situation
    if situation == "error" or situation == "problem":
        message = (
            "I noticed you encountered an issue. Would you like to view our troubleshooting guide?"
        )
    elif situation == "premium" or situation == "subscription":
        message = (
            "Want to learn more about Premium features? Check out our detailed tutorial!"
        )
    else:
        message = (
            f"💡 *Tutorial Suggestion*\n\n"
            f"Would you like to learn more about {tutorial['title'].lower()}?"
        )
    
    try:
        if update.message:
            await update.message.reply_text(
                message,
                parse_mode="MARKDOWN",
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                message, 
                parse_mode="MARKDOWN",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error suggesting tutorial: {e}")
        
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
   application.add_handler(CommandHandler("tutorial", tutorial_command))
   application.add_handler(CommandHandler("subscribe", subscribe_command))
   application.add_handler(CommandHandler("subscribebasic", subscribe_basic_command))
   application.add_handler(CommandHandler("subscribepremium", subscribe_premium_command))
   application.add_handler(CommandHandler("subscribe_basic", subscribe_basic_command))
   application.add_handler(CommandHandler("subscribe_premium", subscribe_premium_command))
   application.add_handler(CommandHandler("managesubscription", managesubscription_command))
   application.add_handler(CommandHandler("dealsofweek", dealsofweek_command))
   application.add_handler(CommandHandler("car_details", car_details_command))
   
   # Register admin commands
   application.add_handler(CommandHandler("runscraper", run_scrapers_command))
   application.add_handler(CommandHandler("sendalerts", send_alerts_command))
   
   # Register callback query handler for interactive buttons
   application.add_handler(CallbackQueryHandler(handle_start_buttons))
   
   # Register error handler
   application.add_error_handler(error_handler)
   
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
