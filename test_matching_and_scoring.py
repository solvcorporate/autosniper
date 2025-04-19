"""
Test script for the combined matching and scoring system.
"""
import logging
from matching import get_matching_engine
from scoring import get_scoring_engine, SAMPLE_MARKET_DATA

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_combined")

def print_match_details(match):
    """Print the match and scoring details in a readable format."""
    print(f"{match['make']} {match['model']} ({match['year']}):")
    print(f"  Price: £{match['price']}")
    print(f"  Mileage: {match.get('mileage', 'N/A')}")
    
    if 'score' in match:
        print(f"  Score: {match['score']} ({match['grade']})")
    
    if 'score_details' in match:
        details = match['score_details']
        print(f"  Price Score: {details.get('price_score', 'N/A')}")
        print(f"  Mileage Score: {details.get('mileage_score', 'N/A')}")
        if details.get('suspicious', False):
            print(f"  SUSPICIOUS: {details.get('reasons', ['Unknown reason'])}")
    
    print()

def test_combined_system():
    """Test the complete matching and scoring system."""
    logger.info("Testing combined matching and scoring system...")
    
    # Create matching engine (this will also create a scoring engine)
    matching_engine = get_matching_engine(SAMPLE_MARKET_DATA)
    
    # Sample listings
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
            'make': 'Volkswagen',
            'model': 'Golf',
            'year': 2019,
            'price': 16500,  # Average deal - slightly above market (16000)
            'mileage': 25000,  # Low mileage
            'location': 'Liverpool, UK',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic',
            'url': 'https://example.com/listing2'
        },
        {
            'id': '3',
            'make': 'BMW',
            'model': '3 Series',
            'year': 2017,
            'price': 10000,  # Very good deal - well below market (16000)
            'mileage': 80000,  # Higher mileage
            'location': 'London, UK',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic',
            'url': 'https://example.com/listing3'
        },
        {
            'id': '4',
            'make': 'Mercedes',
            'model': 'S Class',
            'year': 2020,
            'price': 500,  # Suspiciously low - should be flagged
            'mileage': 15000,
            'location': 'Manchester, UK',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic',
            'url': 'https://example.com/listing4'
        },
        {
            'id': '5',
            'make': 'Toyota',
            'model': 'Corolla',
            'year': 2019,
            'price': 12000,
            'mileage': 35000,
            'location': 'Leeds, UK',
            'fuel_type': 'Hybrid',
            'transmission': 'Automatic',
            'url': 'https://example.com/listing5'
        },
        {
            'id': '6',
            'make': 'Audi',
            'model': 'A4',
            'year': 2020,
            'price': 24000,
            'mileage': 15000,
            'location': 'Birmingham, UK',
            'fuel_type': 'Petrol',
            'transmission': 'Automatic',
            'url': 'https://example.com/listing6'
        }
    ]
    
    # Sample user preferences
    preferences = [
        {
            'user_id': '123',
            'make': 'Ford',
            'model': 'Focus',
            'min_year': 2016,
            'max_year': 2020,
            'min_price': 5000,
            'max_price': 12000,
            'location': 'UK: Manchester',
            'fuel_type': 'Any',
            'transmission': 'Any'
        },
        {
            'user_id': '456',
            'make': 'BMW',
            'model': '3 Series',
            'min_year': 2015,
            'max_year': 2020,
            'min_price': 8000,
            'max_price': 20000,
            'location': 'UK: London',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic'
        },
        {
            'user_id': '789',
            'make': 'Toyota',
            'model': 'Corolla',
            'min_year': 2018,
            'max_year': 2022,
            'min_price': 8000,
            'max_price': 18000,
            'location': 'UK: Any',
            'fuel_type': 'Hybrid',
            'transmission': 'Any'
        }
    ]
    
    # Find matches (the matching engine will also score listings)
    matches = matching_engine.find_matches(listings, preferences)
    
    # Print results
    print("\nMatching and Scoring Results:")
    print("============================\n")
    
    for user_id, user_matches in matches.items():
        print(f"User {user_id} has {len(user_matches)} matches:")
        print("-" * 40)
        
        for match in user_matches:
            print_match_details(match)
        
        print("\n")
    
    # Print summary of all listings with scores
    print("All Listings with Scores:")
    print("=======================\n")
    
    # Score all listings directly
    scoring_engine = get_scoring_engine(SAMPLE_MARKET_DATA)
    scored_listings = scoring_engine.batch_score_listings(listings)
    
    for listing in sorted(scored_listings, key=lambda x: x.get('score', 0), reverse=True):
        print_match_details(listing)
    
    return matches, scored_listings


if __name__ == "__main__":
    test_combined_system()
