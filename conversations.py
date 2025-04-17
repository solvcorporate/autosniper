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
CHOOSE_ACTION, MAKE, MODEL, MIN_YEAR, MAX_YEAR, MIN_PRICE, MAX_PRICE, LOCATION, CONFIRM = range(9)

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
    ['£15,000-20,000', '£20,000-30,000', '£30,000+'],
    ['Custom']
]

# Helper functions
def extract_year_range(year_option):
    """Extract min and max year from a year option."""
    if year_option == 'Custom':
        return None, None
    
    if year_option == '2020-Present':
        return 2020, 2025  # Assuming "present" means current year or newer
    
    years = year_option.split('-')
    return int(years[0]), int(years[1])

def extract_price_range(price_option):
    """Extract min and max price from a price option."""
    if price_option == 'Custom':
        return None, None
        
    if price_option.endswith('+'):
        currency = price_option[0]
        min_price = price_option[1:].split('+')[0].replace(',', '')
        return int(min_price), 1000000  # Arbitrary high max price
    
    currency = price_option[0]
    prices = price_option[1:].split('-')
    min_price = prices[0].replace(',', '')
    max_price = prices[1].replace(',', '')
    return int(min_price), int(max_price)

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
        "What year range are you interested in? You can select a preset range or choose 'Custom' to specify exact years.",
        reply_markup=ReplyKeyboardMarkup(YEAR_OPTIONS, one_time_keyboard=True)
    )
    return MIN_YEAR

async def min_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle year range selection."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    min_year, max_year = extract_year_range(text)
    
    if min_year and max_year:
        # User selected a preset range
        context.user_data['car_preferences']['min_year'] = min_year
        context.user_data['car_preferences']['max_year'] = max_year
        
        # Skip to price range
        await update.message.reply_text(
            f"Great! Looking for cars from {min_year} to {max_year}.\n\n"
            f"Now, what price range are you interested in?",
            reply_markup=ReplyKeyboardMarkup(PRICE_OPTIONS, one_time_keyboard=True)
        )
        return MIN_PRICE
    else:
        # User wants to input custom range
        await update.message.reply_text(
            "Please enter the minimum year you're interested in (e.g., 2015):"
        )
        return MAX_YEAR

async def max_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom minimum year input and ask for maximum year."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Validate year input
    try:
        year = int(text)
        if year < 1900 or year > 2030:
            raise ValueError("Year out of reasonable range")
    except ValueError:
        await update.message.reply_text(
            "That doesn't seem to be a valid year. Please enter a year between 1900 and 2030:"
        )
        return MAX_YEAR
    
    # Save min year
    context.user_data['car_preferences']['min_year'] = year
    
    # Now ask for max year
    await update.message.reply_text(
        f"Thanks! Now, what's the maximum year you're interested in? (Must be {year} or later)"
    )
    return MIN_PRICE

async def min_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle max year input or price range selection."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Check if we're coming from max_year
    if 'max_year' not in context.user_data['car_preferences']:
        try:
            year = int(text)
            min_year = context.user_data['car_preferences']['min_year']
            
            if year < min_year:
                await update.message.reply_text(
                    f"The maximum year must be greater than or equal to the minimum year ({min_year})."
                    f"Please enter a valid maximum year:"
                )
                return MIN_PRICE
            
            context.user_data['car_preferences']['max_year'] = year
            
            # Now move to price range
            await update.message.reply_text(
                f"Great! Looking for cars from {min_year} to {year}.\n\n"
                f"Now, what price range are you interested in?",
                reply_markup=ReplyKeyboardMarkup(PRICE_OPTIONS, one_time_keyboard=True)
            )
            return MAX_PRICE
        except ValueError:
            await update.message.reply_text(
                "That doesn't seem to be a valid year. Please enter a numeric year:"
            )
            return MIN_PRICE
    
    # If we're here, we're handling price range selection
    min_price, max_price = extract_price_range(text)
    
    if min_price and max_price:
        # User selected a preset range
        context.user_data['car_preferences']['min_price'] = min_price
        context.user_data['car_preferences']['max_price'] = max_price
        
        # Move to location
        await update.message.reply_text(
            f"Great! Looking for cars priced between {min_price} and {max_price}.\n\n"
            f"Finally, which location are you interested in?",
            reply_markup=ReplyKeyboardMarkup(LOCATIONS, one_time_keyboard=True)
        )
        return LOCATION
    else:
        # User wants to input custom price range
        await update.message.reply_text(
            "Please enter the minimum price you're interested in (numeric value only, e.g., 5000):"
        )
        return MAX_PRICE

