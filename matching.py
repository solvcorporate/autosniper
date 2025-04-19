"""
Matching algorithm to compare car listings against user preferences.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple

# Import the scoring engine
from scoring import get_scoring_engine, SAMPLE_MARKET_DATA

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("matching")

class MatchingEngine:
    """Engine for matching car listings to user preferences."""
    
    def __init__(self, market_data: Optional[Dict[str, Any]] = None):
        """Initialize the matching engine.
        
        Args:
            market_data: Optional dictionary with market average data
        """
        self.logger = logging.getLogger("matching.engine")
        
        # Initialize the scoring engine
        self.scoring_engine = get_scoring_engine(market_data or SAMPLE_MARKET_DATA)
        
    def find_matches(self, listings: List[Dict[str, Any]], user_preferences: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Find matches between listings and user preferences.
        
        Args:
            listings: List of car listing dictionaries
            user_preferences: List of user preference dictionaries with user_id
            
        Returns:
            Dictionary mapping user_ids to lists of matching listings
        """
        # First, score all the listings
        scored_listings = self.scoring_engine.batch_score_listings(listings)
        
        matches = {}
        
        # Process each user's preferences
        for preference in user_preferences:
            user_id = preference.get('user_id')
            if not user_id:
                self.logger.warning("Preference missing user_id, skipping")
                continue
            
            # Find matching listings for this user's preferences
            user_matches = self.match_listings_to_preference(scored_listings, preference)
            
            # Only include users with matches
            if user_matches:
                # Convert user_id to string for consistency
                user_id_str = str(user_id)
                
                # Initialize if this is the first match for this user
                if user_id_str not in matches:
                    matches[user_id_str] = []
                
                # Add matches to the user's list
                matches[user_id_str].extend(user_matches)
                
                self.logger.info(f"Found {len(user_matches)} matches for user {user_id}")
            else:
                self.logger.info(f"No matches found for user {user_id}")
        
        # Sort each user's matches by score (if present) or price
        for user_id, user_matches in matches.items():
            if user_matches and 'score' in user_matches[0]:
                # Sort by score (descending) for scored listings
                matches[user_id] = sorted(user_matches, key=lambda x: x.get('score', 0), reverse=True)
            else:
                # Fallback to sorting by price (ascending)
                matches[user_id] = sorted(user_matches, key=lambda x: x.get('price', 0))
        
        return matches
    
    def match_listings_to_preference(self, listings: List[Dict[str, Any]], preference: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match a list of listings against a single user preference.
        
        Args:
            listings: List of car listing dictionaries
            preference: User preference dictionary
            
        Returns:
            List of matching listings
        """
        matches = []
        
        # Extract preference criteria
        make = preference.get('make', '').lower()
        model = preference.get('model', '').lower()
        min_year = preference.get('min_year', 0)
        max_year = preference.get('max_year', 9999)
        min_price = preference.get('min_price', 0)
        max_price = preference.get('max_price', 9999999)
        location = preference.get('location', '').lower()
        fuel_type = preference.get('fuel_type', 'Any').lower()
        transmission = preference.get('transmission', 'Any').lower()
        
        # Process each listing
        for listing in listings:
            # Skip listings that have already been matched/alerted for this user
            if 'matched_to' in listing and str(preference.get('user_id', '')) in str(listing.get('matched_to', '')):
                continue
            
            # Apply matching criteria
            match, match_details = self._check_match(listing, make, model, min_year, max_year, 
                                    min_price, max_price, location, fuel_type, transmission)
            
            # Add match details to the listing copy
            if match:
                listing_copy = listing.copy()
                listing_copy['match_details'] = match_details
                listing_copy['preference_id'] = preference.get('id', '')
                listing_copy['user_id'] = preference.get('user_id', '')
                matches.append(listing_copy)
        
        self.logger.info(f"Found {len(matches)} matches for preference: {make} {model}")
        return matches
    
    def _check_match(self, listing: Dict[str, Any], make: str, model: str, 
                    min_year: int, max_year: int, min_price: int, max_price: int,
                    location: str, fuel_type: str, transmission: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if a listing matches the specified criteria.
        
        Args:
            listing: Car listing dictionary
            make: Car make to match
            model: Car model to match
            min_year: Minimum year
            max_year: Maximum year
            min_price: Minimum price
            max_price: Maximum price
            location: Location preference
            fuel_type: Fuel type preference
            transmission: Transmission preference
            
        Returns:
            Tuple of (match_result, match_details)
        """
        match_details = {}
        
        # Skip suspicious listings (marked by scoring engine)
        if listing.get('score_details', {}).get('suspicious', False):
            return False, {}
        
        # Check make - must match unless preference is 'any'
        listing_make = listing.get('make', '').lower()
        if make != 'any' and make and listing_make:
            # Check if listing make contains the preference make or vice versa
            if make not in listing_make and listing_make not in make:
                return False, {}
        match_details['make_match'] = True
        
        # Check model - must match unless preference is 'any'
        listing_model = listing.get('model', '').lower()
        if model != 'any' and model and listing_model:
            # Check if listing model contains the preference model or vice versa
            if model not in listing_model and listing_model not in model:
                return False, match_details
        match_details['model_match'] = True
        
        # Check year range
        listing_year = listing.get('year')
        if listing_year:
            if listing_year < min_year or listing_year > max_year:
                return False, match_details
        match_details['year_match'] = True
        
        # Check price range
        listing_price = listing.get('price')
        if listing_price:
            if listing_price < min_price or listing_price > max_price:
                return False, match_details
        match_details['price_match'] = True
        
        # Check location (if specified)
        if location and location.lower() != 'any':
            listing_location = listing.get('location', '').lower()
            
            # Extract city/region information from location strings
            location_city = self._extract_location(location)
            listing_location_city = self._extract_location(listing_location)
            
            # Location match is more flexible - we just check if the city names overlap
            if location_city and listing_location_city:
                if location_city not in listing_location_city and listing_location_city not in location_city:
                    # Location doesn't match
                    match_details['location_match'] = False
                else:
                    match_details['location_match'] = True
            else:
                # If we can't extract location properly, don't filter on it
                match_details['location_match'] = True
        else:
            match_details['location_match'] = True
        
        # Check fuel type (if specified and not 'Any')
        if fuel_type and fuel_type.lower() != 'any':
            listing_fuel_type = listing.get('fuel_type', '').lower()
            if listing_fuel_type and fuel_type not in listing_fuel_type:
                match_details['fuel_type_match'] = False
            else:
                match_details['fuel_type_match'] = True
        else:
            match_details['fuel_type_match'] = True
        
        # Check transmission (if specified and not 'Any')
        if transmission and transmission.lower() != 'any':
            listing_transmission = listing.get('transmission', '').lower()
            if listing_transmission and transmission not in listing_transmission:
                match_details['transmission_match'] = False
            else:
                match_details['transmission_match'] = True
        else:
            match_details['transmission_match'] = True
        
        # Consider it a match if all required fields match
        is_match = (match_details.get('make_match', False) and 
                   match_details.get('model_match', False) and
                   match_details.get('year_match', False) and
                   match_details.get('price_match', False) and
                   match_details.get('location_match', True) and   # Optional matches
                   match_details.get('fuel_type_match', True) and  # Optional matches
                   match_details.get('transmission_match', True))  # Optional matches
        
        # Add the score and grade to the match details if present
        if 'score' in listing:
            match_details['score'] = listing['score']
            match_details['grade'] = listing['grade']
        
        return is_match, match_details
    
    def _extract_location(self, location_str: str) -> str:
        """Extract city/region from a location string.
        
        Args:
            location_str: Location string to process
            
        Returns:
            Extracted city/region name
        """
        # Check for UK/Ireland format (e.g., 'UK: London')
        if ':' in location_str:
            parts = location_str.split(':')
            if len(parts) > 1:
                return parts[1].strip().lower()
        
        # Otherwise just return the cleaned string
        return location_str.strip().lower()


# Helper function to create a matching engine instance
def get_matching_engine(market_data: Optional[Dict[str, Any]] = None):
    """Get a MatchingEngine instance.
    
    Args:
        market_data: Optional dictionary with market average data
        
    Returns:
        MatchingEngine instance
    """
    return MatchingEngine(market_data)


# Test function
def test_matching():
    """Test the matching engine with sample data."""
    engine = get_matching_engine(SAMPLE_MARKET_DATA)
    
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
    
    # Find matches
    matches = engine.find_matches(listings, preferences)
    
    # Print results
    for user_id, user_matches in matches.items():
        print(f"User {user_id} has {len(user_matches)} matches:")
        for match in user_matches:
            print(f"- {match['make']} {match['model']} ({match['year']}): £{match['price']}")
            if 'score' in match:
                print(f"  Score: {match['score']} ({match['grade']})")
    
    return matches


if __name__ == "__main__":
    test_matching()
