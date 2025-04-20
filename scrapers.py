"""
Main entry point for scrapers.
This module provides functions to manage and run scrapers for different car listing sites.
"""

import logging
import os
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scrapers")

# Flag to control whether to use Selenium-based scrapers
# This can be controlled via environment variable
USE_SELENIUM = os.getenv('USE_SELENIUM', 'false').lower() == 'true'

def get_scraper(scraper_name: str) -> Optional['BaseScraper']:
    """Get a scraper instance by name.
    
    Args:
        scraper_name: Name of the scraper to get
        
    Returns:
        Scraper instance or None if not found
    """
    # Import here to avoid circular imports
    from scrapers.autotrader import AutoTraderScraper
    from scrapers.gumtree import GumtreeScraper
    
    # Use Selenium-based scrapers if enabled
    if USE_SELENIUM:
        try:
            from selenium_integration import get_selenium_scraper
            
            selenium_scraper = get_selenium_scraper(scraper_name)
            if selenium_scraper:
                logger.info(f"Using Selenium-based scraper for {scraper_name}")
                return selenium_scraper
            else:
                logger.warning(f"Selenium scraper not found for {scraper_name}, falling back to BeautifulSoup")
        except ImportError as e:
            logger.warning(f"Selenium integration not available: {e}")
            logger.warning("Falling back to BeautifulSoup-based scrapers")
    
    # Default to BeautifulSoup-based scrapers
    scrapers = {
        "autotrader": AutoTraderScraper(),
        "gumtree": GumtreeScraper(),
        # Add more scrapers here as they are implemented
    }
    
    scraper = scrapers.get(scraper_name.lower())
    
    if not scraper:
        logger.warning(f"Scraper '{scraper_name}' not found")
        
    return scraper

def run_all_scrapers(preferences_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Run all available scrapers with the given preferences.
    
    Args:
        preferences_list: List of preference dictionaries
        
    Returns:
        Dictionary mapping scraper names to lists of listings
    """
    # Import here to avoid circular imports
    from scrapers.autotrader import AutoTraderScraper
    from scrapers.gumtree import GumtreeScraper
    
    available_scrapers = {}
    
    # Use Selenium-based scrapers if enabled
    if USE_SELENIUM:
        try:
            from selenium_integration import get_selenium_scraper
            
            autotrader_selenium = get_selenium_scraper("autotrader")
            gumtree_selenium = get_selenium_scraper("gumtree")
            
            if autotrader_selenium:
                available_scrapers["autotrader"] = autotrader_selenium
            else:
                available_scrapers["autotrader"] = AutoTraderScraper()
                
            if gumtree_selenium:
                available_scrapers["gumtree"] = gumtree_selenium
            else:
                available_scrapers["gumtree"] = GumtreeScraper()
                
            logger.info("Using Selenium-based scrapers where available")
        except ImportError as e:
            logger.warning(f"Selenium integration not available: {e}")
            logger.warning("Using BeautifulSoup-based scrapers")
            
            available_scrapers = {
                "autotrader": AutoTraderScraper(),
                "gumtree": GumtreeScraper(),
            }
    else:
        # Default to BeautifulSoup-based scrapers
        available_scrapers = {
            "autotrader": AutoTraderScraper(),
            "gumtree": GumtreeScraper(),
            # Add more scrapers here as they are implemented
        }
    
    results = {}
    
    for name, scraper in available_scrapers.items():
        logger.info(f"Running scraper: {name}")
        try:
            listings = scraper.run_scraper(preferences_list)
            results[name] = listings
            logger.info(f"Scraper {name} found {len(listings)} listings")
        except Exception as e:
            logger.error(f"Error running scraper {name}: {e}")
            results[name] = []
    
    return results

# Test function to check if Selenium is enabled
def is_selenium_enabled():
    """Check if Selenium-based scrapers are enabled."""
    return USE_SELENIUM
