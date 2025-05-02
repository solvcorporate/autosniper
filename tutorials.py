"""
Tutorial system for AutoSniper.
This module contains tutorials to help users understand and use AutoSniper effectively.
"""

import logging
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tutorials")

# Tutorial definitions
TUTORIALS = {
    "getting_started": {
        "title": "Getting Started with AutoSniper",
        "description": "Learn the basics of using AutoSniper to find great car deals.",
        "steps": [
            {
                "title": "Welcome to AutoSniper! 👋",
                "content": (
                    "AutoSniper helps you find exceptional car deals by scanning multiple car listing sites 24/7 and "
                    "notifying you when great opportunities appear.\n\n"
                    "This tutorial will show you how to get the most out of AutoSniper."
                ),
                "image": None
            },
            {
                "title": "Setting Up Car Preferences 🚗",
                "content": (
                    "Start by telling AutoSniper what cars you're looking for using the /mycars command.\n\n"
                    "You can specify:\n"
                    "• Make and model\n"
                    "• Price range\n"
                    "• Year range\n"
                    "• Location\n"
                    "• And more!\n\n"
                    "Basic users can have up to 3 active preferences, while Premium users get unlimited preferences."
                ),
                "image": None
            },
            {
                "title": "Understanding Alerts 🚨",
                "content": (
                    "When AutoSniper finds a deal matching your preferences, you'll receive an alert like this:\n\n"
                    "🚨 *A+ DEAL ALERT!* 🚨\n\n"
                    "🚗 *2018 BMW 3 Series*\n"
                    "💰 *Price: £14,500* (Market avg: £19,200)\n"
                    "🔄 72,000 miles | ⛽ Diesel | 📍 Manchester\n\n"
                    "Each alert includes:\n"
                    "• The car's details\n"
                    "• How the price compares to market average\n"
                    "• A grade (A+ to D) indicating how good the deal is\n"
                    "• A direct link to the listing"
                ),
                "image": None
            },
            {
                "title": "Deal Grades Explained 📊",
                "content": (
                    "AutoSniper grades each deal from A+ to D:\n\n"
                    "🏆 *A+*: Exceptional deal (20%+ below market)\n"
                    "🥇 *A*: Great deal (10-20% below market)\n"
                    "🥈 *B*: Good deal (5-10% below market)\n"
                    "🥉 *C*: Fair deal (0-5% below market)\n"
                    "⚠️ *D*: Standard listing (at or above market price)\n\n"
                    "We also consider factors like mileage, documentation completeness, and listing quality."
                ),
                "image": None
            },
            {
                "title": "Premium Features ✨",
                "content": (
                    "Upgrade to Premium for enhanced features:\n\n"
                    "• *Unlimited car preferences*\n"
                    "• *More alert capacity* (10/day vs. 3/day for Basic)\n"
                    "• *Deals of the Week* - curated list of the best deals across all categories\n"
                    "• *Enhanced alerts* with additional data points and analysis\n"
                    "• *Earlier notifications* for competitive advantage\n\n"
                    "Use /subscribe to view subscription options."
                ),
                "image": None
            },
            {
                "title": "Tips for Success 💡",
                "content": (
                    "Here are some tips to get the most out of AutoSniper:\n\n"
                    "• *Set up multiple preferences* to catch more opportunities\n"
                    "• *Act quickly* when you receive an A+ or A grade alert\n"
                    "• *Use the suggested messages* to contact sellers promptly\n"
                    "• *Check Deals of the Week* (Premium) for opportunities outside your preferences\n"
                    "• *Update your preferences* if your requirements change\n\n"
                    "The best deals often disappear within hours!"
                ),
                "image": None
            },
            {
                "title": "Need Help? ❓",
                "content": (
                    "AutoSniper has several ways to get help:\n\n"
                    "• Use /help to see all available commands\n"
                    "• Use /faq to read frequently asked questions\n"
                    "• Use /tutorial anytime to revisit this tutorial\n"
                    "• Contact support at solvcorporate@gmail.com\n\n"
                    "We're here to help you find the best car deals!"
                ),
                "image": None
            }
        ]
    },
    "premium_features": {
        "title": "Premium Features Tutorial",
        "description": "Learn about the exclusive features available to Premium subscribers.",
        "steps": [
            {
                "title": "Premium Features Overview ✨",
                "content": (
                    "Congratulations on your Premium subscription! This tutorial will help you make the most of your "
                    "Premium features.\n\n"
                    "Let's explore what's available to you as a Premium subscriber."
                ),
                "image": None
            },
            {
                "title": "Unlimited Car Preferences 🚗",
                "content": (
                    "As a Premium subscriber, you can create unlimited car preferences.\n\n"
                    "This allows you to:\n"
                    "• Monitor multiple car models simultaneously\n"
                    "• Track different price ranges for the same model\n"
                    "• Set up preferences for different locations\n\n"
                    "Use /mycars to manage your preferences."
                ),
                "image": None
            },
            {
                "title": "Deals of the Week 🏆",
                "content": (
                    "The Deals of the Week feature is exclusive to Premium subscribers.\n\n"
                    "Every week, our algorithm identifies the absolute best deals across all categories, even outside "
                    "your specific preferences.\n\n"
                    "Use /dealsofweek to see the current top deals.\n\n"
                    "For detailed information about a specific deal, use /car_details followed by the number "
                    "(e.g., /car_details 1)."
                ),
                "image": None
            },
            {
                "title": "Enhanced Alerts 📊",
                "content": (
                    "Premium subscribers receive enhanced alerts with additional data points:\n\n"
                    "• Detailed market comparison\n"
                    "• Mileage assessment\n"
                    "• Documentation completeness analysis\n"
                    "• Seller history information (when available)\n"
                    "• Premium badge for easy identification\n\n"
                    "These enhanced details help you make better decisions, faster."
                ),
                "image": None
            },
            {
                "title": "Priority Alerting ⚡",
                "content": (
                    "Premium subscribers receive alerts before Basic users.\n\n"
                    "When a matching listing is found, the alert sequence is:\n"
                    "1. Premium subscribers\n"
                    "2. Basic subscribers\n"
                    "3. Free users\n\n"
                    "This timing advantage can be crucial for securing the best deals, which often sell within hours "
                    "of listing."
                ),
                "image": None
            },
            {
                "title": "Higher Alert Capacity 📈",
                "content": (
                    "Premium subscribers can receive up to 10 alerts per day, compared to:\n"
                    "• 3 alerts for Basic subscribers\n"
                    "• 1 alert for free users\n\n"
                    "This ensures you never miss a great deal, even on busy days with many new listings."
                ),
                "image": None
            },
            {
                "title": "Managing Your Subscription 💳",
                "content": (
                    "You can manage your Premium subscription anytime using the /managesubscription command.\n\n"
                    "This allows you to:\n"
                    "• Check your current subscription status\n"
                    "• See when your subscription renews\n"
                    "• View the features included in your plan\n\n"
                    "Thank you for supporting AutoSniper with your Premium subscription!"
                ),
                "image": None
            }
        ]
    },
    "advanced_search": {
        "title": "Advanced Search Techniques",
        "description": "Learn how to use advanced search features to find specific vehicles.",
        "steps": [
            {
                "title": "Advanced Search Techniques 🔍",
                "content": (
                    "AutoSniper offers powerful advanced search capabilities to help you find exactly what you're "
                    "looking for.\n\n"
                    "This tutorial will show you how to use these features effectively."
                ),
                "image": None
            },
            {
                "title": "Fuel Type Filtering ⛽",
                "content": (
                    "You can specify a preferred fuel type when setting up your car preferences.\n\n"
                    "Options include:\n"
                    "• Petrol\n"
                    "• Diesel\n"
                    "• Hybrid\n"
                    "• Electric\n"
                    "• Any (default)\n\n"
                    "This is especially useful if you have specific requirements or are looking to avoid certain fuel types."
                ),
                "image": None
            },
            {
                "title": "Transmission Preferences 🎮",
                "content": (
                    "You can filter by transmission type:\n\n"
                    "• Manual\n"
                    "• Automatic\n"
                    "• Any (default)\n\n"
                    "This helps ensure you only receive alerts for cars with your preferred transmission."
                ),
                "image": None
            },
            {
                "title": "Location Strategies 📍",
                "content": (
                    "AutoSniper offers flexible location options:\n\n"
                    "• Specific cities (e.g., Dublin, London)\n"
                    "• Regions (e.g., Ireland: Dublin, UK: Manchester)\n"
                    "• Countries (Ireland, UK)\n"
                    "• Any location\n\n"
                    "Pro tip: Setting up multiple preferences with different locations can help you compare prices across regions."
                ),
                "image": None
            },
            {
                "title": "Price Range Optimization 💰",
                "content": (
                    "Setting the right price range is crucial:\n\n"
                    "• Too narrow: You might miss good deals just outside your range\n"
                    "• Too wide: You may receive too many alerts\n\n"
                    "Pro tip: Consider setting up two preferences for the same car:\n"
                    "1. A narrow price range for your ideal budget\n"
                    "2. A wider range to catch exceptional deals\n\n"
                    "Premium subscribers can do this easily with unlimited preferences."
                ),
                "image": None
            },
            {
                "title": "Year Range Strategies 📅",
                "content": (
                    "Year range tips:\n\n"
                    "• Newer models (1-3 years old): Often have warranty remaining\n"
                    "• Mid-range (4-7 years old): Often the best value proposition\n"
                    "• Older models (8+ years): Can offer significant savings\n\n"
                    "Pro tip: For models with major design changes, use specific year ranges to target particular "
                    "generations."
                ),
                "image": None
            },
            {
                "title": "Multiple Model Strategy 🚙",
                "content": (
                    "Instead of focusing on just one model, consider alternatives:\n\n"
                    "For example, if looking for a BMW 3 Series, you might also consider:\n"
                    "• Audi A4\n"
                    "• Mercedes C-Class\n"
                    "• Lexus IS\n\n"
                    "Setting up preferences for multiple similar models increases your chances of finding an exceptional deal."
                ),
                "image": None
            }
        ]
    },
    "troubleshooting": {
        "title": "Troubleshooting & FAQ",
        "description": "Common issues and how to resolve them.",
        "steps": [
            {
                "title": "Common Issues & Solutions 🔧",
                "content": (
                    "This tutorial covers common issues you might encounter while using AutoSniper "
                    "and how to resolve them quickly.\n\n"
                    "Let's troubleshoot the most frequent questions users have."
                ),
                "image": None
            },
            {
                "title": "No Alerts Received 🔕",
                "content": (
                    "If you're not receiving alerts, check:\n\n"
                    "• *Car preferences*: Make sure you've set up preferences with /mycars\n"
                    "• *Alert limits*: Free users (1/day), Basic (3/day), Premium (10/day)\n"
                    "• *Notification settings*: Ensure Telegram notifications are enabled\n"
                    "• *Bot status*: Try sending /start to verify the bot is responding\n\n"
                    "Remember: AutoSniper only sends alerts when matching cars are found. If your criteria are very specific, it may take longer to find matches."
                ),
                "image": None
            },
            {
                "title": "Car Setup Issues 🚗",
                "content": (
                    "If you're having trouble setting up car preferences:\n\n"
                    "• Type 'cancel' at any point to reset the setup process\n"
                    "• For make/model, try using common spellings (e.g., 'BMW' not 'B.M.W.')\n"
                    "• Price and year ranges must use numbers only\n"
                    "• Try selecting from the suggested options when available\n\n"
                    "You can always view your current preferences with /mycars"
                ),
                "image": None
            },
            {
                "title": "Subscription Problems 💳",
                "content": (
                    "For subscription-related issues:\n\n"
                    "• Check your current status with /managesubscription\n"
                    "• If payment was successful but subscription isn't active, try /start\n"
                    "• For payment failures, retry with /subscribe\n"
                    "• Allow a few minutes for your subscription to activate after payment\n\n"
                    "If problems persist, contact support at solvcorporate@gmail.com with details of the issue."
                ),
                "image": None
            },
            {
                "title": "Command Not Working ⚠️",
                "content": (
                    "If commands aren't responding correctly:\n\n"
                    "• Ensure you're typing the command correctly with the '/' prefix\n"
                    "• Check if the bot responded with an error message\n"
                    "• Try /start to reset your conversation with the bot\n"
                    "• For Premium commands, verify your subscription status\n\n"
                    "Some commands may be temporarily unavailable during maintenance."
                ),
                "image": None
            },
            {
                "title": "Missed a Great Deal? ⏱️",
                "content": (
                    "If you missed out on a deal:\n\n"
                    "• Check alerts promptly - the best deals can go very quickly\n"
                    "• Consider upgrading to Premium for priority notifications\n"
                    "• Make sure your phone notifications for Telegram are enabled\n"
                    "• Set up more flexible price/year ranges to catch more opportunities\n\n"
                    "Premium users: Use /dealsofweek for additional opportunities."
                ),
                "image": None
            },
            {
                "title": "Contact Support 📞",
                "content": (
                    "If you're still having issues:\n\n"
                    "• Email: solvcorporate@gmail.com\n"
                    "• Include your Telegram username\n"
                    "• Describe the issue in detail\n"
                    "• Mention any error messages received\n"
                    "• Screenshot the problem if possible\n\n"
                    "Our support team typically responds within 24 hours."
                ),
                "image": None
            }
        ]
    }
}

