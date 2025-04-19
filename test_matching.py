"""
Test script for the matching algorithm.
"""
import logging
from matching import get_matching_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_matching")

def print_matches(matches):
    """Print matching results in a readable format.
    
    Args:
        matches: Dictionary mapping user_ids to lists of matching listings
    """
    if not matches:
        print("No matches found.")
        return
        
    for user_id, user_matches in matches.items():
        print(f"User {user_id} has {len(user_matches)} matches:")
        for i, match in enumerate(user_matches, 1):
            print(f"  {i}. {match['make']} {match['model']} ({match['year']})")
            print(f"     Price: £{match['price']}, Mileage: {match.get('mileage', 'N/A')}")
            print(f"     Location: {match['location']}")
            if 'fuel_type' in match and match['fuel_type']:
                print(f"     Fuel: {match['fuel_type']}")
            if 'transmission' in match and match['transmission']:
                print(f"     Transmission: {match['transmission']}")
            print(f"     URL: {match['url']}")
            print()

def test_matching_algorithm():
    """Test the matching algorithm with various scenarios."""
    logger.info("Testing matching algorithm...")
    
    # Create matching engine
    engine = get_matching_engine()
    
    # Sample listings
    listings = [
        {
            'id': '1',
            'make': 'Ford',
            'model': 'Focus',
            'year': 2018,
            'price': 7500,
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
            'price': 12000,
            'mileage': 30000,
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
            'price': 15000,
            'mileage': 55000,
            'location': 'London, UK',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic',
            'url': 'https://example.com/listing3'
        },
        {
            'id': '4',
            'make': 'Mercedes',
            'model': 'S Class',
            'year': 2018,
            'price': 35000,
            'mileage': 25000,
            'location': 'Manchester, UK',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic',
            'url': 'https://example.com/listing4'
        },
        {
            'id': '5',
            'make': 'Ford',
            'model': 'Focus',
            'year': 2016,
            'price': 6000,
            'mileage': 65000,
            'location': 'Dublin, Ireland',
            'fuel_type': 'Petrol',
            'transmission': 'Manual',
            'url': 'https://example.com/listing5'
        }
    ]
    
    # Test case 1: Basic matching - should match listing 1
    preferences1 = [
        {
            'user_id': '123',
            'make': 'Ford',
            'model': 'Focus',
            'min_year': 2016,
            'max_year': 2020,
            'min_price': 5000,
            'max_price': 10000,
            'location': 'UK: Manchester',
            'fuel_type': 'Any',
            'transmission': 'Any'
        }
    ]
    
    logger.info("Test case 1: Basic matching - Ford Focus in Manchester")
    matches1 = engine.find_matches(listings, preferences1)
    print_matches(matches1)
    
    # Test case 2: Multiple preferences - user 456 should match listing 3
    preferences2 = [
        {
            'user_id': '123',
            'make': 'Ford',
            'model': 'Focus',
            'min_year': 2016,
            'max_year': 2020,
            'min_price': 5000,
            'max_price': 10000,
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
            'min_price': 10000,
            'max_price': 20000,
            'location': 'UK: London',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic'
        }
    ]
    
    logger.info("Test case 2: Multiple preferences - Different users with different cars")
    matches2 = engine.find_matches(listings, preferences2)
    print_matches(matches2)
    
    # Test case 3: Location flexibility - should match listing 5 (Dublin)
    preferences3 = [
        {
            'user_id': '789',
            'make': 'Ford',
            'model': 'Focus',
            'min_year': 2015,
            'max_year': 2020,
            'min_price': 5000,
            'max_price': 10000,
            'location': 'Ireland: Dublin',
            'fuel_type': 'Petrol',
            'transmission': 'Manual'
        }
    ]
    
    logger.info("Test case 3: Location flexibility - Ford Focus in Dublin")
    matches3 = engine.find_matches(listings, preferences3)
    print_matches(matches3)
    
    # Test case 4: Multiple matches for one user - should match listings 1 and 5
    preferences4 = [
        {
            'user_id': '123',
            'make': 'Ford',
            'model': 'Focus',
            'min_year': 2015,
            'max_year': 2020,
            'min_price': 5000,
            'max_price': 10000,
            'location': 'Any',  # Any location is fine
            'fuel_type': 'Petrol',
            'transmission': 'Manual'
        }
    ]
    
    logger.info("Test case 4: Multiple matches - Ford Focus anywhere")
    matches4 = engine.find_matches(listings, preferences4)
    print_matches(matches4)
    
    # Test case 5: Specific fuel type and transmission - should match listing 3
    preferences5 = [
        {
            'user_id': '456',
            'make': 'BMW',
            'model': '3 Series',
            'min_year': 2015,
            'max_year': 2020,
            'min_price': 10000,
            'max_price': 20000,
            'location': 'Any',
            'fuel_type': 'Diesel',
            'transmission': 'Automatic'
        }
    ]
    
    logger.info("Test case 5: Specific fuel type and transmission - BMW with Diesel/Auto")
    matches5 = engine.find_matches(listings, preferences5)
    print_matches(matches5)
    
    # Return all matches for further analysis
    return {
        "test1": matches1,
        "test2": matches2,
        "test3": matches3,
        "test4": matches4,
        "test5": matches5
    }


if __name__ == "__main__":
    test_matching_algorithm()
