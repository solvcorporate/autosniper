"""
Alert system for notifying users about car listings that match their preferences.
"""

import logging
import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("alerts")

class AlertEngine:
    """Engine for generating and sending alerts about car listings."""
    
    def __init__(self, bot: Bot):
        """Initialize the alert engine.
        
        Args:
            bot: Telegram bot instance for sending messages
        """
        self.logger = logging.getLogger("alerts.engine")
        self.bot = bot
    
    async def process_matches(self, user_matches: Dict[str, List[Dict[str, Any]]], sheets_manager=None) -> Dict[str, int]:
        """Process matches and send alerts to users.
        
        Args:
            user_matches: Dictionary mapping user_ids to lists of matching listings
            sheets_manager: Optional SheetsManager instance for updating notification status
            
        Returns:
            Dictionary with statistics about alerts sent
        """
        alert_stats = {
            "total_users": len(user_matches),
            "total_matches": sum(len(matches) for matches in user_matches.values()),
            "alerts_sent": 0,
            "failures": 0,
            "users_notified": 0
        }
        
        self.logger.info(f"Processing matches for {alert_stats['total_users']} users with {alert_stats['total_matches']} total matches")
        
        # Process each user's matches
        for user_id, matches in user_matches.items():
            if not matches:
                continue
                
            # Sort matches by score if available, otherwise by price
            if 'score' in matches[0]:
                sorted_matches = sorted(matches, key=lambda x: x.get('score', 0), reverse=True)
            else:
                sorted_matches = sorted(matches, key=lambda x: x.get('price', 0))
            
            # Send alerts for this user's top matches
            user_alert_count = 0
            try:
                # Get user's subscription tier from the first match (all matches should have same user_id)
                user_subscription = self._get_user_subscription(matches[0], sheets_manager)
                
                # Determine how many alerts to send based on subscription tier
                max_alerts = self._get_max_alerts(user_subscription)
                
                # Send alerts up to the maximum
                for match in sorted_matches[:max_alerts]:
                    if await self.send_alert(user_id, match):
                        user_alert_count += 1
                        alert_stats["alerts_sent"] += 1
                        
                        # Update notification status in Google Sheets if a sheets_manager is provided
                        if sheets_manager:
                            self._update_notification_status(match, user_id, sheets_manager)
                    else:
                        alert_stats["failures"] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing alerts for user {user_id}: {e}")
                alert_stats["failures"] += 1
            
            # Count user as notified if at least one alert was sent
            if user_alert_count > 0:
                alert_stats["users_notified"] += 1
                
            self.logger.info(f"Sent {user_alert_count} alerts to user {user_id}")
        
        self.logger.info(f"Alert processing complete: {alert_stats['alerts_sent']} alerts sent to {alert_stats['users_notified']} users")
        return alert_stats
    
    async def send_alert(self, user_id: str, match: Dict[str, Any]) -> bool:
        """Send an alert to a user about a matching car listing.
        
        Args:
            user_id: Telegram user ID
            match: The matching car listing with score
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Generate the alert message
            message = self._generate_alert_message(match)
            
            # Send the message to the user
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="MARKDOWN",
                disable_web_page_preview=True  # Don't preview the URL
            )
            
            self.logger.info(f"Sent alert to user {user_id} for {match.get('make', '')} {match.get('model', '')}")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Telegram error sending alert to user {user_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending alert to user {user_id}: {e}")
            return False
    
    def _generate_alert_message(self, match: Dict[str, Any]) -> str:
        """Generate an alert message for a matching car listing.
        
        Args:
            match: The matching car listing with score
            
        Returns:
            Formatted alert message
        """
        # Extract basic information
        make = match.get('make', 'Unknown')
        model = match.get('model', 'Unknown')
        year = match.get('year', 'Unknown')
        price = match.get('price', 0)
        mileage = match.get('mileage', 'Unknown')
        location = match.get('location', 'Unknown')
        fuel_type = match.get('fuel_type', '')
        transmission = match.get('transmission', '')
        url = match.get('url', '')
        
        # Extract score information if available
        score = match.get('score', None)
        grade = match.get('grade', '')
        score_details = match.get('score_details', {})
        
        # Format the price with thousands separator
        price_formatted = f"£{price:,}" if price else "Unknown"
        
        # Format the mileage with thousands separator
        mileage_formatted = f"{mileage:,} miles" if mileage else "Unknown mileage"
        
        # Determine alert emphasis based on grade
        alert_emphasis = "DEAL ALERT!"
        if grade == 'A+':
            alert_emphasis = "A+ EXCEPTIONAL DEAL ALERT!"
        elif grade == 'A':
            alert_emphasis = "A GREAT DEAL ALERT!"
        elif grade == 'B':
            alert_emphasis = "B GOOD DEAL ALERT!"
        
        # Build the message with grade-specific formatting
        message_parts = []
        
        # Alert header
        if grade in ['A+', 'A']:
            message_parts.append(f"🚨 *{alert_emphasis}* 🚨\n")
        else:
            message_parts.append(f"🚘 *{alert_emphasis}* 🚘\n")
        
        # Car details section
        message_parts.append(f"🚗 *{year} {make} {model}*\n")
        
        # Price section with market comparison if available
        price_section = f"💰 *Price: {price_formatted}*"
        market_avg = score_details.get('market_average', None)
        if market_avg:
            price_diff_pct = ((market_avg - price) / market_avg) * 100
            price_section += f" (Market avg: £{market_avg:,}, {price_diff_pct:.0f}% below market)"
        message_parts.append(price_section + "\n")
        
        # Car specifications
        specs = []
        specs.append(f"🔄 {mileage_formatted}")
        if fuel_type:
            specs.append(f"⛽ {fuel_type}")
        if transmission:
            specs.append(f"🎮 {transmission}")
        specs.append(f"📍 {location}")
        message_parts.append(" | ".join(specs) + "\n")
        
        # Score and grade if available
        if score is not None:
            message_parts.append(f"📊 *Score: {score:.1f} ({grade})*")
            if score_details.get('price_score'):
                message_parts.append(f" (Price: {score_details['price_score']:.1f}")
            if score_details.get('mileage_score'):
                message_parts.append(f", Mileage: {score_details['mileage_score']:.1f})")
            else:
                message_parts.append(")")
            message_parts.append("\n")
        
        # Suggested message to seller
        if make and model:
            message_parts.append(f"💬 Suggested message: \"Hi, is your {year} {make} {model} still available? I can view it soon if it is.\"\n")
        
        # Link to the listing
        if url:
            message_parts.append(f"\n➡️ [View Listing]({url})")
        
        # Join all parts into a single message
        return "".join(message_parts)
    
    def _get_user_subscription(self, match: Dict[str, Any], sheets_manager) -> str:
        """Get a user's subscription tier.
        
        Args:
            match: A match for the user (contains user_id)
            sheets_manager: SheetsManager instance for querying user info
            
        Returns:
            Subscription tier (e.g., 'Basic', 'Premium', 'None')
        """
        user_id = match.get('user_id')
        
        if not user_id or not sheets_manager:
            return 'Basic'  # Default to Basic tier if no sheets_manager
        
        try:
            # Query the user's subscription tier
            # This will depend on how you've structured your sheets
            # Here's a simple implementation based on the assumed structure
            users = sheets_manager.users_sheet.get_all_records()
            for user in users:
                if str(user.get('user_id', '')) == str(user_id):
                    return user.get('subscription_tier', 'Basic')
            
            return 'Basic'  # Default if user not found
        except Exception as e:
            self.logger.error(f"Error getting subscription for user {user_id}: {e}")
            return 'Basic'  # Default on error
    
    def _get_max_alerts(self, subscription_tier: str) -> int:
        """Get the maximum number of alerts based on subscription tier.
        
        Args:
            subscription_tier: User's subscription tier
            
        Returns:
            Maximum number of alerts to send
        """
        tiers = {
            'Premium': 10,  # Premium users get up to 10 alerts
            'Basic': 3,     # Basic users get up to 3 alerts
            'None': 1       # Non-subscribers get at most 1 alert
        }
        
        return tiers.get(subscription_tier, 1)  # Default to 1 if tier not found
    
    def _update_notification_status(self, match: Dict[str, Any], user_id: str, sheets_manager) -> bool:
        """Update the notification status in Google Sheets.
        
        Args:
            match: The listing that was alerted
            user_id: The user who was notified
            sheets_manager: SheetsManager instance
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            listing_id = match.get('id') or match.get('listing_id')
            if not listing_id:
                return False
                
            # The implementation here will depend on your sheets structure
            # This is a placeholder for the actual implementation
            # sheets_manager.update_notification_status(listing_id, user_id)
            
            return True
        except Exception as e:
            self.logger.error(f"Error updating notification status: {e}")
            return False


