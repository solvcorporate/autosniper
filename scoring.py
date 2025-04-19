"""
Scoring system for evaluating car listings.
"""

import logging
import re
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scoring")

# Reference data for typical mileage by car age (in years)
# Format: {years_old: expected_mileage}
TYPICAL_MILEAGE = {
    1: 10000,    # 1-year-old car: 10,000 miles
    2: 20000,    # 2-year-old car: 20,000 miles
    3: 30000,
    4: 40000,
    5: 48000,
    6: 56000,
    7: 64000,
    8: 72000,
    9: 80000,
    10: 88000,
    11: 95000,
    12: 102000,
    13: 109000,
    14: 115000,
    15: 121000,
    16: 127000,
    17: 133000,
    18: 138000,
    19: 143000,
    20: 148000
}

# Price depreciation curve - approximate values for typical car
# Format: {years_old: percentage_of_original_value}
PRICE_DEPRECIATION = {
    0: 1.00,    # New car: 100% of value
    1: 0.80,    # 1-year-old car: 80% of original value
    2: 0.70,
    3: 0.60,
    4: 0.50,
    5: 0.42,
    6: 0.36,
    7: 0.31,
    8: 0.27,
    9: 0.24,
    10: 0.21,
    12: 0.18,
    14: 0.15,
    16: 0.13,
    18: 0.11,
    20: 0.10
}

# Letter grades and their corresponding score ranges
GRADE_RANGES = {
    'A+': (90, 100),
    'A': (80, 89),
    'B': (70, 79),
    'C': (60, 69),
    'D': (0, 59)
}

