"""
Scrapers package for AutoSniper.
This package contains scrapers for different car listing sites.
"""
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scrapers")

# Import the scraper classes
from .base import BaseScraper
from .autotrader import AutoTraderScraper
from .gumtree import GumtreeScraper

def get_scraper(scraper_name: str) -> Optional[BaseScraper]:
    """Get a scraper instance by name.
    
    Args:
        scraper_name: Name of the scraper to get
        
    Returns:
        Scraper instance or None if not found
    """
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

# Helper function for backward compatibility
def is_selenium_enabled():
    """Check if Selenium-based scrapers are enabled (always returns False now)."""
    return False

__all__ = [
    'BaseScraper', 
    'AutoTraderScraper', 
    'GumtreeScraper',
    'get_scraper',
    'run_all_scrapers',
    'is_selenium_enabled'
]
