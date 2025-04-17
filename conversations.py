from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters
)
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for the conversation
CHOOSE_ACTION, MAKE, MODEL, YEAR, PRICE, LOCATION, CONFIRM = range(7)

# Common car makes for keyboard suggestions
CAR_MAKES = [
    ['BMW', 'Mercedes', 'Audi'], 
    ['Toyota', 'Honda', 'Nissan'],
    ['Ford', 'Volkswagen', 'Hyundai'],
    ['Other']
]

# Location options
LOCATIONS = [
    ['Ireland: Dublin', 'Ireland: Cork', 'Ireland: Galway'],
    ['Ireland: Other', 'UK: London', 'UK: Manchester'],
    ['UK: Other']
]

# Year shortcuts
YEAR_OPTIONS = [
    ['2020-Present', '2015-2020', '2010-2015'],
    ['2005-2010', '2000-2005', 'Custom']
]

# Price range shortcuts
PRICE_OPTIONS = [
    ['€0-5,000', '€5,000-10,000', '€10,000-15,000'],
    ['€15,000-20,000', '€20,000-30,000', '€30,000+'],
    ['£0-5,000', '£5,000-10,000', '£10,000-15,000'],
    ['£15,000-20,000', '£20,000-30,000', '£30,000+']
]

async def start_car_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the car preferences conversation."""
    user = update.effective_user
    
    # Check if sheets_manager is available in the context
    if not context.bot_data.get('sheets_manager'):
        await update.message.reply_text(
            "Sorry, the bot is not properly configured to save preferences right now. "
            "Please try again later or contact support."
        )
        return ConversationHandler.END
    
    # Initialize user data in context
    context.user_data['car_preferences'] = {}
    
    # Get existing car preferences for this user
    sheets_manager = context.bot_data['sheets_manager']
    existing_preferences = sheets_manager.get_car_preferences(user.id)
    
    if existing_preferences:
        # User already has preferences
        reply_keyboard = [['Set New Car', 'View Current', 'Cancel']]
        await update.message.reply_text(
            "I see you already have car preferences set up. What would you like to do?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return CHOOSE_ACTION
    else:
        # New user, start with car make
        await update.message.reply_text(
            "Let's set up your car preferences! I'll ask you a series of questions "
            "to understand what kind of car you're looking for.\n\n"
            "You can type 'cancel' at any point to stop the process.\n\n"
            "First, what make of car are you interested in?",
            reply_markup=ReplyKeyboardMarkup(CAR_MAKES, one_time_keyboard=True)
        )
        return MAKE

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's choice of action regarding car preferences."""
    choice = update.message.text
    
    if choice == 'Set New Car':
        await update.message.reply_text(
            "Great! Let's set up new car preferences.\n\n"
            "What make of car are you interested in?",
            reply_markup=ReplyKeyboardMarkup(CAR_MAKES, one_time_keyboard=True)
        )
        return MAKE
    
    elif choice == 'View Current':
        # Get user's current preferences and display them
        sheets_manager = context.bot_data['sheets_manager']
        preferences = sheets_manager.get_car_preferences(update.effective_user.id)
        
        if preferences:
            for car in preferences:
                await update.message.reply_text(
                    f"🚗 *Your Current Car Preferences*\n\n"
                    f"Make: {car['make']}\n"
                    f"Model: {car['model']}\n"
                    f"Year Range: {car['min_year']} to {car['max_year']}\n"
                    f"Price Range: {car['min_price']} to {car['max_price']}\n"
                    f"Location: {car['location']}\n\n"
                    f"Use /mycars to update these preferences.",
                    parse_mode="MARKDOWN",
                    reply_markup=ReplyKeyboardRemove()
                )
        else:
            await update.message.reply_text(
                "You don't seem to have any active car preferences. Let's set some up!\n\n"
                "What make of car are you interested in?",
                reply_markup=ReplyKeyboardMarkup(CAR_MAKES, one_time_keyboard=True)
            )
            return MAKE
        
        return ConversationHandler.END
    
    elif choice == 'Cancel':
        await update.message.reply_text(
            "Alright, we'll keep your existing preferences. You can use /mycars "
            "anytime to view or update them.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    else:
        await update.message.reply_text(
            "I didn't understand that choice. Please select one of the options below.",
            reply_markup=ReplyKeyboardMarkup([['Set New Car', 'View Current', 'Cancel']], one_time_keyboard=True)
        )
        return CHOOSE_ACTION

async def car_make(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle car make selection."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Save the car make
    context.user_data['car_preferences']['make'] = text
    
    if text == 'Other':
        await update.message.reply_text(
            "Please type in the make of car you're interested in:"
        )
        return MODEL
    
    # Now ask for model
    await update.message.reply_text(
        f"Great! You selected {text}. Now, what model are you interested in?\n\n"
        f"Please type the model name (e.g., '3 Series', 'Corolla', etc.)"
    )
    return MODEL

async def car_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle car model input."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # If the user typed 'Other' for make, now we capture the actual make
    if context.user_data['car_preferences'].get('make') == 'Other':
        context.user_data['car_preferences']['make'] = text
        await update.message.reply_text(
            f"Thanks! Now, what model of {text} are you interested in?\n\n"
            f"Please type the model name (e.g., '3 Series', 'Corolla', etc.)"
        )
        return MODEL
    
    # Save the car model
    context.user_data['car_preferences']['model'] = text
    
    # Now ask for year range
    await update.message.reply_text(
        "What year range are you interested in?",
        reply_markup=ReplyKeyboardMarkup(YEAR_OPTIONS, one_time_keyboard=True)
    )
    return YEAR

async def year_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle year range input."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Parse the year range
    if text == 'Custom':
        await update.message.reply_text(
            "Please enter your custom year range in format 'MIN-MAX' (e.g., '2015-2020'):"
        )
        # Return to the same state to get the custom input
        return YEAR
    
    # Save the year range
    context.user_data['car_preferences']['year_range'] = text
    
    # Move to price range
    await update.message.reply_text(
        "What price range are you interested in?",
        reply_markup=ReplyKeyboardMarkup(PRICE_OPTIONS, one_time_keyboard=True)
    )
    return PRICE
    # Save the year range
    context.user_data['car_preferences']['year_range'] = text
    
    # Move to price range
    await update.message.reply_text(
        "What price range are you interested in?",
        reply_markup=ReplyKeyboardMarkup(PRICE_OPTIONS, one_time_keyboard=True)
    )
    return PRICE

async def price_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle price range input."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Save the price range
    context.user_data['car_preferences']['price_range'] = text
    
    # Move to location
    await update.message.reply_text(
        "Finally, which location are you interested in?",
        reply_markup=ReplyKeyboardMarkup(LOCATIONS, one_time_keyboard=True)
    )
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location input."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Save the location
    context.user_data['car_preferences']['location'] = text
    
    # Show summary and ask for confirmation
    prefs = context.user_data['car_preferences']
    await update.message.reply_text(
        f"🚗 *Here's a summary of your preferences:*\n\n"
        f"Make: {prefs.get('make', 'Not specified')}\n"
        f"Model: {prefs.get('model', 'Not specified')}\n"
        f"Year Range: {prefs.get('year_range', 'Not specified')}\n"
        f"Price Range: {prefs.get('price_range', 'Not specified')}\n"
        f"Location: {prefs.get('location', 'Not specified')}\n\n"
        f"Is this correct? (Yes/No)",
        parse_mode="MARKDOWN",
        reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
    )
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation of car preferences."""
    text = update.message.text.lower()
    
    if text == 'cancel' or text == 'no':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        # Clear user data
        if 'car_preferences' in context.user_data:
            del context.user_data['car_preferences']
        return ConversationHandler.END
    
    if text == 'yes':
        # Save to Google Sheets (simplified for now)
        sheets_manager = context.bot_data['sheets_manager']
        prefs = context.user_data['car_preferences']
        
        # Parse year range 
        year_range = prefs.get('year_range', '')
        min_year = 0
        max_year = 9999
        
        if 'Present' in year_range:
            year_parts = year_range.split('-')
            min_year = int(year_parts[0])
            max_year = 2025  # Current year as "Present"
        elif '-' in year_range:
            year_parts = year_range.split('-')
            min_year = int(year_parts[0])
            max_year = int(year_parts[1])
        
        # Parse price range
        price_range = prefs.get('price_range', '')
        min_price = 0
        max_price = 9999999
        
        if '+' in price_range:
            # Handle format like "€30,000+"
            price_parts = price_range.replace(',', '').replace('€', '').replace('£', '')
            price_parts = price_parts.split('+')[0]
            min_price = int(price_parts)
            max_price = 9999999
        elif '-' in price_range:
            # Handle format like "€15,000-20,000"
            price_parts = price_range.replace(',', '').replace('€', '').replace('£', '')
            price_parts = price_parts.split('-')
            min_price = int(price_parts[0])
            max_price = int(price_parts[1])
        
        success = sheets_manager.add_car_preferences(
            user_id=update.effective_user.id,
            make=prefs.get('make', ''),
            model=prefs.get('model', ''),
            min_year=min_year,
            max_year=max_year,
            min_price=min_price,
            max_price=max_price,
            location=prefs.get('location', '')
        )
        
        if success:
            await update.message.reply_text(
                "Perfect! Your car preferences have been saved. AutoSniper will now start looking "
                "for deals matching your criteria.\n\n"
                "You'll receive alerts when we find cars that match your preferences. "
                "You can update your preferences anytime by using the /mycars command.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                "There was an error saving your preferences. Please try again later or contact support.",
                reply_markup=ReplyKeyboardRemove()
            )
        
        # Clear user data
        if 'car_preferences' in context.user_data:
            del context.user_data['car_preferences']
        return ConversationHandler.END
    
    # If response wasn't yes or no
    await update.message.reply_text(
        "Please confirm if the preferences are correct by selecting Yes or No.",
        reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
    )
    return CONFIRM

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "Car preference setup cancelled. You can restart anytime with /mycars.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Clear only car preferences data, not all user data
    if 'car_preferences' in context.user_data:
        del context.user_data['car_preferences']
    return ConversationHandler.END

def get_car_preferences_conversation(sheets_manager):
    """Return a ConversationHandler for collecting car preferences."""
    
    return ConversationHandler(
        entry_points=[CommandHandler("mycars", start_car_setup)],
        states={
            CHOOSE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
            MAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_make)],
            MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_model)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, year_range)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_range)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex('^[Cc]ancel$'), cancel)
        ],
        name="car_preferences",
        persistent=False,
        allow_reentry=True
    )
