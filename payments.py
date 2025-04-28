"""
Payment handling for AutoSniper, including Stripe integration.
"""

import os
import logging
import stripe
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("payments")

# Initialize Stripe with API key
stripe.api_key = os.getenv('STRIPE_API_KEY')

# Subscription tier details
SUBSCRIPTION_TIERS = {
    'Basic': {
        'name': 'Basic Subscription',
        'price_eur': 10,
        'description': 'Limited car alerts and basic features',
        'features': [
            'Multiple car preferences',
            'Regular deal alerts',
            'Limited to 3 alerts per day',
            'Access to AutoTrader and Gumtree scrapers'
        ],
        'stripe_price_id': os.getenv('STRIPE_BASIC_PRICE_ID')
    },
    'Premium': {
        'name': 'Premium Subscription',
        'price_eur': 20,  # Changed from 25 to 20
        'description': 'Unlimited car alerts and premium features',
        'features': [
            'Unlimited car preferences',
            'Priority deal alerts',
            'Unlimited alerts',
            'Access to all scrapers',
            'Weekly curated "Deals of the Week"',
            'Premium customer support'
        ],
        'stripe_price_id': os.getenv('STRIPE_PREMIUM_PRICE_ID')
    }
}

class PaymentManager:
    """Manager for handling payments and subscriptions."""
    
    def __init__(self, sheets_manager=None):
        """Initialize the payment manager.
        
        Args:
            sheets_manager: SheetsManager instance for updating subscription status
        """
        self.sheets_manager = sheets_manager
        self.logger = logging.getLogger("payments.manager")
        
        # Check if Stripe API key is available
        if not stripe.api_key:
            self.logger.error("Stripe API key not found in environment variables")
        else:
            self.logger.info("Payment manager initialized with Stripe API")
    
    def create_checkout_session(self, user_id: int, tier: str, success_url: str, cancel_url: str) -> str:
        """Create a Stripe Checkout Session for a subscription.
        
        Args:
            user_id: Telegram user ID
            tier: Subscription tier ('Basic' or 'Premium')
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            
        Returns:
            Checkout URL or None if creation failed
        """
        if tier not in SUBSCRIPTION_TIERS:
            self.logger.error(f"Invalid subscription tier: {tier}")
            return None
        
        tier_info = SUBSCRIPTION_TIERS[tier]
        price_id = tier_info['stripe_price_id']
        
        if not price_id:
            self.logger.error(f"Price ID not found for tier: {tier}")
            return None
        
        try:
            # Create a Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(user_id),
                metadata={
                    'user_id': str(user_id),
                    'tier': tier,
                    'product': 'AutoSniper Subscription'
                }
            )
            
            return checkout_session.url
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error: {e}")
            return None
    
    def handle_webhook_event(self, payload: Dict[str, Any], signature: str) -> bool:
        """Handle Stripe webhook event.
        
        Args:
            payload: Webhook event payload
            signature: Stripe signature header
            
        Returns:
            bool: True if handled successfully, False otherwise
        """
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if not webhook_secret:
            self.logger.error("Stripe webhook secret not found in environment variables")
            return False
        
        try:
            # Verify and construct the event
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            
            # Handle checkout.session.completed event
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                
                # Get user ID and tier from metadata
                user_id = session.get('metadata', {}).get('user_id')
                tier = session.get('metadata', {}).get('tier')
                
                if not user_id or not tier:
                    self.logger.error("User ID or tier not found in session metadata")
                    return False
                
                # Update user's subscription in Google Sheets
                if self.sheets_manager:
                    # Calculate expiration date (30 days from now)
                    expiration_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    
                    # Update subscription in Google Sheets
                    success = self.sheets_manager.update_subscription(
                        user_id=int(user_id),
                        subscription_tier=tier,
                        payment_id=session.get('id'),
                        amount=session.get('amount_total', 0) / 100,  # Convert cents to euros
                        expiration_date=expiration_date
                    )
                    
                    if not success:
                        self.logger.error(f"Failed to update subscription in Google Sheets for user {user_id}")
                        return False
                else:
                    self.logger.warning(f"No sheets_manager available to update subscription for user {user_id}")
                
                self.logger.info(f"Successfully processed payment for user {user_id}: {tier} subscription")
                return True
                
            return True  # Successfully handled event (even if we didn't do anything with it)
            
        except Exception as e:
            self.logger.error(f"Error processing webhook: {e}")
            return False
    
    def is_premium_user(self, user_id: int) -> bool:
        """Check if a user has a Premium subscription.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if user has Premium subscription, False otherwise
        """
        if not self.sheets_manager:
            self.logger.warning(f"No sheets_manager available to check subscription for user {user_id}")
            return False
            
        try:
            # Get the user's subscription tier from Google Sheets
            subscription_tier = self.sheets_manager.get_subscription_tier(user_id)
            return subscription_tier == 'Premium'
        except Exception as e:
            self.logger.error(f"Error checking subscription: {e}")
            return False
    
    def has_active_subscription(self, user_id: int) -> bool:
        """Check if a user has any active subscription.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if user has active subscription, False otherwise
        """
        if not self.sheets_manager:
            self.logger.warning(f"No sheets_manager available to check subscription for user {user_id}")
            return False
            
        try:
            # Get the user's subscription tier from Google Sheets
            subscription_tier = self.sheets_manager.get_subscription_tier(user_id)
            return subscription_tier in ['Basic', 'Premium']
        except Exception as e:
            self.logger.error(f"Error checking subscription: {e}")
            return False
    
    def get_subscription_tier(self, user_id: int) -> str:
        """Get a user's subscription tier.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            str: Subscription tier ('Basic', 'Premium', or 'None')
        """
        if not self.sheets_manager:
            self.logger.warning(f"No sheets_manager available to get subscription for user {user_id}")
            return 'None'
            
        try:
            # Get the user's subscription tier from Google Sheets
            subscription_tier = self.sheets_manager.get_subscription_tier(user_id)
            return subscription_tier or 'None'
        except Exception as e:
            self.logger.error(f"Error getting subscription tier: {e}")
            return 'None'


# Helper function to get a payment manager instance
def get_payment_manager(sheets_manager=None):
    """Get a PaymentManager instance.
    
    Args:
        sheets_manager: SheetsManager instance for user data
        
    Returns:
        PaymentManager instance
    """
    return PaymentManager(sheets_manager)
