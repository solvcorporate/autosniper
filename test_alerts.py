"""
Test script for the alert system.
"""
import asyncio
import logging
from telegram import Bot
from alerts import AlertEngine
from scoring import get_scoring_engine, SAMPLE_MARKET_DATA

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_alerts")

class MockBot:
    """Mock Bot class for testing alerts without sending real Telegram messages."""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None):
        """Mock implementation of send_message."""
        message = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': disable_web_page_preview
        }
        self.messages.append(message)
        logger.info(f"Mock sent message to {chat_id}")
        return True

def create_sample_matches():
    """Create sample matches for testing."""
    # Sample scored listings
    scoring_engine = get_scoring_engine(SAMPLE_MARKET_DATA)
    
    listings = [
        {
            'id': '1',
            'make': 'Ford',
            'model': 'Focus',
            'year': 2018,
            'price': 7500,  # Good deal - below market (12000)
            'mileage': 45000,
            'location': 'Manchester, UK',
            'fuel_type': 'Petrol',
            'transmission': 'Manual',
            'url': 'https://example.com/listing1'
        },
        {
            'id': '2',
            'make': 'BMW',
            'model': '3 Series',
            'year': 2017,
            'price': 10000,  # Very good deal - well below market (16000)
            'mileage': 80000,  # Higher mileage
            'location': 'London, UK',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic',
            'url': 'https://example.com/listing2'
        },
        {
            'id': '3',
            'make': 'Volkswagen',
            'model': 'Golf',
            'year': 2019,
            'price': 16500,  # Average deal - slightly above market (16000)
            'mileage': 25000,  # Low mileage
            'location': 'Liverpool, UK',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic',
            'url': 'https://example.com/listing3'
        }
    ]
    
    scored_listings = scoring_engine.batch_score_listings(listings)
    
    # Add user_id to create matches
    for listing in scored_listings:
        if listing['make'] == 'Ford':
            listing['user_id'] = '123'
        elif listing['make'] == 'BMW':
            listing['user_id'] = '456'
        elif listing['make'] == 'Volkswagen':
            listing['user_id'] = '789'
    
    # Group by user_id
    matches = {}
    for listing in scored_listings:
        user_id = str(listing.get('user_id', ''))
        if user_id:
            if user_id not in matches:
                matches[user_id] = []
            matches[user_id].append(listing)
    
    return matches

async def test_alert_engine():
    """Test the alert engine."""
    logger.info("Testing alert engine...")
    
    # Create a mock bot
    mock_bot = MockBot()
    
    # Initialize the alert engine with the mock bot
    alert_engine = AlertEngine(mock_bot)
    
    # Create sample matches
    matches = create_sample_matches()
    
    # Process matches
    stats = await alert_engine.process_matches(matches)
    
    # Print stats
    logger.info(f"Alert Stats: {stats}")
    
    # Print all messages that would have been sent
    logger.info(f"Would have sent {len(mock_bot.messages)} messages:")
    for i, message in enumerate(mock_bot.messages, 1):
        logger.info(f"\nMessage {i} to chat_id {message['chat_id']}:")
        # Print just the first 200 characters to avoid cluttering logs
        logger.info(f"{message['text'][:200]}...")
    
    return stats, mock_bot.messages

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_alert_engine())
