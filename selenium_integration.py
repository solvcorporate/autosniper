"""
Integration module for Selenium-based scrapers.
This module adapts the Selenium scrapers to work with the existing scraper framework.
"""

import logging
from typing import Dict, List, Optional, Any

from scrapers.base import BaseScraper
from selenium_scraper import AutoTraderSeleniumScraper, GumtreeSeleniumScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("selenium_integration")

class AutoTraderSeleniumAdapter(BaseScraper):
    """Adapter for AutoTrader Selenium scraper to conform to the BaseScraper interface."""
    
    def __init__(self):
        """Initialize the AutoTrader Selenium scraper adapter."""
        super().__init__(
            name="AutoTrader",
            base_url="https://www.autotrader.co.uk",
        )
        self.logger = logging.getLogger("selenium_integration.autotrader")
        self.selenium_scraper = AutoTraderSeleniumScraper(headless=True)
    
    def construct_search_url(self, preferences: Dict[str, Any]) -> str:
        """Construct a search URL based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            String URL for searching
        """
        # This isn't actually used for the Selenium scraper, but we need to implement it
        # to satisfy the BaseScraper interface
        return self.selenium_scraper._construct_search_url(preferences)
    
    def extract_listings(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract car listings from HTML content.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of dictionaries with car details
        """
        # This isn't actually used for the Selenium scraper, but we need to implement it
        # to satisfy the BaseScraper interface
        return []
    
    def search(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for car listings based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            List of car listings
        """
        self.logger.info(f"Searching AutoTrader with Selenium for: {preferences.get('make', '')} {preferences.get('model', '')}")
        
        try:
            # Use the Selenium scraper to search
            listings = self.selenium_scraper.search_cars(preferences)
            
            # Format the listings for consistency
            formatted_listings = [self.format_listing(listing) for listing in listings]
            self.logger.info(f"Found {len(formatted_listings)} listings")
            
            return formatted_listings
        except Exception as e:
            self.logger.error(f"Error searching AutoTrader with Selenium: {e}")
            return []


class GumtreeSeleniumAdapter(BaseScraper):
    """Adapter for Gumtree Selenium scraper to conform to the BaseScraper interface."""
    
    def __init__(self):
        """Initialize the Gumtree Selenium scraper adapter."""
        super().__init__(
            name="Gumtree",
            base_url="https://www.gumtree.com",
        )
        self.logger = logging.getLogger("selenium_integration.gumtree")
        self.selenium_scraper = GumtreeSeleniumScraper(headless=True)
    
    def construct_search_url(self, preferences: Dict[str, Any]) -> str:
        """Construct a search URL based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            String URL for searching
        """
        # This isn't actually used for the Selenium scraper, but we need to implement it
        # to satisfy the BaseScraper interface
        return self.selenium_scraper._construct_search_url(preferences)
    
    def extract_listings(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract car listings from HTML content.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of dictionaries with car details
        """
        # This isn't actually used for the Selenium scraper, but we need to implement it
        # to satisfy the BaseScraper interface
        return []
    
    def search(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for car listings based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            List of car listings
        """
        self.logger.info(f"Searching Gumtree with Selenium for: {preferences.get('make', '')} {preferences.get('model', '')}")
        
        try:
            # Use the Selenium scraper to search
            listings = self.selenium_scraper.search_cars(preferences)
            
            # Format the listings for consistency
            formatted_listings = [self.format_listing(listing) for listing in listings]
            self.logger.info(f"Found {len(formatted_listings)} listings")
            
            return formatted_listings
        except Exception as e:
            self.logger.error(f"Error searching Gumtree with Selenium: {e}")
            return []


# Factory function to create Selenium-based scrapers
def get_selenium_scraper(scraper_name: str) -> Optional[BaseScraper]:
    """Get a Selenium-based scraper by name.
    
    Args:
        scraper_name: Name of the scraper
        
    Returns:
        BaseScraper instance or None if not found
    """
    scrapers = {
        "autotrader": AutoTraderSeleniumAdapter(),
        "gumtree": GumtreeSeleniumAdapter(),
    }
    
    scraper = scrapers.get(scraper_name.lower())
    
    if not scraper:
        logger.warning(f"Selenium scraper '{scraper_name}' not found")
        
    return scraper


# Test function
def test_selenium_integration():
    """Test the Selenium scraper integration."""
    # Test preferences
    preferences = {
        'make': 'Ford',
        'model': 'Focus',
        'min_year': 2015,
        'max_year': 2021,
        'min_price': 5000,
        'max_price': 15000,
        'location': 'UK: Manchester'
    }
    
    # Test AutoTrader
    logger.info("Testing AutoTrader Selenium integration...")
    autotrader_scraper = get_selenium_scraper("autotrader")
    if autotrader_scraper:
        autotrader_listings = autotrader_scraper.search(preferences)
        logger.info(f"Found {len(autotrader_listings)} AutoTrader listings")
    
    # Test Gumtree
    logger.info("Testing Gumtree Selenium integration...")
    gumtree_scraper = get_selenium_scraper("gumtree")
    if gumtree_scraper:
        gumtree_listings = gumtree_scraper.search(preferences)
        logger.info(f"Found {len(gumtree_listings)} Gumtree listings")


if __name__ == "__main__":
    test_selenium_integration()
