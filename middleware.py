"""
Middleware for AutoSniper.
This module provides middleware to handle subscription verification and other common tasks.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("middleware")

# Import the subscription manager
from subscription import get_subscription_manager

class SubscriptionMiddleware:
    """Middleware for verifying user subscription status."""
    
    def __init__(self):
        """Initialize the subscription middleware."""
        self.logger = logging.getLogger("middleware.subscription")
        self.subscription_manager = get_subscription_manager()
    
    async def verify_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Verify that a user has a premium subscription.
        
        Args:
            update: Update object from Telegram
            context: Context object from Telegram
            
        Returns:
            bool: True if user has premium subscription, False otherwise
        """
        user_id = update.effective_user.id
        
        # Check if user has premium subscription
        is_premium = self.subscription_manager.is_user_premium(user_id)
        
        if not is_premium:
            # If not premium, send a message notifying the user
            await update.message.reply_text(
                "*Premium Feature Required*\n\n"
                "This feature is exclusively available to Premium subscribers.\n\n"
                "Use /subscribe to learn about our subscription options and upgrade your account.",
                parse_mode="MARKDOWN"
            )
            return False
        
        return True
    
    async def verify_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Verify that a user has any active subscription.
        
        Args:
            update: Update object from Telegram
            context: Context object from Telegram
            
        Returns:
            bool: True if user has any subscription, False otherwise
        """
        user_id = update.effective_user.id
        
        # Check if user has any subscription
        has_subscription = self.subscription_manager.has_active_subscription(user_id)
        
        if not has_subscription:
            # If no subscription, send a message notifying the user
            await update.message.reply_text(
                "*Subscription Required*\n\n"
                "This feature requires an active subscription.\n\n"
                "Use /subscribe to learn about our subscription options.",
                parse_mode="MARKDOWN"
            )
            return False
        
        return True
    
    def premium_required(self, func: Callable) -> Callable:
        """Decorator for functions that require premium subscription.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function that checks for premium subscription
        """
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            if await self.verify_premium(update, context):
                return await func(update, context)
            return None
        return wrapper
    
    def subscription_required(self, func: Callable) -> Callable:
        """Decorator for functions that require any subscription.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function that checks for any subscription
        """
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            if await self.verify_subscription(update, context):
                return await func(update, context)
            return None
        return wrapper


# Helper function to get a subscription middleware instance
def get_subscription_middleware():
    """Get a SubscriptionMiddleware instance.
    
    Returns:
        SubscriptionMiddleware instance
    """
    return SubscriptionMiddleware()
