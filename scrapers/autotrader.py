import re
import logging
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any

from .base import BaseScraper

class AutoTraderScraper(BaseScraper):
    """Scraper for AutoTrader UK and Ireland."""
    
    def __init__(self):
        """Initialize the AutoTrader scraper."""
        super().__init__(
            name="AutoTrader",
            base_url="https://www.autotrader.co.uk",  # Default to UK site
        )
        self.logger = logging.getLogger("scraper.autotrader")
    
    def construct_search_url(self, preferences: Dict[str, Any]) -> str:
        """Construct a search URL based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            String URL for searching
        """
        # Determine if we're searching UK or Ireland
        location = preferences.get('location', '')
        if 'ireland' in location.lower():
            self.base_url = "https://www.autotrader.ie"
        else:
            self.base_url = "https://www.autotrader.co.uk"
        
        # Extract search parameters from preferences
        make = preferences.get('make', '')
        model = preferences.get('model', '')
        min_year = preferences.get('min_year', '')
        max_year = preferences.get('max_year', '')
        min_price = preferences.get('min_price', '')
        max_price = preferences.get('max_price', '')
        
        # Optional parameters
        fuel_type = preferences.get('fuel_type', 'Any')
        transmission = preferences.get('transmission', 'Any')
        
        # Build query parameters
        params = {}
        
        # Add make and model if provided
        if make and make.lower() != 'any':
            params['make'] = make
            
            if model and model.lower() != 'any':
                params['model'] = model
        
        # Add price range if provided
        if min_price:
            params['price-from'] = min_price
        if max_price and max_price < 9999999:  # Check if it's not the default max value
            params['price-to'] = max_price
        
        # Add year range if provided
        if min_year:
            params['year-from'] = min_year
        if max_year and max_year < 9999:  # Check if it's not the default max value
            params['year-to'] = max_year
        
        # Add fuel type if specified
        if fuel_type and fuel_type.lower() != 'any':
            params['fuel-type'] = fuel_type.lower()
        
        # Add transmission if specified
        if transmission and transmission.lower() != 'any':
            params['transmission'] = transmission.lower()
        
        # Construct the URL
        if self.base_url == "https://www.autotrader.co.uk":
            # UK AutoTrader
            search_path = "/car-search"
        else:
            # Ireland AutoTrader
            search_path = "/cars-for-sale"
        
        # Handle location for UK
        if 'uk:' in location.lower():
            # Extract the city/region
            city = location.split(':')[1].strip().lower()
            if city not in ['london', 'manchester', 'other']:
                # Add postcode/location parameter if it's a specific city
                params['postcode'] = city
                params['radius'] = 50  # 50 mile radius
        
        # Handle location for Ireland
        if 'ireland:' in location.lower():
            # Extract the city/region
            city = location.split(':')[1].strip().lower()
            if city not in ['dublin', 'cork', 'galway', 'other']:
                # Add location parameter if it's a specific city
                params['area'] = city
        
        # Add sorting by newest first
        params['sort'] = 'date-desc'
        
        # Add page size parameter (maximum results per page)
        params['page-size'] = 100
        
        # Construct the URL with parameters
        url = f"{self.base_url}{search_path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        
        return url
    
    def extract_listings(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract car listings from HTML content.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of dictionaries with car details
        """
        soup = self._parse_html(html_content)
        if not soup:
            return []
        
        listings = []
        
        # Detect UK or Ireland site based on HTML structure
        is_uk = "autotrader.co.uk" in html_content
        
        try:
            if is_uk:
                # Extract listings for UK site
                listing_elements = soup.select('.search-page__results .search-card')
                
                for element in listing_elements:
                    try:
                        # Extract listing details
                        listing = self._extract_uk_listing(element)
                        if listing:
                            listings.append(listing)
                    except Exception as e:
                        self.logger.error(f"Error extracting UK listing: {e}")
            else:
                # Extract listings for Ireland site
                listing_elements = soup.select('.car-list__result')
                
                for element in listing_elements:
                    try:
                        # Extract listing details
                        listing = self._extract_ie_listing(element)
                        if listing:
                            listings.append(listing)
                    except Exception as e:
                        self.logger.error(f"Error extracting Ireland listing: {e}")
        
        except Exception as e:
            self.logger.error(f"Error extracting listings: {e}")
        
        return listings
    
    def _extract_uk_listing(self, element: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract details from a UK AutoTrader listing.
        
        Args:
            element: BeautifulSoup element for a single listing
            
        Returns:
            Dictionary with listing details or None if extraction failed
        """
        try:
            # Check if it's a featured/promoted listing
            if element.select_one('.search-card__banner'):
                return None  # Skip featured/promoted listings
            
            # Get title containing make and model
            title_element = element.select_one('.product-card-details__title')
            if not title_element:
                return None
                
            title = title_element.text.strip()
            
            # Extract make and model from title
            make_model = title.split(' ', 1)
            make = make_model[0] if len(make_model) > 0 else ""
            model = make_model[1] if len(make_model) > 1 else ""
            
            # Get URL
            url_element = element.select_one('a.tracking-standard-link')
            url = url_element['href'] if url_element and 'href' in url_element.attrs else ""
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}"
            
            # Get price
            price_element = element.select_one('.product-card-pricing__price')
            price_text = price_element.text.strip() if price_element else ""
            price = self._extract_price(price_text)
            
            # Check if the price is suspiciously low (likely misleading)
            if price and price < 500:  # £500 or €500 threshold
                return None
            
            # Get year from title or description
            year_element = element.select_one('.product-card-details__subtitle')
            year = None
            if year_element:
                year = self._extract_year(year_element.text)
            if not year:
                # Try to find year in title
                year = self._extract_year(title)
            
            # Get mileage
            mileage = None
            key_specs = element.select('.atc-field')
            for spec in key_specs:
                text = spec.text.strip().lower()
                if 'miles' in text or 'km' in text:
                    mileage = self._extract_number(text)
                    break
            
            # Location
            location_element = element.select_one('.product-card__wrapper .product-card__distance-location')
            location = location_element.text.strip() if location_element else "Unknown"
            
            # Extract additional details if available
            fuel_type = None
            transmission = None
            for spec in key_specs:
                text = spec.text.strip().lower()
                if any(fuel in text for fuel in ['petrol', 'diesel', 'electric', 'hybrid']):
                    fuel_type = text.capitalize()
                elif any(trans in text for trans in ['manual', 'automatic']):
                    transmission = text.capitalize()
            
            # Construct the listing dictionary
            listing = {
                'make': make,
                'model': model,
                'year': year,
                'price': price,
                'mileage': mileage,
                'url': url,
                'location': location,
                'title': title,
                'fuel_type': fuel_type,
                'transmission': transmission
            }
            
            return listing
        
        except Exception as e:
            self.logger.error(f"Error in _extract_uk_listing: {e}")
            return None
    
    def _extract_ie_listing(self, element: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract details from an Ireland AutoTrader listing.
        
        Args:
            element: BeautifulSoup element for a single listing
            
        Returns:
            Dictionary with listing details or None if extraction failed
        """
        try:
            # Get title containing make and model
            title_element = element.select_one('.car-list__title')
            if not title_element:
                return None
                
            title = title_element.text.strip()
            
            # Extract make and model from title
            make_model = title.split(' ', 1)
            make = make_model[0] if len(make_model) > 0 else ""
            model = make_model[1] if len(make_model) > 1 else ""
            
            # Get URL
            url_element = title_element.parent
            url = url_element['href'] if url_element and 'href' in url_element.attrs else ""
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}"
            
            # Get price
            price_element = element.select_one('.car-list__price')
            price_text = price_element.text.strip() if price_element else ""
            price = self._extract_price(price_text)
            
            # Check if the price is suspiciously low (likely misleading)
            if price and price < 500:  # €500 threshold
                return None
            
            # Get year from title or description
            year = self._extract_year(title)
            if not year:
                # Try to find year in other elements
                subtitle_element = element.select_one('.car-list__subtitle')
                if subtitle_element:
                    year = self._extract_year(subtitle_element.text)
            
            # Get mileage and other details
            mileage = None
            fuel_type = None
            transmission = None
            
            detail_elements = element.select('.car-list__details li')
            for detail in detail_elements:
                text = detail.text.strip().lower()
                if 'km' in text or 'miles' in text:
                    mileage = self._extract_number(text)
                elif any(fuel in text for fuel in ['petrol', 'diesel', 'electric', 'hybrid']):
                    fuel_type = text.capitalize()
                elif any(trans in text for trans in ['manual', 'automatic']):
                    transmission = text.capitalize()
            
            # Location
            location_element = element.select_one('.car-list__seller-location')
            location = location_element.text.strip() if location_element else "Ireland"
            
            # Construct the listing dictionary
            listing = {
                'make': make,
                'model': model,
                'year': year,
                'price': price,
                'mileage': mileage,
                'url': url,
                'location': location,
                'title': title,
                'fuel_type': fuel_type,
                'transmission': transmission
            }
            
            return listing
        
        except Exception as e:
            self.logger.error(f"Error in _extract_ie_listing: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> Optional[int]:
        """Extract a numeric price from price text.
        
        Args:
            price_text: Text containing a price
            
        Returns:
            Integer price or None if extraction failed
        """
        try:
            # Remove currency symbols and commas
            cleaned = price_text.replace('£', '').replace('€', '').replace(',', '').strip()
            
            # Extract first number found
            match = re.search(r'\d+', cleaned)
            if match:
                return int(match.group())
            return None
        except Exception:
            return None
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract a year (4-digit number between 1990 and current year) from text.
        
        Args:
            text: Text that might contain a year
            
        Returns:
            Integer year or None if extraction failed
        """
        try:
            # Look for 4-digit numbers that could be years (between 1990 and 2030)
            matches = re.findall(r'\b(19[9][0-9]|20[0-2][0-9]|2030)\b', text)
            if matches:
                return int(matches[0])
            return None
        except Exception:
            return None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """Extract a numeric value from text.
        
        Args:
            text: Text containing a number
            
        Returns:
            Integer number or None if extraction failed
        """
        try:
            # Remove commas and extract first number found
            cleaned = text.replace(',', '').strip()
            match = re.search(r'\d+', cleaned)
            if match:
                return int(match.group())
            return None
        except Exception:
            return None
