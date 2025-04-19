"""
Test script for the scoring system.
"""
import logging
from scoring import get_scoring_engine, SAMPLE_MARKET_DATA

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_scoring")

def print_score_details(listing):
    """Print the scoring details for a listing in a readable format."""
    print(f"{listing['make']} {listing['model']} ({listing['year']}):")
    print(f"  Price: £{listing['price']}")
    print(f"  Mileage: {listing.get('mileage', 'N/A')}")
    print(f"  Score: {listing.get('score', 'N/A')}")
    print(f"  Grade: {listing.get('grade', 'N/A')}")
    
    if 'score_details' in listing:
        details = listing['score_details']
        print(f"  Price Score: {details.get('price_score', 'N/A')}")
        print(f"  Mileage Score: {details.get('mileage_score', 'N/A')}")
        if details.get('suspicious', False):
            print(f"  SUSPICIOUS: {details.get('reasons', ['Unknown reason'])}")
    
    print()

def test_scoring_engine():
    """Test the scoring engine with various scenarios."""
    logger.info("Testing scoring engine...")
    
    # Create scoring engine with sample market data
    engine = get_scoring_engine(SAMPLE_MARKET_DATA)
    
    # Test case 1: Good deals
    good_deals = [
        {
            'id': '1',
            'make': 'Ford',
            'model': 'Focus',
            'year': 2018,
            'price': 7500,  # Significantly below market (12000)
            'mileage': 45000,  # Slightly above average
            'location': 'Manchester, UK'
        },
        {
            'id': '3',
            'make': 'BMW',
            'model': '3 Series',
            'year': 2017,
            'price': 10000,  # Well below market (16000)
            'mileage': 80000,  # Above average
            'location': 'London, UK'
        }
    ]
    
    logger.info("Test case 1: Good deals (below market price)")
    scored_good_deals = engine.batch_score_listings(good_deals)
    
    print("Good Deals Scoring Results:")
    print("---------------------------")
    for listing in scored_good_deals:
        print_score_details(listing)
    
    # Test case 2: Average and poor deals
    average_deals = [
        {
            'id': '2',
            'make': 'Volkswagen',
            'model': 'Golf',
            'year': 2019,
            'price': 16500,  # Slightly above market (16000)
            'mileage': 25000,  # Below average
            'location': 'Liverpool, UK'
        },
        {
            'id': '4',
            'make': 'Mercedes',
            'model': 'S Class',  # Not in our market data
            'year': 2018,
            'price': 35000,
            'mileage': 25000,  # Below average
            'location': 'Manchester, UK'
        }
    ]
    
    logger.info("Test case 2: Average deals (at or above market price)")
    scored_average_deals = engine.batch_score_listings(average_deals)
    
    print("Average Deals Scoring Results:")
    print("-----------------------------")
    for listing in scored_average_deals:
        print_score_details(listing)
    
    # Test case 3: Suspicious listings
    suspicious_deals = [
        {
            'id': '6',
            'make': 'Ford',
            'model': 'Focus',
            'year': 2022,
            'price': 500,  # Suspiciously low
            'mileage': 5000,
            'location': 'Leeds, UK'
        },
        {
            'id': '7',
            'make': 'Audi',
            'model': 'A4',
            'year': 2020,
            'price': 999,  # Suspiciously low for a recent car
            'mileage': 20000,
            'location': 'Birmingham, UK'
        }
    ]
    
    logger.info("Test case 3: Suspicious deals (unrealistically low prices)")
    scored_suspicious_deals = engine.batch_score_listings(suspicious_deals)
    
    print("Suspicious Deals Scoring Results:")
    print("--------------------------------")
    for listing in scored_suspicious_deals:
        print_score_details(listing)
    
    # Test case 4: Missing data
    incomplete_deals = [
        {
            'id': '8',
            'make': 'Toyota',
            'model': 'Corolla',
            'year': 2019,
            'price': 12000,
            # Missing mileage
            'location': 'Glasgow, UK'
        },
        {
            'id': '9',
            'make': 'Honda',
            'model': 'Civic',
            # Missing year
            'price': 8000,
            'mileage': 60000,
            'location': 'Belfast, UK'
        }
    ]
    
    logger.info("Test case 4: Incomplete deals (missing data)")
    scored_incomplete_deals = engine.batch_score_listings(incomplete_deals)
    
    print("Incomplete Deals Scoring Results:")
    print("--------------------------------")
    for listing in scored_incomplete_deals:
        print_score_details(listing)
    
    return {
        "good_deals": scored_good_deals,
        "average_deals": scored_average_deals,
        "suspicious_deals": scored_suspicious_deals,
        "incomplete_deals": scored_incomplete_deals
    }

if __name__ == "__main__":
    test_scoring_engine()