class ScoringEngine:
    """Engine for scoring car listings based on value metrics."""
    
    def __init__(self, market_data: Optional[Dict[str, Any]] = None):
        """Initialize the scoring engine.
        
        Args:
            market_data: Optional dictionary with market average data
        """
        self.logger = logging.getLogger("scoring.engine")
        # Market data keyed by make+model, containing average prices by year
        self.market_data = market_data or {}
    
    def score_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Score a car listing based on multiple factors.
        
        Args:
            listing: Car listing dictionary
            
        Returns:
            Updated listing with score and score details
        """
        # Make a copy of the listing to avoid modifying the original
        scored_listing = listing.copy()
        
        # Check for suspicious listings (e.g., extremely low prices)
        if self._is_suspicious(scored_listing):
            scored_listing['score'] = 0
            scored_listing['grade'] = 'F'
            scored_listing['score_details'] = {
                'price_score': 0,
                'mileage_score': 0,
                'suspicious': True,
                'reasons': ['Suspiciously low price or missing critical information']
            }
            return scored_listing
        
        # Calculate individual scores
        price_score = self._calculate_price_score(scored_listing)
        mileage_score = self._calculate_mileage_score(scored_listing)
        
        # Calculate overall score (weighted average)
        # Price is 60% of the score, mileage is 40%
        overall_score = (price_score * 0.6) + (mileage_score * 0.4)
        
        # Determine grade
        grade = self._get_grade(overall_score)
        
        # Add scores to the listing
        scored_listing['score'] = round(overall_score, 1)
        scored_listing['grade'] = grade
        scored_listing['score_details'] = {
            'price_score': round(price_score, 1),
            'mileage_score': round(mileage_score, 1),
            'suspicious': False
        }
        
        return scored_listing
    
    def batch_score_listings(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score multiple listings.
        
        Args:
            listings: List of car listing dictionaries
            
        Returns:
            List of listings with scores added
        """
        scored_listings = []
        
        for listing in listings:
            try:
                scored_listing = self.score_listing(listing)
                scored_listings.append(scored_listing)
            except Exception as e:
                self.logger.error(f"Error scoring listing: {e}")
                # Add the unscored listing to keep the same length
                scored_listings.append(listing)
        
        return scored_listings
    
    def _is_suspicious(self, listing: Dict[str, Any]) -> bool:
        """Check if a listing seems suspicious or potentially misleading.
        
        Args:
            listing: Car listing dictionary
            
        Returns:
            True if the listing is suspicious, False otherwise
        """
        # Check for very low price (less than £500/€500)
        price = listing.get('price')
        if price is not None and price < 500:
            return True
        
        # Check for missing critical information
        if listing.get('make') is None or listing.get('model') is None:
            return True
        
        # Check for suspiciously low price compared to car age
        year = listing.get('year')
        current_year = datetime.now().year
        
        if year is not None and price is not None:
            car_age = current_year - year
            
            # Car less than 3 years old should not be below £3000/€3000
            if car_age <= 3 and price < 3000:
                return True
            
            # Car less than 10 years old should not be below £1000/€1000
            if car_age <= 10 and price < 1000:
                return True
        
        return False
    
    def _calculate_price_score(self, listing: Dict[str, Any]) -> float:
        """Calculate a score based on the listing price compared to market average.
        
        Args:
            listing: Car listing dictionary
            
        Returns:
            Price score (0-100)
        """
        price = listing.get('price')
        make = listing.get('make', '').lower()
        model = listing.get('model', '').lower()
        year = listing.get('year')
        
        if not price or not make or not model or not year:
            return 50  # Neutral score if missing data
        
        # Try to get market average from our data
        market_average = self._get_market_average(make, model, year)
        
        if market_average:
            # Calculate how much below/above market average
            price_ratio = price / market_average
            
            # Score interpretation:
            # 1.0 = market average = 50 points
            # 0.8 = 20% below market = 70 points
            # 0.6 = 40% below market = 90 points
            # 0.5 or less = 50% or more below market = 100 points
            # 1.2 = 20% above market = 30 points
            # 1.4 or more = 40% or more above market = 10 points
            
            if price_ratio <= 0.5:
                return 100  # Exceptional deal (50% or more below market)
            elif price_ratio <= 0.9:
                # Linear scale from 60 to 90 for 10-50% below market
                return 90 - ((price_ratio - 0.5) * 75)
            elif price_ratio <= 1.1:
                # Linear scale from 40 to 60 for within 10% of market
                return 60 - ((price_ratio - 0.9) * 100)
            elif price_ratio <= 1.5:
                # Linear scale from 10 to 40 for 10-50% above market
                return 40 - ((price_ratio - 1.1) * 75)
            else:
                return 10  # Poor deal (50% or more above market)
        else:
            # No market data available - calculate based on depreciation curve
            current_year = datetime.now().year
            car_age = current_year - year
            
            if car_age < 0:
                # Future year cars (probably an error)
                return 50
            
            # Approximate new car value based on current price and typical depreciation
            # Find the nearest age in our depreciation curve
            closest_age = min(PRICE_DEPRECIATION.keys(), key=lambda k: abs(k - car_age))
            depreciation_factor = PRICE_DEPRECIATION.get(closest_age, 0.1)  # Default to 10% if too old
            
            # Estimate original price
            estimated_original_price = price / depreciation_factor
            
            # Now calculate expected price for this age
            expected_price = estimated_original_price * depreciation_factor
            
            # Calculate how the actual price compares to expected
            price_ratio = price / expected_price
            
            # Similar scoring scale as above
            if price_ratio <= 0.7:
                return 90  # Very good deal
            elif price_ratio <= 0.9:
                return 70  # Good deal
            elif price_ratio <= 1.1:
                return 50  # Fair price
            elif price_ratio <= 1.3:
                return 30  # Somewhat overpriced
            else:
                return 10  # Significantly overpriced
    
    def _calculate_mileage_score(self, listing: Dict[str, Any]) -> float:
        """Calculate a score based on the listing mileage compared to typical mileage.
        
        Args:
            listing: Car listing dictionary
            
        Returns:
            Mileage score (0-100)
        """
        mileage = listing.get('mileage')
        year = listing.get('year')
        
        if not mileage or not year:
            return 50  # Neutral score if missing data
        
        current_year = datetime.now().year
        car_age = current_year - year
        
        if car_age < 0:
            # Future year cars (probably an error)
            return 50
        
        # Find the closest age in our typical mileage data
        closest_age = min(TYPICAL_MILEAGE.keys(), key=lambda k: abs(k - car_age))
        expected_mileage = TYPICAL_MILEAGE.get(closest_age, 150000)  # Default for very old cars
        
        # Linear interpolation for more precise expected mileage
        if car_age in TYPICAL_MILEAGE:
            expected_mileage = TYPICAL_MILEAGE[car_age]
        else:
            # Find the two closest ages and interpolate
            ages = sorted(TYPICAL_MILEAGE.keys())
            if car_age < ages[0]:
                # Younger than our youngest data point
                expected_mileage = TYPICAL_MILEAGE[ages[0]] * (car_age / ages[0])
            elif car_age > ages[-1]:
                # Older than our oldest data point
                expected_mileage = TYPICAL_MILEAGE[ages[-1]] + (5000 * (car_age - ages[-1]))
            else:
                # Interpolate between two points
                for i in range(len(ages)-1):
                    if ages[i] <= car_age < ages[i+1]:
                        fraction = (car_age - ages[i]) / (ages[i+1] - ages[i])
                        expected_mileage = TYPICAL_MILEAGE[ages[i]] + (fraction * (TYPICAL_MILEAGE[ages[i+1]] - TYPICAL_MILEAGE[ages[i]]))
                        break
        
        # Calculate mileage ratio (actual vs expected)
        mileage_ratio = mileage / expected_mileage
        
        # Score interpretation:
        # 1.0 = typical mileage = 50 points
        # 0.7 = 30% below typical = 70 points
        # 0.5 or less = 50% or more below typical = 90 points
        # 1.3 = 30% above typical = 30 points
        # 1.5 or more = 50% or more above typical = 10 points
        
        if mileage_ratio <= 0.5:
            return 90  # Very low mileage
        elif mileage_ratio <= 0.9:
            # Linear scale from 55 to 90 for 10-50% below typical
            return 55 + ((0.9 - mileage_ratio) * 87.5)
        elif mileage_ratio <= 1.1:
            # Linear scale from 45 to 55 for within 10% of typical
            return 55 - ((mileage_ratio - 0.9) * 50)
        elif mileage_ratio <= 1.5:
            # Linear scale from 10 to 45 for 10-50% above typical
            return 45 - ((mileage_ratio - 1.1) * 87.5)
        else:
            return 10  # Very high mileage
    
    def _get_market_average(self, make: str, model: str, year: int) -> Optional[float]:
        """Get the market average price for a specific make/model/year.
        
        Args:
            make: Car make
            model: Car model
            year: Car year
            
        Returns:
            Market average price if available, None otherwise
        """
        if not self.market_data:
            return None
        
        # Normalize make and model
        make_model_key = f"{make.lower()}_{model.lower()}"
        
        # Check if we have data for this make/model
        if make_model_key in self.market_data:
            model_data = self.market_data[make_model_key]
            
            # Check if we have data for this specific year
            year_str = str(year)
            if year_str in model_data:
                return model_data[year_str]
            
            # Try to interpolate from surrounding years
            available_years = sorted([int(y) for y in model_data.keys()])
            if not available_years:
                return None
                
            if year < available_years[0]:
                # Earlier than our earliest data
                return None
            elif year > available_years[-1]:
                # Later than our latest data
                return None
            else:
                # Interpolate between two surrounding years
                for i in range(len(available_years)-1):
                    if available_years[i] <= year < available_years[i+1]:
                        year1, year2 = available_years[i], available_years[i+1]
                        price1 = model_data[str(year1)]
                        price2 = model_data[str(year2)]
                        
                        # Linear interpolation
                        fraction = (year - year1) / (year2 - year1)
                        return price1 + (fraction * (price2 - price1))
        
        return None
    
    def _get_grade(self, score: float) -> str:
        """Convert a numerical score to a letter grade.
        
        Args:
            score: Numerical score (0-100)
            
        Returns:
            Letter grade (A+, A, B, C, D, F)
        """
        if score < 0:
            return 'F'  # For any negative scores (shouldn't happen)
        
        for grade, (min_score, max_score) in GRADE_RANGES.items():
            if min_score <= score <= max_score:
                return grade
        
        return 'F'  # Default for any scores outside our ranges


