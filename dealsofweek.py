"""
Deals of the Week feature for AutoSniper.
This module handles finding and formatting the best deals across all categories.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dealsofweek")

# Import modules needed for finding deals
from scrapers import run_all_scrapers
from matching import get_matching_engine
from scoring import get_scoring_engine, SAMPLE_MARKET_DATA

class DealsOfWeekManager:
    """Manager for finding and displaying the Deals of the Week."""
    
    def __init__(self, sheets_manager=None, market_data=None):
        """Initialize the Deals of the Week manager.
        
        Args:
            sheets_manager: SheetsManager instance (optional)
            market_data: Market data for pricing comparisons (optional)
        """
        self.sheets_manager = sheets_manager
        self.logger = logging.getLogger("dealsofweek.manager")
        
        # Initialize the scoring engine with market data
        self.scoring_engine = get_scoring_engine(market_data or SAMPLE_MARKET_DATA)
        
        # Initialize the matching engine (used for scoring)
        self.matching_engine = get_matching_engine(market_data or SAMPLE_MARKET_DATA)
        
        # Cache for deals of the week (refreshed weekly)
        self.cached_deals = []
        self.cache_timestamp = None
        
        self.logger.info("DealsOfWeekManager initialized")
    
    def get_deals_of_week(self, max_deals: int = 10, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get the Deals of the Week.
        
        Args:
            max_deals: Maximum number of deals to return
            force_refresh: Whether to force a refresh of the deals
            
        Returns:
            List of top deals with scores and details
        """
        # Check if we have cached deals and they're not too old
        if not force_refresh and self.cached_deals and self.cache_timestamp:
            cache_age = datetime.now() - self.cache_timestamp
            if cache_age < timedelta(days=1):  # Cache for 1 day
                self.logger.info(f"Using cached deals ({len(self.cached_deals)} deals, {cache_age.total_seconds()/3600:.1f} hours old)")
                return self.cached_deals[:max_deals]
        
        # Get deals from sheets if available
        if self.sheets_manager:
            deals = self._get_deals_from_sheets()
            if deals:
                self.logger.info(f"Found {len(deals)} deals in sheets")
                return self._process_deals(deals, max_deals)
        
        # If no deals in sheets or couldn't access sheets, generate placeholder deals
        self.logger.info("Generating placeholder deals")
        return self._generate_placeholder_deals(max_deals)
    
    def _get_deals_from_sheets(self) -> List[Dict[str, Any]]:
        """Get recent car listings from the Google Sheets.
        
        Returns:
            List of car listings
        """
        try:
            # This method would normally fetch all recent listings from Google Sheets
            # Implement the actual method based on your sheets structure
            # For now, we'll return an empty list
            return []
        except Exception as e:
            self.logger.error(f"Error getting deals from sheets: {e}")
            return []
    
    def _process_deals(self, listings: List[Dict[str, Any]], max_deals: int) -> List[Dict[str, Any]]:
        """Process listings to find the best deals.
        
        Args:
            listings: List of car listings
            max_deals: Maximum number of deals to return
            
        Returns:
            List of top deals with scores and details
        """
        # Score all listings if not already scored
        scored_listings = []
        for listing in listings:
            if 'score' not in listing:
                try:
                    scored_listing = self.scoring_engine.score_listing(listing)
                    scored_listings.append(scored_listing)
                except Exception as e:
                    self.logger.error(f"Error scoring listing: {e}")
            else:
                scored_listings.append(listing)
        
        # Filter out suspiciously low-priced listings
        filtered_listings = [
            listing for listing in scored_listings
            if not listing.get('score_details', {}).get('suspicious', False)
        ]
        
        # Find the top deals by score
        top_deals = sorted(
            filtered_listings,
            key=lambda x: x.get('score', 0),
            reverse=True
        )[:max_deals]
        
        # Add additional details for display
        for deal in top_deals:
            self._enhance_deal_for_display(deal)
        
        # Update cache
        self.cached_deals = top_deals
        self.cache_timestamp = datetime.now()
        
        return top_deals
    
    def _enhance_deal_for_display(self, deal: Dict[str, Any]) -> None:
        """Add additional details to a deal for display.
        
        Args:
            deal: Deal dictionary to enhance
        """
        # Add market comparison if available
        if 'score_details' in deal and 'market_average' in deal.get('score_details', {}):
            market_avg = deal['score_details']['market_average']
            price = deal.get('price', 0)
            if market_avg and price:
                discount_pct = ((market_avg - price) / market_avg) * 100
                deal['discount_percent'] = discount_pct
                deal['market_avg'] = market_avg
        
        # Add formatted price
        price = deal.get('price', 0)
        if price:
            deal['price_formatted'] = f"€{price:,}"
        
        # Add formatted mileage
        mileage = deal.get('mileage', 0)
        if mileage:
            deal['mileage_formatted'] = f"{mileage:,} miles"
    
    def _generate_placeholder_deals(self, max_deals: int) -> List[Dict[str, Any]]:
        """Generate placeholder deals for demonstration.
        
        Args:
            max_deals: Maximum number of deals to generate
            
        Returns:
            List of placeholder deals
        """
        placeholder_deals = [
            {
                'make': 'BMW',
                'model': '3 Series',
                'year': 2019,
                'price': 21500,
                'mileage': 35000,
                'location': 'Dublin, Ireland',
                'fuel_type': 'Diesel',
                'transmission': 'Automatic',
                'url': 'https://example.com/bmw-3-series',
                'score': 93.5,
                'grade': 'A+',
                'discount_percent': 15.0,
                'market_avg': 25300,
                'price_formatted': '€21,500',
                'mileage_formatted': '35,000 miles',
                'source': 'AutoTrader',
                'description': 'BMW 3 Series 320d M Sport, Full service history, 1 owner'
            },
            {
                'make': 'Audi',
                'model': 'A4',
                'year': 2020,
                'price': 24750,
                'mileage': 28000,
                'location': 'London, UK',
                'fuel_type': 'Petrol',
                'transmission': 'Automatic',
                'url': 'https://example.com/audi-a4',
                'score': 89.2,
                'grade': 'A',
                'discount_percent': 12.0,
                'market_avg': 28125,
                'price_formatted': '€24,750',
                'mileage_formatted': '28,000 miles',
                'source': 'Gumtree',
                'description': 'Audi A4 2.0 TFSI S Line, Immaculate condition, Full Audi service history'
            },
            {
                'make': 'Mercedes',
                'model': 'C-Class',
                'year': 2018,
                'price': 19900,
                'mileage': 42000,
                'location': 'Manchester, UK',
                'fuel_type': 'Diesel',
                'transmission': 'Automatic',
                'url': 'https://example.com/mercedes-c-class',
                'score': 87.5,
                'grade': 'B+',
                'discount_percent': 10.0,
                'market_avg': 22110,
                'price_formatted': '€19,900',
                'mileage_formatted': '42,000 miles',
                'source': 'AutoTrader',
                'description': 'Mercedes C Class C220d AMG Line, Premium Plus package, Panoramic roof'
            },
            {
                'make': 'Volkswagen',
                'model': 'Golf',
                'year': 2020,
                'price': 18500,
                'mileage': 22000,
                'location': 'Glasgow, UK',
                'fuel_type': 'Petrol',
                'transmission': 'Manual',
                'url': 'https://example.com/vw-golf',
                'score': 86.8,
                'grade': 'B+',
                'discount_percent': 9.5,
                'market_avg': 20440,
                'price_formatted': '€18,500',
                'mileage_formatted': '22,000 miles',
                'source': 'Gumtree',
                'description': 'VW Golf 1.5 TSI EVO Match, Adaptive cruise, Winter pack'
            },
            {
                'make': 'Toyota',
                'model': 'Corolla',
                'year': 2021,
                'price': 17900,
                'mileage': 15000,
                'location': 'Cork, Ireland',
                'fuel_type': 'Hybrid',
                'transmission': 'Automatic',
                'url': 'https://example.com/toyota-corolla',
                'score': 85.5,
                'grade': 'B+',
                'discount_percent': 8.5,
                'market_avg': 19562,
                'price_formatted': '€17,900',
                'mileage_formatted': '15,000 miles',
                'source': 'DoneDeal',
                'description': 'Toyota Corolla 1.8 Hybrid Design, Toyota warranty until 2026'
            },
            {
                'make': 'Ford',
                'model': 'Focus',
                'year': 2019,
                'price': 14750,
                'mileage': 31000,
                'location': 'Leeds, UK',
                'fuel_type': 'Petrol',
                'transmission': 'Manual',
                'url': 'https://example.com/ford-focus',
                'score': 84.2,
                'grade': 'B',
                'discount_percent': 7.8,
                'market_avg': 16000,
                'price_formatted': '€14,750',
                'mileage_formatted': '31,000 miles',
                'source': 'AutoTrader',
                'description': 'Ford Focus 1.0 EcoBoost ST-Line, Technology Pack, Winter Pack'
            },
            {
                'make': 'Honda',
                'model': 'Civic',
                'year': 2020,
                'price': 16500,
                'mileage': 25000,
                'location': 'Birmingham, UK',
                'fuel_type': 'Petrol',
                'transmission': 'Manual',
                'url': 'https://example.com/honda-civic',
                'score': 83.7,
                'grade': 'B',
                'discount_percent': 7.2,
                'market_avg': 17780,
                'price_formatted': '€16,500',
                'mileage_formatted': '25,000 miles',
                'source': 'Gumtree',
                'description': 'Honda Civic 1.5 VTEC Turbo Sport, Honda Sensing, Single owner'
            },
            {
                'make': 'Nissan',
                'model': 'Qashqai',
                'year': 2019,
                'price': 15900,
                'mileage': 38000,
                'location': 'Edinburgh, UK',
                'fuel_type': 'Diesel',
                'transmission': 'Manual',
                'url': 'https://example.com/nissan-qashqai',
                'score': 82.5,
                'grade': 'B',
                'discount_percent': 6.8,
                'market_avg': 17060,
                'price_formatted': '€15,900',
                'mileage_formatted': '38,000 miles',
                'source': 'AutoTrader',
                'description': 'Nissan Qashqai 1.5 dCi N-Connecta, Glass roof pack, Around view monitor'
            },
            {
                'make': 'Hyundai',
                'model': 'Tucson',
                'year': 2020,
                'price': 19250,
                'mileage': 32000,
                'location': 'Belfast, UK',
                'fuel_type': 'Diesel',
                'transmission': 'Automatic',
                'url': 'https://example.com/hyundai-tucson',
                'score': 81.8,
                'grade': 'B',
                'discount_percent': 6.5,
                'market_avg': 20590,
                'price_formatted': '€19,250',
                'mileage_formatted': '32,000 miles',
                'source': 'Gumtree',
                'description': 'Hyundai Tucson 1.6 CRDi Premium SE, Panoramic roof, Manufacturer warranty'
            },
            {
                'make': 'Kia',
                'model': 'Sportage',
                'year': 2019,
                'price': 16750,
                'mileage': 35000,
                'location': 'Liverpool, UK',
                'fuel_type': 'Diesel',
                'transmission': 'Manual',
                'url': 'https://example.com/kia-sportage',
                'score': 81.2,
                'grade': 'B',
                'discount_percent': 6.2,
                'market_avg': 17860,
                'price_formatted': '€16,750',
                'mileage_formatted': '35,000 miles',
                'source': 'AutoTrader',
                'description': 'Kia Sportage 1.6 CRDi GT-Line, Remaining 7-year warranty, Full service history'
            }
        ]
        
        # Only return requested number of deals
        return placeholder_deals[:max_deals]
    
    def format_deals_of_week_message(self, deals: List[Dict[str, Any]]) -> str:
        """Format the Deals of the Week as a Telegram message.
        
        Args:
            deals: List of top deals
            
        Returns:
            Formatted message text
        """
        if not deals:
            return "No exceptional deals found this week. Check back soon!"
        
        # Create the header
        message_parts = [
            "*🌟 AutoSniper Deals of the Week 🌟*\n",
            "_Exclusive content for Premium subscribers_\n",
            "Our algorithm has identified these exceptional deals across multiple platforms:\n\n"
        ]
        
        # Add each deal
        for i, deal in enumerate(deals, 1):
            make = deal.get('make', 'Unknown')
            model = deal.get('model', 'Unknown')
            year = deal.get('year', 'Unknown')
            price_formatted = deal.get('price_formatted', f"€{deal.get('price', 0):,}")
            grade = deal.get('grade', '')
            discount = deal.get('discount_percent', 0)
            source = deal.get('source', 'Unknown')
            
            deal_text = f"*{i}. {year} {make} {model}* - {price_formatted}"
            
            if discount > 0:
                deal_text += f" ({discount:.0f}% below market)"
            
            if grade:
                deal_text += f" - {grade} Deal"
            
            deal_text += f"\n_Source: {source}_\n\n"
            message_parts.append(deal_text)
        
        # Add footer
        message_parts.append(
            "_Use /car_details followed by the number to see full details of any listing_\n"
            "_Example: /car_details 1 for the first car_\n\n"
            "Deals are updated weekly. Next update: Monday 00:00 UTC"
        )
        
        return "".join(message_parts)
    
    def format_deal_details(self, deal: Dict[str, Any]) -> str:
        """Format detailed information about a specific deal.
        
        Args:
            deal: Deal dictionary
            
        Returns:
            Formatted message text with detailed information
        """
        make = deal.get('make', 'Unknown')
        model = deal.get('model', 'Unknown')
        year = deal.get('year', 'Unknown')
        price_formatted = deal.get('price_formatted', f"€{deal.get('price', 0):,}")
        mileage_formatted = deal.get('mileage_formatted', 'Unknown mileage')
        location = deal.get('location', 'Unknown location')
        fuel_type = deal.get('fuel_type', 'Not specified')
        transmission = deal.get('transmission', 'Not specified')
        grade = deal.get('grade', '')
        score = deal.get('score', 0)
        discount = deal.get('discount_percent', 0)
        market_avg = deal.get('market_avg', 0)
        source = deal.get('source', 'Unknown')
        description = deal.get('description', '')
        url = deal.get('url', '')
        
        # Build the detail message
        message_parts = [
            f"*🚗 {year} {make} {model}*\n\n",
            f"💰 *Price:* {price_formatted}\n"
        ]
        
        if market_avg > 0:
            message_parts.append(f"📊 *Market Average:* €{market_avg:,}\n")
            
        if discount > 0:
            message_parts.append(f"🔻 *Discount:* {discount:.1f}% below market\n")
            
        message_parts.extend([
            f"🔄 *Mileage:* {mileage_formatted}\n",
            f"📍 *Location:* {location}\n",
            f"⛽ *Fuel Type:* {fuel_type}\n",
            f"🎮 *Transmission:* {transmission}\n"
        ])
        
        if grade and score > 0:
            message_parts.append(f"📋 *AutoSniper Score:* {score:.1f}/100 ({grade} Grade)\n")
            
        message_parts.append(f"🔍 *Source:* {source}\n")
        
        if description:
            message_parts.append(f"\n📝 *Description:*\n{description}\n")
            
        # Add suggested message to seller
        message_parts.append(
            f"\n💬 *Suggested Message to Seller:*\n"
            f"\"Hi, I'm interested in your {year} {make} {model} "
            f"priced at {price_formatted}. Is it still available?\"\n"
        )
        
        # Add link to the listing
        if url:
            message_parts.append(f"\n➡️ [View Original Listing]({url})")
            
        return "".join(message_parts)


# Helper function to get a deals of week manager instance
def get_deals_of_week_manager(sheets_manager=None, market_data=None):
    """Get a DealsOfWeekManager instance.
    
    Args:
        sheets_manager: SheetsManager instance (optional)
        market_data: Market data for pricing comparisons (optional)
        
    Returns:
        DealsOfWeekManager instance
    """
    return DealsOfWeekManager(sheets_manager, market_data)
