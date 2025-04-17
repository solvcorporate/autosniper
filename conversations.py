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
MAKE, MODEL, YEAR, PRICE, LOCATION, CONFIRM = range(6)

async def start_car_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the car preferences conversation."""
    await update.message.reply_text("Let's set up your car preferences! What make are you interested in?")
    return MAKE

async def car_make(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle car make selection."""
    context.user_data['make'] = update.message.text
    await update.message.reply_text(f"Got it! You're looking for a {update.message.text}. What model?")
    return MODEL

async def car_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle car model input."""
    context.user_data['model'] = update.message.text
    await update.message.reply_text("What year range? (e.g., '2015-2020')")
    return YEAR

async def year_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle year range input."""
    context.user_data['year_range'] = update.message.text
    await update.message.reply_text("What price range? (e.g., '10000-20000')")
    return PRICE

async def price_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle price range input."""
    context.user_data['price_range'] = update.message.text
    await update.message.reply_text("Which location? (e.g., 'Ireland: Dublin')")
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location input."""
    context.user_data['location'] = update.message.text
    
    # Show summary and ask for confirmation
    await update.message.reply_text(
        f"Here's a summary of your preferences:\n\n"
        f"Make: {context.user_data.get('make')}\n"
        f"Model: {context.user_data.get('model')}\n"
        f"Year Range: {context.user_data.get('year_range')}\n"
        f"Price Range: {context.user_data.get('price_range')}\n"
        f"Location: {context.user_data.get('location')}\n\n"
        f"Is this correct? (Yes/No)",
        reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
    )
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation of car preferences."""
    text = update.message.text.lower()
    
    if text == 'yes':
        # Here we would save to Google Sheets, but for now just acknowledge
        await update.message.reply_text(
            "Perfect! Your car preferences have been saved.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "Let's try again. Use /mycars to restart.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("Setup cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def get_car_preferences_conversation(sheets_manager):
    """Return a ConversationHandler for collecting car preferences."""
    
    return ConversationHandler(
        entry_points=[CommandHandler("mycars", start_car_setup)],
        states={
            MAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_make)],
            MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_model)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, year_range)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_range)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="car_preferences",
        persistent=False,
        allow_reentry=True
    )
