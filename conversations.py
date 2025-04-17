from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters
)
import logging
import asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for the conversation
CHOOSE_ACTION, MAKE, MODEL, YEAR, PRICE, LOCATION, ADVANCED, FUEL, TRANSMISSION, CONFIRM = range(10)

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

# Fuel type options
FUEL_OPTIONS = [
    ['Petrol', 'Diesel', 'Hybrid'],
    ['Electric', 'Any']
]

# Transmission options
TRANSMISSION_OPTIONS = [
    ['Automatic', 'Manual', 'Any']
]

# Advanced options
ADVANCED_OPTIONS = [
    ['Set Fuel Type', 'Set Transmission'],
    ['Skip Advanced Options']
]

# Helper for loading animation
async def loading_animation(update: Update, message_text: str, final_text: str):
    """Display a simple loading animation with dots."""
    loading_message = await update.message.reply_text(f"{message_text}...")
    
    for _ in range(3):
        await asyncio.sleep(0.7)
        await loading_message.edit_text(f"{message_text}...")
        await asyncio.sleep(0.7)
        await loading_message.edit_text(f"{message_text}..")
        await asyncio.sleep(0.7)
        await loading_message.edit_text(f"{message_text}.")
        await asyncio.sleep(0.7)
        await loading_message.edit_text(f"{message_text}")
    
    await loading_message.edit_text(final_text)

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
    context.user_data['setup_step'] = 1
    context.user_data['total_steps'] = 5
    
    # Get existing car preferences for this user
    sheets_manager = context.bot_data['sheets_manager']
    existing_preferences = sheets_manager.get_car_preferences(user.id)
    
    if existing_preferences:
        # User already has preferences
        active_count = len(existing_preferences)
        reply_keyboard = [['Set New Car', 'View Current', 'Cancel']]
        await update.message.reply_text(
            f"You currently have {active_count} active car preference{'s' if active_count > 1 else ''}. What would you like to do?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return CHOOSE_ACTION
    else:
        # New user, start with car make
        await update.message.reply_text(
            "*AutoSniper Car Preferences Setup*\n\n"
            f"Step 1/{context.user_data['total_steps']}: Car Make\n\n"
            "Let's set up your car preferences. What make of car are you interested in?",
            parse_mode="MARKDOWN",
            reply_markup=ReplyKeyboardMarkup(CAR_MAKES, one_time_keyboard=True)
        )
        return MAKE

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's choice of action regarding car preferences."""
    choice = update.message.text
    
    if choice == 'Set New Car':
        context.user_data['setup_step'] = 1
        context.user_data['total_steps'] = 5
        
        await update.message.reply_text(
            "*AutoSniper Car Preferences Setup*\n\n"
            f"Step 1/{context.user_data['total_steps']}: Car Make\n\n"
            "What make of car are you interested in?",
            parse_mode="MARKDOWN",
            reply_markup=ReplyKeyboardMarkup(CAR_MAKES, one_time_keyboard=True)
        )
        return MAKE
    
    elif choice == 'View Current':
        # Get user's current preferences and display them
        sheets_manager = context.bot_data['sheets_manager']
        preferences = sheets_manager.get_car_preferences(update.effective_user.id)
        
        if preferences:
            await update.message.reply_text(
                "*Your Current Car Preferences*\n"
                "───────────────────────",
                parse_mode="MARKDOWN"
            )
            
            for i, car in enumerate(preferences, 1):
                # Create a nicely formatted card for each preference
                fuel_type = car.get('fuel_type', 'Any')
                transmission = car.get('transmission', 'Any')
                
                await update.message.reply_text(
                    f"*Preference #{i}*\n"
                    "───────────────────────\n"
                    f"*Make:* {car['make']}\n"
                    f"*Model:* {car['model']}\n"
                    f"*Year Range:* {car['min_year']} to {car['max_year']}\n"
                    f"*Price Range:* {car['min_price']} to {car['max_price']}\n"
                    f"*Location:* {car['location']}\n"
                    f"*Fuel Type:* {fuel_type}\n"
                    f"*Transmission:* {transmission}\n"
                    "───────────────────────",
                    parse_mode="MARKDOWN"
                )
            
            await update.message.reply_text(
                "Use /mycars to add or update your preferences.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            context.user_data['setup_step'] = 1
            context.user_data['total_steps'] = 5
            
            await update.message.reply_text(
                "You don't have any active car preferences. Let's set some up!\n\n"
                "*AutoSniper Car Preferences Setup*\n\n"
                f"Step 1/{context.user_data['total_steps']}: Car Make\n\n"
                "What make of car are you interested in?",
                parse_mode="MARKDOWN",
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
            "*AutoSniper Car Preferences Setup*\n\n"
            f"Step 1/{context.user_data['total_steps']}: Car Make\n\n"
            "Please specify the make of car you're interested in:",
            parse_mode="MARKDOWN"
        )
        return MODEL
    
    # Increment step counter
    context.user_data['setup_step'] = 2
    
    # Now ask for model
    await update.message.reply_text(
        "*AutoSniper Car Preferences Setup*\n\n"
        f"Step 2/{context.user_data['total_steps']}: Car Model\n\n"
        f"You selected {text}. What model are you interested in?",
        parse_mode="MARKDOWN"
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
        context.user_data['setup_step'] = 2
        
        await update.message.reply_text(
            "*AutoSniper Car Preferences Setup*\n\n"
            f"Step 2/{context.user_data['total_steps']}: Car Model\n\n"
            f"What model of {text} are you interested in?",
            parse_mode="MARKDOWN"
        )
        return MODEL
    
    # Save the car model
    context.user_data['car_preferences']['model'] = text
    
    # Increment step counter
    context.user_data['setup_step'] = 3
    
    # Now ask for year range
    await update.message.reply_text(
        "*AutoSniper Car Preferences Setup*\n\n"
        f"Step 3/{context.user_data['total_steps']}: Year Range\n\n"
        "What year range are you interested in?",
        parse_mode="MARKDOWN",
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
            "*AutoSniper Car Preferences Setup*\n\n"
            f"Step 3/{context.user_data['total_steps']}: Year Range\n\n"
            "Please enter your custom year range in format 'MIN-MAX' (e.g., '2015-2020').\n"
            "Or simply enter a single year (e.g., '2017') if you're looking for a specific year.",
            parse_mode="MARKDOWN"
        )
        # Return to the same state to get the custom input
        return YEAR
    
    # Check if this is a custom year input (after selecting Custom)
    if 'car_preferences' in context.user_data and 'year_range' not in context.user_data['car_preferences']:
        try:
            # Try to parse as a range (e.g., "2015-2020")
            if '-' in text:
                year_parts = text.split('-')
                min_year = int(year_parts[0].strip())
                max_year = int(year_parts[1].strip())
                year_text = f"{min_year}-{max_year}"
            else:
                # Try to parse as a single year (e.g., "2017")
                year = int(text.strip())
                min_year = year
                max_year = year
                year_text = f"{year}"
                
            # Save to context
            context.user_data['car_preferences']['year_range'] = year_text
            context.user_data['car_preferences']['min_year'] = min_year
            context.user_data['car_preferences']['max_year'] = max_year
            
            # Increment step counter
            context.user_data['setup_step'] = 4
            
            # Move to price range
            await update.message.reply_text(
                "*AutoSniper Car Preferences Setup*\n\n"
                f"Step 4/{context.user_data['total_steps']}: Price Range\n\n"
                f"Looking for cars from {year_text}. What price range are you interested in?",
                parse_mode="MARKDOWN",
                reply_markup=ReplyKeyboardMarkup(PRICE_OPTIONS, one_time_keyboard=True)
            )
            return PRICE
        except ValueError:
            # Not a valid year format
            await update.message.reply_text(
                "*AutoSniper Car Preferences Setup*\n\n"
                f"Step 3/{context.user_data['total_steps']}: Year Range\n\n"
                "That doesn't seem to be a valid year or year range. "
                "Please enter a year (e.g., '2017') or year range (e.g., '2015-2020'):",
                parse_mode="MARKDOWN"
            )
            return YEAR
    
    # Save the year range for preset options
    context.user_data['car_preferences']['year_range'] = text
    
    # Also parse and save min_year and max_year for preset options
    if 'Present' in text:
        year_parts = text.split('-')
        min_year = int(year_parts[0])
        max_year = 2025  # Current year as "Present"
    else:
        year_parts = text.split('-')
        min_year = int(year_parts[0])
        max_year = int(year_parts[1])
    
    context.user_data['car_preferences']['min_year'] = min_year
    context.user_data['car_preferences']['max_year'] = max_year
    
    # Increment step counter
    context.user_data['setup_step'] = 4
    
    # Move to price range
    await update.message.reply_text(
        "*AutoSniper Car Preferences Setup*\n\n"
        f"Step 4/{context.user_data['total_steps']}: Price Range\n\n"
        f"Looking for cars from {text}. What price range are you interested in?",
        parse_mode="MARKDOWN",
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
    
    # Parse the price range
    if '+' in text:
        # Handle format like "€30,000+"
        price_parts = text.replace(',', '').replace('€', '').replace('£', '')
        price_parts = price_parts.split('+')[0]
        min_price = int(price_parts)
        max_price = 9999999
    else:
        # Handle format like "€15,000-20,000"
        price_parts = text.replace(',', '').replace('€', '').replace('£', '')
        price_parts = price_parts.split('-')
        min_price = int(price_parts[0])
        max_price = int(price_parts[1])
    
    context.user_data['car_preferences']['min_price'] = min_price
    context.user_data['car_preferences']['max_price'] = max_price
    
    # Increment step counter
    context.user_data['setup_step'] = 5
    
    # Move to location
    await update.message.reply_text(
        "*AutoSniper Car Preferences Setup*\n\n"
        f"Step 5/{context.user_data['total_steps']}: Location\n\n"
        "Which location are you interested in?",
        parse_mode="MARKDOWN",
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
    
    # Check if user selected an "Other" location option
    if text == 'Ireland: Other' or text == 'UK: Other':
        country = text.split(':')[0]  # Extract country part (Ireland or UK)
        await update.message.reply_text(
            "*AutoSniper Car Preferences Setup*\n\n"
            f"Step 5/{context.user_data['total_steps']}: Location\n\n"
            f"Please specify which area in {country} you're interested in:",
            parse_mode="MARKDOWN"
        )
        # Stay in the same state to get the specific location
        return LOCATION
    
    # Save the location
    context.user_data['car_preferences']['location'] = text
    
    # Ask if user wants to set advanced options
    if 'total_steps' in context.user_data and context.user_data['total_steps'] == 5:
        # If we haven't already included advanced steps, ask if user wants them
        await update.message.reply_text(
            "*AutoSniper Car Preferences Setup*\n\n"
            "Would you like to set advanced options like fuel type and transmission?",
            parse_mode="MARKDOWN",
            reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
        )
        return ADVANCED
    else:
        # If advanced steps are already included, go to confirmation
        prefs = context.user_data['car_preferences']
        
        # Build a nicely formatted summary card
        summary = (
            "*Preference Summary*\n"
            "───────────────────────\n"
            f"*Make:* {prefs.get('make', 'Not specified')}\n"
            f"*Model:* {prefs.get('model', 'Not specified')}\n"
            f"*Year Range:* {prefs.get('year_range', 'Not specified')}\n"
            f"*Price Range:* {prefs.get('price_range', 'Not specified')}\n"
            f"*Location:* {prefs.get('location', 'Not specified')}\n"
        )
        
        # Add advanced options if set
        if 'fuel_type' in prefs:
            summary += f"*Fuel Type:* {prefs.get('fuel_type')}\n"
        if 'transmission' in prefs:
            summary += f"*Transmission:* {prefs.get('transmission')}\n"
        
        summary += "───────────────────────\n\nIs this correct?"
        
        await update.message.reply_text(
            summary,
            parse_mode="MARKDOWN",
            reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
        )
        return CONFIRM

async def advanced_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle advanced options selection."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    if text.lower() == 'yes':
        # Update total steps to include advanced options
        context.user_data['total_steps'] = 7
        context.user_data['setup_step'] = 6
        
        # Ask for fuel type
        await update.message.reply_text(
            "*AutoSniper Car Preferences Setup*\n\n"
            f"Step 6/{context.user_data['total_steps']}: Fuel Type\n\n"
            "What fuel type are you interested in?",
            parse_mode="MARKDOWN",
            reply_markup=ReplyKeyboardMarkup(FUEL_OPTIONS, one_time_keyboard=True)
        )
        return FUEL
    else:
        # Skip advanced options, go to confirmation
        prefs = context.user_data['car_preferences']
        
        # Build a nicely formatted summary card
        summary = (
            "*Preference Summary*\n"
            "───────────────────────\n"
            f"*Make:* {prefs.get('make', 'Not specified')}\n"
            f"*Model:* {prefs.get('model', 'Not specified')}\n"
            f"*Year Range:* {prefs.get('year_range', 'Not specified')}\n"
            f"*Price Range:* {prefs.get('price_range', 'Not specified')}\n"
            f"*Location:* {prefs.get('location', 'Not specified')}\n"
            "───────────────────────\n\nIs this correct?"
        )
        
        await update.message.reply_text(
            summary,
            parse_mode="MARKDOWN",
            reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
        )
        return CONFIRM

async def fuel_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle fuel type selection."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Save fuel type
    context.user_data['car_preferences']['fuel_type'] = text
    
    # Increment step counter
    context.user_data['setup_step'] = 7
    
    # Ask for transmission
    await update.message.reply_text(
        "*AutoSniper Car Preferences Setup*\n\n"
        f"Step 7/{context.user_data['total_steps']}: Transmission\n\n"
        "What transmission type are you interested in?",
        parse_mode="MARKDOWN",
        reply_markup=ReplyKeyboardMarkup(TRANSMISSION_OPTIONS, one_time_keyboard=True)
    )
    return TRANSMISSION

async def transmission_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle transmission type selection."""
    text = update.message.text
    
    if text.lower() == 'cancel':
        await update.message.reply_text(
            "Car preference setup cancelled. You can restart anytime with /mycars.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Save transmission type
    context.user_data['car_preferences']['transmission'] = text
    
    # Show summary and ask for confirmation
    prefs = context.user_data['car_preferences']
    
    # Build a nicely formatted summary card
    summary = (
        "*Preference Summary*\n"
        "───────────────────────\n"
        f"*Make:* {prefs.get('make', 'Not specified')}\n"
        f"*Model:* {prefs.get('model', 'Not specified')}\n"
        f"*Year Range:* {prefs.get('year_range', 'Not specified')}\n"
        f"*Price Range:* {prefs.get('price_range', 'Not specified')}\n"
        f"*Location:* {prefs.get('location', 'Not specified')}\n"
        f"*Fuel Type:* {prefs.get('fuel_type', 'Not specified')}\n"
        f"*Transmission:* {prefs.get('transmission', 'Not specified')}\n"
        "───────────────────────\n\nIs this correct?"
    )
    
    await update.message.reply_text(
        summary,
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
        # Show loading animation
        await loading_animation(
            update,
            "Saving your preferences",
            "Preferences saved successfully!"
        )
        
        # Save to Google Sheets
        sheets_manager = context.bot_data['sheets_manager']
        prefs = context.user_data['car_preferences']
        
        # Get directly stored min/max year and price values
        min_year = prefs.get('min_year', 0)
        max_year = prefs.get('max_year', 9999)
        min_price = prefs.get('min_price', 0)
        max_price = prefs.get('max_price', 9999999)
        
        # Add optional params
        fuel_type = prefs.get('fuel_type', 'Any')
        transmission = prefs.get('transmission', 'Any')
        
        success = sheets_manager.add_car_preferences(
            user_id=update.effective_user.id,
            make=prefs.get('make', ''),
            model=prefs.get('model', ''),
            min_year=min_year,
            max_year=max_year,
            min_price=min_price,
            max_price=max_price,
            location=prefs.get('location', ''),
            fuel_type=fuel_type,
            transmission=transmission
        )
        
        if success:
            # Show sample alert based on preferences
            make = prefs.get('make', 'car')
            model = prefs.get('model', '')
            car_name = f"{make} {model}".strip()
            
            # Generate a sample alert for the user
            sample_alert = (
                "*Here's a sample of alerts you'll receive:*\n\n"
                "─────────────────────\n"
                "*A+ DEAL ALERT*\n\n"
                f"*{car_name}*\n"
                f"Price: £14,500 (Market avg: £19,200)\n"
                f"72,000 miles | {fuel_type} | {transmission}\n"
                f"Location: {prefs.get('location', 'Manchester')}\n"
                f"Full service history | Valid MOT\n"
                "*Score: A+* (24% below market)\n\n"
                "Suggested message: \"Hi, is your car still available? I can view it today if possible.\"\n\n"
                "[View Listing](https://example.com/listing)\n"
                "─────────────────────"
            )
            
            await update.message.reply_text(
                "Your car preferences have been saved. AutoSniper will now start looking "
                "for deals matching your criteria.\n\n"
                f"{sample_alert}\n\n"
                "You'll receive alerts when we find cars that match your preferences. "
                "You can update your preferences anytime by using the /mycars command.",
                parse_mode="MARKDOWN",
                disable_web_page_preview=True,
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
        if 'setup_step' in context.user_data:
            del context.user_data['setup_step']
        if 'total_steps' in context.user_data:
            del context.user_data['total_steps']
            
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
    if 'setup_step' in context.user_data:
        del context.user_data['setup_step']
    if 'total_steps' in context.user_data:
        del context.user_data['total_steps']
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
            ADVANCED: [MessageHandler(filters.TEXT & ~filters.COMMAND, advanced_options)],
            FUEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuel_type)],
            TRANSMISSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, transmission_type)],
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
