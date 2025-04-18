"""
Scrapers package for AutoSniper.
This package contains scrapers for different car listing sites.
"""

from .base import BaseScraper
from .autotrader import AutoTraderScraper

__all__ = ['BaseScraper', 'AutoTraderScraper', 'get_scraper']

def get_scraper(scraper_name: str):
    """Get a scraper instance by name.
    
    Args:
        scraper_name: Name of the scraper to get
        
    Returns:
        Scraper instance or None if not found
    """
    scrapers = {
        "autotrader": AutoTraderScraper(),
        # Add more scrapers here as they are implemented
    }
    
    return scrapers.get(scraper_name.lower())