# Test function to generate sample alert messages
def test_alert_messages():
    """Test generating alert messages with sample data."""
    # Sample match with score
    sample_match = {
        'id': '1',
        'make': 'BMW',
        'model': '3 Series',
        'year': 2018,
        'price': 14500,
        'mileage': 45000,
        'location': 'Manchester, UK',
        'fuel_type': 'Diesel',
        'transmission': 'Automatic',
        'url': 'https://example.com/listing1',
        'score': 85.3,
        'grade': 'A',
        'score_details': {
            'price_score': 88.5,
            'mileage_score': 80.0,
            'suspicious': False,
            'market_average': 19200
        }
    }
    
    # Create a mock AlertEngine (without a real bot)
    class MockBot:
        async def send_message(self, **kwargs):
            return True
    
    alert_engine = AlertEngine(MockBot())
    
    # Generate a message
    message = alert_engine._generate_alert_message(sample_match)
    
    print("Sample Alert Message:")
    print("-" * 40)
    print(message)
    print("-" * 40)
    
    # Sample match without score (legacy case)
    sample_match_no_score = {
        'id': '2',
        'make': 'Ford',
        'model': 'Focus',
        'year': 2019,
        'price': 9500,
        'mileage': 30000,
        'location': 'London, UK',
        'fuel_type': 'Petrol',
        'transmission': 'Manual',
        'url': 'https://example.com/listing2'
    }
    
    # Generate a message without score
    message_no_score = alert_engine._generate_alert_message(sample_match_no_score)
    
    print("\nSample Alert Message (No Score):")
    print("-" * 40)
    print(message_no_score)
    
    return message, message_no_score


if __name__ == "__main__":
    test_alert_messages()
