"""
Test script for the Gumtree scraper.
"""
import logging
from scrapers.gumtree import GumtreeScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_gumtree")

def test_gumtree_scraper():
    """Test the Gumtree scraper with example preferences."""
    logger.info("Testing Gumtree scraper...")
    
    # Create scraper instance
    scraper = GumtreeScraper()
    
    # Define test preferences
    test_preferences = {
        'make': 'Toyota',
        'model': 'Corolla',
        'min_year': 2015,
        'max_year': 2022,
        'min_price': 5000,
        'max_price': 15000,
        'location': 'UK: London'
    }
    
    # Construct search URL
    search_url = scraper.construct_search_url(test_preferences)
    logger.info(f"Search URL: {search_url}")
    
    # Run the search
    listings = scraper.search(test_preferences)
    
    # Log results
    logger.info(f"Found {len(listings)} listings")
    
    # Display the first 3 listings
    for i, listing in enumerate(listings[:3], 1):
        logger.info(f"Listing {i}:")
        for key, value in listing.items():
            logger.info(f"  {key}: {value}")
    
    return listings

if __name__ == "__main__":
    test_gumtree_scraper()
