"""
Subscription management for AutoSniper.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("subscription")

# Import managers
from sheets import get_sheets_manager
from payments import get_payment_manager

class SubscriptionManager:
    """Manager for handling user subscriptions."""
    
    def __init__(self):
        """Initialize the subscription manager."""
        self.sheets_manager = get_sheets_manager()
        self.payment_manager = get_payment_manager(self.sheets_manager)
        self.logger = logging.getLogger("subscription.manager")
        
        if not self.sheets_manager:
            self.logger.error("Failed to initialize SheetsManager")
        if not self.payment_manager:
            self.logger.error("Failed to initialize PaymentManager")
    
    def get_user_tier(self, user_id: int) -> str:
        """Get a user's subscription tier.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            string: Subscription tier ('Basic', 'Premium', or 'None')
        """
        if not self.sheets_manager:
            self.logger.warning(f"No sheets_manager available to get user tier for user {user_id}")
            return 'None'
            
        tier = self.sheets_manager.get_subscription_tier(user_id)
        return tier if tier else 'None'
    
    def is_user_premium(self, user_id: int) -> bool:
        """Check if user has a Premium subscription.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if user has Premium subscription, False otherwise
        """
        return self.get_user_tier(user_id) == 'Premium'
    
    def has_active_subscription(self, user_id: int) -> bool:
        """Check if user has any active subscription.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if user has active subscription, False otherwise
        """
        tier = self.get_user_tier(user_id)
        return tier in ['Basic', 'Premium']
    
    def get_subscription_details(self, user_id: int) -> Dict[str, Any]:
        """Get detailed subscription information for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: Subscription details or None if error
        """
        if not self.sheets_manager:
            self.logger.warning(f"No sheets_manager available to get subscription details for user {user_id}")
            return {
                'tier': 'None',
                'active': False
            }
            
        return self.sheets_manager.get_subscription_details(user_id)
    
    def create_checkout_url(self, user_id: int, tier: str, success_url: str, cancel_url: str) -> Optional[str]:
        """Create a checkout URL for subscription payment.
        
        Args:
            user_id: Telegram user ID
            tier: Subscription tier ('Basic' or 'Premium')
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            
        Returns:
            string: Checkout URL or None if creation failed
        """
        if not self.payment_manager:
            self.logger.error("No payment_manager available to create checkout session")
            return None
            
        return self.payment_manager.create_checkout_session(user_id, tier, success_url, cancel_url)
    
    def check_expired_subscriptions(self) -> int:
        """Check for expired subscriptions and update status.
        
        Returns:
            int: Number of subscriptions updated
        """
        if not self.sheets_manager:
            self.logger.warning("No sheets_manager available to check expired subscriptions")
            return 0
            
        return self.sheets_manager.check_subscriptions_expiry()
    
    def handle_webhook_event(self, payload: Dict[str, Any], signature: str) -> bool:
        """Handle Stripe webhook event.
        
        Args:
            payload: Webhook event payload
            signature: Stripe signature header
            
        Returns:
            bool: True if handled successfully, False otherwise
        """
        if not self.payment_manager:
            self.logger.error("No payment_manager available to handle webhook event")
            return False
            
        return self.payment_manager.handle_webhook_event(payload, signature)


# Helper function to get a subscription manager instance
def get_subscription_manager():
    """Get a SubscriptionManager instance.
    
    Returns:
        SubscriptionManager instance
    """
    return SubscriptionManager()


# Subscription tiers and features (for display to users)
SUBSCRIPTION_FEATURES = {
    'Basic': {
        'name': 'Basic Plan',
        'price': '€10/month',
        'features': [
            'Multiple car preferences',
            'Regular deal alerts',
            'Limited to 3 alerts per day',
            'Access to AutoTrader and Gumtree scrapers'
        ],
        'emoji': '🔹'
    },
    'Premium': {
        'name': 'Premium Plan',
        'price': '€20/month',
        'features': [
            'Unlimited car preferences',
            'Priority deal alerts',
            'Unlimited alerts',
            'Access to all scrapers',
            'Weekly curated "Deals of the Week"',
            'Premium customer support'
        ],
        'emoji': '🔸'
    }
}
