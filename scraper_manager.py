"""
Manager for running scrapers and handling listings.
"""

import logging
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import the scrapers
from scrapers import get_scraper
from sheets import get_sheets_manager
from matching import get_matching_engine  # Add this import

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scraper_manager")

class ScraperManager:
    """Manager for running scrapers and handling listings."""
    
    def __init__(self, sheets_manager=None):
        """Initialize the scraper manager.
        
        Args:
            sheets_manager: SheetsManager instance (optional)
        """
        self.sheets_manager = sheets_manager
        self.logger = logging.getLogger("scraper_manager")
        
        # List of available scrapers
        self.available_scrapers = [
            "autotrader",
            "gumtree"
            # More scrapers will be added here as they're implemented
        ]
        
        # Initialize the matching engine
        self.matching_engine = get_matching_engine()  # Add this line
        
        self.logger.info("ScraperManager initialized")
    
    def run_scrapers(self, preferences_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run all available scrapers with the given preferences.
        
        Args:
            preferences_list: List of preference dictionaries
            
        Returns:
            List of all listings found
        """
        all_listings = []
        
        self.logger.info(f"Running scrapers for {len(preferences_list)} preference sets")
        
        # Run each scraper
        for scraper_name in self.available_scrapers:
            try:
                scraper = get_scraper(scraper_name)
                if not scraper:
                    self.logger.warning(f"Scraper '{scraper_name}' not found")
                    continue
                
                self.logger.info(f"Running scraper: {scraper_name}")
                listings = scraper.run_scraper(preferences_list)
                
                self.logger.info(f"Scraper {scraper_name} found {len(listings)} listings")
                all_listings.extend(listings)
                
                # Add a delay between scrapers to avoid network overload
                if scraper_name != self.available_scrapers[-1]:
                    delay = 2 + random.random() * 3  # 2-5 seconds
                    time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error running scraper {scraper_name}: {e}")
        
        # Apply deduplication
        unique_listings = self._deduplicate_listings(all_listings)
        self.logger.info(f"Found {len(unique_listings)} unique listings after deduplication")
        
        return unique_listings
    
    def _deduplicate_listings(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate listings.
        
        Args:
            listings: List of listing dictionaries
            
        Returns:
            List of deduplicated listings
        """
        # Use a dictionary to deduplicate by URL
        unique_dict = {}
        
        for listing in listings:
            url = listing.get('url', '')
            if url:
                # If this URL is already in our dictionary, keep the listing with more information
                if url in unique_dict:
                    existing = unique_dict[url]
                    # Count non-None values in each listing
                    existing_count = sum(1 for v in existing.values() if v is not None)
                    current_count = sum(1 for v in listing.values() if v is not None)
                    
                    # Replace only if current listing has more information
                    if current_count > existing_count:
                        unique_dict[url] = listing
                else:
                    unique_dict[url] = listing
        
        return list(unique_dict.values())
    
    def save_listings(self, listings: List[Dict[str, Any]]) -> int:
        """Save listings to Google Sheets.
        
        Args:
            listings: List of listing dictionaries
            
        Returns:
            int: Number of listings saved
        """
        if not self.sheets_manager:
            self.logger.error("No sheets_manager available to save listings")
            return 0
        
        saved_count = 0
        
        for listing in listings:
            try:
                success = self.sheets_manager.add_listing(listing)
                if success:
                    saved_count += 1
            except Exception as e:
                self.logger.error(f"Error saving listing to sheets: {e}")
        
        self.logger.info(f"Saved {saved_count} listings to Google Sheets")
        return saved_count
    
    def get_preferences_from_sheets(self) -> List[Dict[str, Any]]:
        """Get all active preferences from Google Sheets.
        
        Returns:
            List of preference dictionaries
        """
        if not self.sheets_manager:
            self.logger.error("No sheets_manager available to get preferences")
            return []
        
        try:
            # Get all car preferences
            all_preferences = []
            
            # Get all users from the Users sheet
            users = self.sheets_manager.users_sheet.get_all_records()
            
            for user in users:
                user_id = user.get('user_id')
                if not user_id:
                    continue
                
                # Get preferences for this user
                user_preferences = self.sheets_manager.get_car_preferences(user_id)
                all_preferences.extend(user_preferences)
            
            self.logger.info(f"Retrieved {len(all_preferences)} active preferences from Google Sheets")
            return all_preferences
        
        except Exception as e:
            self.logger.error(f"Error getting preferences from sheets: {e}")
            return []
    
    # Add this new method
    def match_listings_to_preferences(self, listings: List[Dict[str, Any]], preferences: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Match listings to user preferences.
        
        Args:
            listings: List of car listing dictionaries
            preferences: List of user preference dictionaries
            
        Returns:
            Dictionary mapping user_ids to lists of matching listings
        """
        if not listings or not preferences:
            self.logger.warning("No listings or preferences to match")
            return {}
        
        # Use the matching engine to find matches
        return self.matching_engine.find_matches(listings, preferences)
    
    def run_scraper_job(self) -> Dict[str, int]:
        """Run a complete scraper job.
        
        This function:
        1. Gets all preferences from Google Sheets
        2. Runs all scrapers with those preferences
        3. Saves the found listings to Google Sheets
        4. Matches listings to user preferences
        
        Returns:
            Dict with statistics about the job
        """
        start_time = datetime.now()
        self.logger.info(f"Starting scraper job at {start_time}")
        
        # Get preferences from sheets
        preferences = self.get_preferences_from_sheets()
        if not preferences:
            self.logger.warning("No preferences found, nothing to scrape for")
            return {
                "preferences": 0,
                "listings": 0,
                "saved": 0,
                "matches": 0,  # Add this field
                "duration_seconds": 0
            }
        
        # Run scrapers with these preferences
        listings = self.run_scrapers(preferences)
        
        # Save listings to sheets
        saved_count = self.save_listings(listings)
        
        # Match listings to preferences
        matches = self.match_listings_to_preferences(listings, preferences)
        match_count = sum(len(user_matches) for user_matches in matches.values())
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.logger.info(f"Finished scraper job in {duration:.2f} seconds")
        self.logger.info(f"Processed {len(preferences)} preferences, found {len(listings)} listings, saved {saved_count}, matched {match_count}")
        
        return {
            "preferences": len(preferences),
            "listings": len(listings),
            "saved": saved_count,
            "matches": match_count,  # Add this field
            "duration_seconds": duration
        }
    
    def test_scraper(self, scraper_name: str, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Test a specific scraper with given preferences.
        
        Args:
            scraper_name: Name of the scraper to test
            preferences: Dictionary of preferences to test with
            
        Returns:
            List of listings found
        """
        self.logger.info(f"Testing scraper '{scraper_name}' with preferences: {preferences}")
        
        scraper = get_scraper(scraper_name)
        if not scraper:
            self.logger.error(f"Scraper '{scraper_name}' not found")
            return []
        
        try:
            # Run the scraper with the test preferences
            listings = scraper.run_scraper([preferences])
            self.logger.info(f"Test found {len(listings)} listings")
            return listings
        
        except Exception as e:
            self.logger.error(f"Error testing scraper: {e}")
            return []


# Helper function to get a scraper manager instance
def get_scraper_manager():
    """Get a ScraperManager instance with sheets integration.
    
    Returns:
        ScraperManager instance
    """
    sheets_manager = get_sheets_manager()
    if not sheets_manager:
        logger.warning("Failed to get sheets_manager, scraper will run without sheets integration")
    
    return ScraperManager(sheets_manager)


# Simple test function
def test_run():
    """Run a test scraper job."""
    manager = get_scraper_manager()
    
    # Test with simple preferences
    test_preferences = {
        'make': 'Toyota',
        'model': 'Corolla',
        'min_year': 2015,
        'max_year': 2022,
        'min_price': 5000,
        'max_price': 15000,
        'location': 'UK: London'
    }
    
    # Test both scrapers
    logger.info("Testing AutoTrader scraper...")
    autotrader_listings = manager.test_scraper('autotrader', test_preferences)
    
    logger.info("Testing Gumtree scraper...")
    gumtree_listings = manager.test_scraper('gumtree', test_preferences)
    
    # Combine listings
    all_listings = autotrader_listings + gumtree_listings
    
    # Show results from both scrapers
    logger.info(f"AutoTrader found {len(autotrader_listings)} listings")
    logger.info(f"Gumtree found {len(gumtree_listings)} listings")
    
    # Show details of first 5 listings from each
    for i, listing in enumerate(autotrader_listings[:5], 1):
        logger.info(f"AutoTrader Listing {i}:")
        for key, value in listing.items():
            logger.info(f"  {key}: {value}")
    
    for i, listing in enumerate(gumtree_listings[:5], 1):
        logger.info(f"Gumtree Listing {i}:")
        for key, value in listing.items():
            logger.info(f"  {key}: {value}")
    
    # Test matching
    test_preferences_list = [
        {
            'user_id': '123',
            **test_preferences
        }
    ]
    
    matches = manager.match_listings_to_preferences(all_listings, test_preferences_list)
    
    logger.info(f"Found {len(matches.get('123', []))} matches for test user")
    
    return all_listings, matches


# For manual testing
if __name__ == "__main__":
    test_run()