class TutorialManager:
    """Manager for handling user tutorials."""
    
    def __init__(self, sheets_manager=None):
        """Initialize the tutorial manager.
        
        Args:
            sheets_manager: SheetsManager instance for tracking progress
        """
        self.logger = logging.getLogger("tutorials.manager")
        self.sheets_manager = sheets_manager
    
    async def start_tutorial(self, update: Update, context: ContextTypes.DEFAULT_TYPE, tutorial_id: str) -> None:
        """Start a specific tutorial.
        
        Args:
            update: Telegram update
            context: Context
            tutorial_id: ID of the tutorial to start
        """
        if tutorial_id not in TUTORIALS:
            await update.message.reply_text(
                "Sorry, that tutorial is not available. Please try another tutorial."
            )
            return
        
        # Get the tutorial
        tutorial = TUTORIALS[tutorial_id]
        
        # Set up the tutorial in user_data
        context.user_data['tutorial'] = {
            'id': tutorial_id,
            'current_step': 0,
            'total_steps': len(tutorial['steps'])
        }
        
        # Record that the user started this tutorial
        if self.sheets_manager:
            try:
                user_id = update.effective_user.id
                # Track tutorial start in sheets - implementation depends on your structure
                # self.sheets_manager.update_tutorial_started(user_id, tutorial_id)
                self.logger.info(f"User {user_id} started tutorial: {tutorial_id}")
            except Exception as e:
                self.logger.error(f"Error tracking tutorial start: {e}")
        
        # Show the first step
        await self.show_tutorial_step(update, context)
    
    async def show_tutorial_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show the current tutorial step.
        
        Args:
            update: Telegram update
            context: Context
        """
        # Check if there's an active tutorial
        if 'tutorial' not in context.user_data:
            await update.message.reply_text(
                "No active tutorial. Use /tutorial to start one."
            )
            return
        
        # Get tutorial data
        tutorial_data = context.user_data['tutorial']
        tutorial_id = tutorial_data['id']
        current_step = tutorial_data['current_step']
        
        # Get the tutorial and step
        tutorial = TUTORIALS[tutorial_id]
        step = tutorial['steps'][current_step]
        
        # Create navigation buttons
        keyboard = []
        
        # Show appropriate navigation buttons
        if current_step > 0:
            keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"tutorial_prev"))
        
        if current_step < tutorial_data['total_steps'] - 1:
            keyboard.append(InlineKeyboardButton("Next ➡️", callback_data=f"tutorial_next"))
        else:
            keyboard.append(InlineKeyboardButton("Finish 🏁", callback_data=f"tutorial_finish"))
        
        # Add exit button
        keyboard = [keyboard, [InlineKeyboardButton("Exit Tutorial ❌", callback_data="tutorial_exit")]]
        
        # Create the reply markup
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format step number
        step_indicator = f"Step {current_step + 1} of {tutorial_data['total_steps']}"
        
        # Format the message with the step content
        message = (
            f"*{step['title']}*\n"
            f"_{step_indicator}_\n\n"
            f"{step['content']}"
        )
        
        # Check if this is a callback query or a message
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            
            try:
                # Try to edit the existing message
                await query.edit_message_text(
                    text=message,
                    parse_mode="MARKDOWN",
                    reply_markup=reply_markup
                )
            except Exception as e:
                self.logger.error(f"Error editing message: {e}")
                
                # Fallback to sending a new message
                await query.message.reply_text(
                    text=message,
                    parse_mode="MARKDOWN",
                    reply_markup=reply_markup
                )
        else:
            # Send a new message
            await update.message.reply_text(
                text=message,
                parse_mode="MARKDOWN",
                reply_markup=reply_markup
            )
    
    async def handle_tutorial_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle tutorial navigation buttons.
        
        Args:
            update: Telegram update
            context: Context
        """
        query = update.callback_query
        
        # Extract the action from the callback data
        action = query.data.split("_")[1]
        
        # Check if there's an active tutorial
        if 'tutorial' not in context.user_data:
            await query.answer("No active tutorial.")
            return
        
        # Process the action
        if action == "next":
            # Move to the next step
            context.user_data['tutorial']['current_step'] += 1
            await self.show_tutorial_step(update, context)
        
        elif action == "prev":
            # Move to the previous step
            context.user_data['tutorial']['current_step'] -= 1
            await self.show_tutorial_step(update, context)
        
        elif action == "finish" or action == "exit":
            # End the tutorial
            await query.answer("Tutorial completed!")
            
            # Save progress to sheets if available
            if self.sheets_manager:
                user_id = update.effective_user.id
                tutorial_id = context.user_data['tutorial']['id']
                
                # Record tutorial completion in sheets
                try:
                    # self.sheets_manager.update_tutorial_completed(user_id, tutorial_id)
                    self.logger.info(f"User {user_id} completed tutorial: {tutorial_id}")
                except Exception as e:
                    self.logger.error(f"Error tracking tutorial completion: {e}")
            
            # Clear the tutorial data
            tutorial_id = context.user_data['tutorial']['id']
            del context.user_data['tutorial']
            
            # Show a completion message
            if action == "finish":
                tutorial = TUTORIALS[tutorial_id]
                
                # Create keyboard with suggested next actions
                keyboard = [
                    [InlineKeyboardButton("🚗 Set Up Car Preferences", callback_data="my_cars")],
                    [InlineKeyboardButton("👀 View More Tutorials", callback_data="tutorial_list")]
                ]
                
                # Add premium button if not on premium tutorial
                if tutorial_id != "premium_features":
                    keyboard.append([InlineKeyboardButton("✨ Upgrade to Premium", callback_data="view_subscription")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=(
                        f"*{tutorial['title']} - Complete!* 🎉\n\n"
                        f"You've completed this tutorial. What would you like to do next?"
                    ),
                    parse_mode="MARKDOWN",
                    reply_markup=reply_markup
                )
            else:
                # Just remove the tutorial message for "exit"
                await query.message.delete()
    
    async def show_tutorial_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show a list of available tutorials.
        
        Args:
            update: Telegram update
            context: Context
        """
        # Create keyboard with available tutorials
        keyboard = []
        
        for tutorial_id, tutorial in TUTORIALS.items():
            # Check if user has completed this tutorial before
            completed = self._is_tutorial_completed(update.effective_user.id, tutorial_id)
            
            # Add checkmark for completed tutorials
            title = f"{tutorial['title']} {'✅' if completed else '📚'}"
            
            keyboard.append([
                InlineKeyboardButton(
                    title,
                    callback_data=f"start_tutorial_{tutorial_id}"
                )
            ])
        
        # Add button to go back to main menu
        keyboard.append([InlineKeyboardButton("↩️ Back to Main Menu", callback_data="tutorial_exit")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Check if this is from a callback query
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            
            await query.edit_message_text(
                text=(
                    "*AutoSniper Tutorials* 📚\n\n"
                    "Choose a tutorial to learn more about AutoSniper features:"
                ),
                parse_mode="MARKDOWN",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=(
                    "*AutoSniper Tutorials* 📚\n\n"
                    "Choose a tutorial to learn more about AutoSniper features:"
                ),
                parse_mode="MARKDOWN",
                reply_markup=reply_markup
            )
    
    def _is_tutorial_completed(self, user_id: int, tutorial_id: str) -> bool:
        """Check if a user has completed a specific tutorial.
        
        Args:
            user_id: User ID
            tutorial_id: Tutorial ID
            
        Returns:
            bool: True if tutorial has been completed, False otherwise
        """
        # Check completion status in context if available
        if self.sheets_manager:
            try:
                # Implementation depends on your sheets structure
                # return self.sheets_manager.get_tutorial_completion(user_id, tutorial_id)
                pass
            except Exception as e:
                self.logger.error(f"Error checking tutorial completion: {e}")
        
        # For now, just return False (not completed)
        # This will be replaced with actual tracking when sheets integration is implemented
        return False
    
    async def handle_tutorial_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle tutorial selection from the list.
        
        Args:
            update: Telegram update
            context: Context
        """
        query = update.callback_query
        await query.answer()
        
        # Extract the tutorial ID from the callback data
        tutorial_id = query.data.split("_")[2]
        
        # Start the selected tutorial
        await self.start_tutorial(update, context, tutorial_id)
    
    async def suggest_tutorial(self, update: Update, context: ContextTypes.DEFAULT_TYPE, suggested_tutorial_id: str) -> None:
        """Suggest a specific tutorial based on user context.
        
        Args:
            update: Update object
            context: Context object
            suggested_tutorial_id: ID of the tutorial to suggest
        """
        if suggested_tutorial_id not in TUTORIALS:
            return  # Invalid tutorial ID
        
        tutorial = TUTORIALS[suggested_tutorial_id]
        
        # Create keyboard with tutorial option
        keyboard = [
            [InlineKeyboardButton(f"View {tutorial['title']} Tutorial", callback_data=f"start_tutorial_{suggested_tutorial_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💡 *Tutorial Suggestion*\n\n"
            f"Want to learn more about this? We have a tutorial on {tutorial['title']} that might help.",
            parse_mode="MARKDOWN",
            reply_markup=reply_markup
        )
    
    def get_suggested_tutorial_id(self, command: str) -> Optional[str]:
        """Get a suggested tutorial ID based on the command or context.
        
        Args:
            command: Command or context string
            
        Returns:
            Optional[str]: Tutorial ID or None if no suitable tutorial found
        """
        command = command.lower()
        
        # Map commands to relevant tutorials
        command_tutorial_map = {
            "start": "getting_started",
            "mycars": "getting_started",
            "subscribe": "premium_features",
            "dealsofweek": "premium_features",
            "error": "troubleshooting",
            "help": "getting_started",
            "advanced": "advanced_search"
        }
        
        # Check for exact matches
        if command in command_tutorial_map:
            return command_tutorial_map[command]
        
        # Check for partial matches
        for cmd, tutorial_id in command_tutorial_map.items():
            if cmd in command:
                return tutorial_id
        
        # Default to getting started
        return "getting_started"


# Helper function to get a tutorial manager instance
def get_tutorial_manager(sheets_manager=None):
    """Get a TutorialManager instance.
    
    Args:
        sheets_manager: SheetsManager instance for tracking progress
        
    Returns:
        TutorialManager instance
    """
    return TutorialManager(sheets_manager)