async def max_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom minimum price input and ask for maximum price."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Validate price input
    try:
        price = int(text.replace(',', '').replace('€', '').replace('£', '').strip())
        if price < 0 or price > 10000000:
            raise ValueError("Price out of reasonable range")
    except ValueError:
        await update.message.reply_text(
            "That doesn't seem to be a valid price. Please enter a numeric value (e.g., 5000):"
        )
        return MAX_PRICE
    
    # Save min price
    context.user_data['car_preferences']['min_price'] = price
    
    # Now ask for max price
    await update.message.reply_text(
        f"Thanks! Now, what's the maximum price you're willing to pay? (Must be {price} or higher)"
    )
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle max price input or location selection."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Check if we're coming from max_price
    if 'max_price' not in context.user_data['car_preferences']:
        try:
            price = int(text.replace(',', '').replace('€', '').replace('£', '').strip())
            min_price = context.user_data['car_preferences']['min_price']
            
            if price < min_price:
                await update.message.reply_text(
                    f"The maximum price must be greater than or equal to the minimum price ({min_price})."
                    f"Please enter a valid maximum price:"
                )
                return LOCATION
            
            context.user_data['car_preferences']['max_price'] = price
            
            # Now move to location
            await update.message.reply_text(
                f"Great! Looking for cars priced between {min_price} and {price}.\n\n"
                f"Finally, which location are you interested in?",
                reply_markup=ReplyKeyboardMarkup(LOCATIONS, one_time_keyboard=True)
            )
            return CONFIRM
        except ValueError:
            await update.message.reply_text(
                "That doesn't seem to be a valid price. Please enter a numeric value (e.g., 20000):"
            )
            return LOCATION
    
    # If we're here, we're handling location selection
    context.user_data['car_preferences']['location'] = text
    
    # Show summary and ask for confirmation
    prefs = context.user_data['car_preferences']
    await update.message.reply_text(
        f"🚗 *Here's a summary of your preferences:*\n\n"
        f"Make: {prefs.get('make', 'Not specified')}\n"
        f"Model: {prefs.get('model', 'Not specified')}\n"
        f"Year Range: {prefs.get('min_year', 'Any')} to {prefs.get('max_year', 'Any')}\n"
        f"Price Range: {prefs.get('min_price', 'Any')} to {prefs.get('max_price', 'Any')}\n"
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
        # Save preferences to Google Sheets
        sheets_manager = context.bot_data['sheets_manager']
        prefs = context.user_data['car_preferences']
        
        success = sheets_manager.add_car_preferences(
            user_id=update.effective_user.id,
            make=prefs.get('make', ''),
            model=prefs.get('model', ''),
            min_year=prefs.get('min_year', 0),
            max_year=prefs.get('max_year', 9999),
            min_price=prefs.get('min_price', 0),
            max_price=prefs.get('max_price', 9999999),
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

# Create the conversation handler
def get_car_preferences_conversation(sheets_manager):
    """Return a ConversationHandler for collecting car preferences."""
    
    return ConversationHandler(
        entry_points=[CommandHandler("mycars", start_car_setup)],
        states={
            CHOOSE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
            MAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_make)],
            MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_model)],
            MIN_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, min_year)],
            MAX_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_year)],
            MIN_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, min_price)],
            MAX_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_price)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex('^[Cc]ancel), cancel)
        ],
        name="car_preferences",
        persistent=False,
        allow_reentry=True
    )