# Helper function to create a scoring engine instance
def get_scoring_engine(market_data: Optional[Dict[str, Any]] = None) -> ScoringEngine:
    """Get a ScoringEngine instance.
    
    Args:
        market_data: Optional dictionary with market average data
        
    Returns:
        ScoringEngine instance
    """
    return ScoringEngine(market_data)


# Sample market data (for testing)
SAMPLE_MARKET_DATA = {
    "ford_focus": {
        "2015": 8000,
        "2016": 9000,
        "2017": 10500,
        "2018": 12000,
        "2019": 14000,
        "2020": 16000,
        "2021": 18000,
        "2022": 20000
    },
    "volkswagen_golf": {
        "2015": 9000,
        "2016": 10500,
        "2017": 12000,
        "2018": 14000,
        "2019": 16000,
        "2020": 18000,
        "2021": 20000,
        "2022": 22000
    },
    "bmw_3 series": {
        "2015": 12000,
        "2016": 14000,
        "2017": 16000,
        "2018": 19000,
        "2019": 22000,
        "2020": 25000,
        "2021": 29000,
        "2022": 33000
    }
}


# Test function
def test_scoring():
    """Test the scoring engine with sample data."""
    engine = get_scoring_engine(SAMPLE_MARKET_DATA)
    
    # Sample listings
    listings = [
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
            'id': '2',
            'make': 'Volkswagen',
            'model': 'Golf',
            'year': 2019,
            'price': 16500,  # Slightly above market (16000)
            'mileage': 25000,  # Below average
            'location': 'Liverpool, UK'
        },
        {
            'id': '3',
            'make': 'BMW',
            'model': '3 Series',
            'year': 2017,
            'price': 10000,  # Well below market (16000)
            'mileage': 80000,  # Above average
            'location': 'London, UK'
        },
        {
            'id': '4',
            'make': 'Mercedes',
            'model': 'S Class',  # Not in our market data
            'year': 2018,
            'price': 35000,
            'mileage': 25000,  # Below average
            'location': 'Manchester, UK'
        },
        {
            'id': '5',
            'make': 'Ford',
            'model': 'Focus',
            'year': 2016,
            'price': 4500,  # Well below market (9000)
            'mileage': 85000,  # Above average
            'location': 'Dublin, Ireland'
        },
        {
            'id': '6',
            'make': 'Ford',
            'model': 'Focus',
            'year': 2022,
            'price': 500,  # Suspiciously low
            'mileage': 5000,
            'location': 'Leeds, UK'
        }
    ]
    
    # Score the listings
    scored_listings = engine.batch_score_listings(listings)
    
    # Print results
    print("Scoring Results:")
    print("----------------")
    
    for listing in scored_listings:
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
    
    return scored_listings


if __name__ == "__main__":
    test_scoring()
