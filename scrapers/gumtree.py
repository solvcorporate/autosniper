import re
import logging
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any

from .base import BaseScraper

class GumtreeScraper(BaseScraper):
    """Scraper for Gumtree UK and Ireland."""
    
    def __init__(self):
        """Initialize the Gumtree scraper."""
        super().__init__(
            name="Gumtree",
            base_url="https://www.gumtree.com",  # Default to UK site
        )
        self.logger = logging.getLogger("scraper.gumtree")
    
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
            self.base_url = "https://www.gumtree.ie"
        else:
            self.base_url = "https://www.gumtree.com"
        
        # Extract search parameters from preferences
        make = preferences.get('make', '')
        model = preferences.get('model', '')
        min_year = preferences.get('min_year', '')
        max_year = preferences.get('max_year', '')
        min_price = preferences.get('min_price', '')
        max_price = preferences.get('max_price', '')
        
        # Build query parameters
        params = {}
        
        # Different URL structures for UK and Ireland
        if self.base_url == "https://www.gumtree.com":
            # UK Gumtree
            search_path = "/search/cars"
            
            # Add make and model if provided
            if make and make.lower() != 'any':
                params['make'] = make.lower()
                
                if model and model.lower() != 'any':
                    params['model'] = model.lower()
            
            # Add price range if provided
            if min_price:
                params['min_price'] = min_price
            if max_price and max_price < 9999999:  # Check if it's not the default max value
                params['max_price'] = max_price
            
            # Add year range if provided
            if min_year:
                params['min_year'] = min_year
            if max_year and max_year < 9999:  # Check if it's not the default max value
                params['max_year'] = max_year
                
            # Handle location for UK
            if 'uk:' in location.lower():
                # Extract the city/region
                city = location.split(':')[1].strip().lower()
                if city not in ['london', 'manchester', 'other']:
                    # Add location parameter if it's a specific city
                    params['search_location'] = city
                    params['search_distance'] = 20  # 20 mile radius
            
            # Sort by newest first
            params['sort'] = 'date'
            
        else:
            # Ireland Gumtree
            search_path = "/cars-for-sale"
            
            # For Ireland, URLs are structured differently
            if make and make.lower() != 'any':
                search_path += f"/{make.lower()}"
                
                if model and model.lower() != 'any':
                    search_path += f"/{model.lower()}"
            
            # Handle location for Ireland
            if 'ireland:' in location.lower():
                # Extract the city/region
                city = location.split(':')[1].strip().lower()
                if city not in ['dublin', 'cork', 'galway', 'other']:
                    # Add location parameter if it's a specific city
                    params['location'] = city
            
            # Add price range if provided
            if min_price:
                params['min_price'] = min_price
            if max_price and max_price < 9999999:
                params['max_price'] = max_price
            
            # Year range is handled differently in Ireland site
            if min_year:
                params['min_car_year'] = min_year
            if max_year and max_year < 9999:
                params['max_car_year'] = max_year
            
            # Sort by newest first
            params['sort'] = 'date_desc'
        
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
        is_uk = "gumtree.com" in html_content
        
        try:
            if is_uk:
                # Extract listings for UK site
                listing_elements = soup.select('.listing-list .listing-list-item')
                
                for element in listing_elements:
                    try:
                        # Skip sponsored listings
                        if element.select_one('.listing-sponsored'):
                            continue
                            
                        # Extract listing details
                        listing = self._extract_uk_listing(element)
                        if listing:
                            listings.append(listing)
                    except Exception as e:
                        self.logger.error(f"Error extracting UK listing: {e}")
            else:
                # Extract listings for Ireland site
                listing_elements = soup.select('.result')
                
                for element in listing_elements:
                    try:
                        # Skip sponsored listings
                        if 'data-sponsored' in element.attrs and element['data-sponsored'] == 'true':
                            continue
                            
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
        """Extract details from a UK Gumtree listing.
        
        Args:
            element: BeautifulSoup element for a single listing
            
        Returns:
            Dictionary with listing details or None if extraction failed
        """
        try:
            # Get title containing make and model
            title_element = element.select_one('.listing-title')
            if not title_element:
                return None
                
            title = title_element.text.strip()
            
            # Extract make and model from title
            # This is approximate since Gumtree title format varies
            car_pattern = r'^([\w\-]+)\s+([\w\-\s]+?)(?:\s+\d|\s+for|\s+in|$)'
            car_match = re.search(car_pattern, title)
            if car_match:
                make = car_match.group(1).strip()
                model = car_match.group(2).strip()
            else:
                # Fallback if regex doesn't match
                make_model = title.split(' ', 1)
                make = make_model[0] if len(make_model) > 0 else ""
                model = make_model[1] if len(make_model) > 1 else ""
            
            # Get URL
            url_element = element.select_one('a.listing-link')
            url = url_element['href'] if url_element and 'href' in url_element.attrs else ""
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}"
            
            # Get price
            price_element = element.select_one('.listing-price')
            price_text = price_element.text.strip() if price_element else ""
            price = self._extract_price(price_text)
            
            # Check if the price is suspiciously low (likely misleading)
            if price and price < 500:  # £500 threshold
                return None
            
            # Get year from title or description
            year = self._extract_year(title)
            if not year:
                # Try to find year in other elements
                description_element = element.select_one('.listing-description')
                if description_element:
                    year = self._extract_year(description_element.text)
            
            # Get mileage from description
            mileage = None
            description_element = element.select_one('.listing-description')
            if description_element:
                description_text = description_element.text.lower()
                mileage_pattern = r'(\d[\d,]*)\s*(?:miles|mile)'
                mileage_match = re.search(mileage_pattern, description_text)
                if mileage_match:
                    mileage = self._extract_number(mileage_match.group(1))
            
            # Location
            location_element = element.select_one('.listing-location')
            location = location_element.text.strip() if location_element else "UK"
            
            # Extract additional details if available
            fuel_type = None
            transmission = None
            
            # Look for these details in the description
            if description_element:
                description_text = description_element.text.lower()
                
                # Check for fuel type
                if 'petrol' in description_text:
                    fuel_type = 'Petrol'
                elif 'diesel' in description_text:
                    fuel_type = 'Diesel'
                elif 'electric' in description_text:
                    fuel_type = 'Electric'
                elif 'hybrid' in description_text:
                    fuel_type = 'Hybrid'
                
                # Check for transmission
                if 'manual' in description_text:
                    transmission = 'Manual'
                elif 'automatic' in description_text or 'auto' in description_text:
                    transmission = 'Automatic'
            
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
        """Extract details from an Ireland Gumtree listing.
        
        Args:
            element: BeautifulSoup element for a single listing
            
        Returns:
            Dictionary with listing details or None if extraction failed
        """
        try:
            # Get title containing make and model
            title_element = element.select_one('.title')
            if not title_element:
                return None
                
            title = title_element.text.strip()
            
            # Extract make and model from title
            car_pattern = r'^([\w\-]+)\s+([\w\-\s]+?)(?:\s+\d|\s+for|\s+in|$)'
            car_match = re.search(car_pattern, title)
            if car_match:
                make = car_match.group(1).strip()
                model = car_match.group(2).strip()
            else:
                # Fallback if regex doesn't match
                make_model = title.split(' ', 1)
                make = make_model[0] if len(make_model) > 0 else ""
                model = make_model[1] if len(make_model) > 1 else ""
            
            # Get URL
            url_element = title_element.parent if title_element.parent.name == 'a' else None
            url = url_element['href'] if url_element and 'href' in url_element.attrs else ""
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}"
            
            # Get price
            price_element = element.select_one('.price')
            price_text = price_element.text.strip() if price_element else ""
            price = self._extract_price(price_text)
            
            # Check if the price is suspiciously low (likely misleading)
            if price and price < 500:  # €500 threshold
                return None
            
            # Get year from title or description
            year = self._extract_year(title)
            if not year:
                # Try to find year in other elements
                description_element = element.select_one('.description')
                if description_element:
                    year = self._extract_year(description_element.text)
            
            # Get mileage from description or additional info
            mileage = None
            description_element = element.select_one('.description')
            if description_element:
                description_text = description_element.text.lower()
                mileage_pattern = r'(\d[\d,]*)\s*(?:miles|mile|km)'
                mileage_match = re.search(mileage_pattern, description_text)
                if mileage_match:
                    mileage = self._extract_number(mileage_match.group(1))
            
            # Location
            location_element = element.select_one('.location')
            location = location_element.text.strip() if location_element else "Ireland"
            
            # Extract additional details if available
            fuel_type = None
            transmission = None
            
            # Look for these details in the description
            if description_element:
                description_text = description_element.text.lower()
                
                # Check for fuel type
                if 'petrol' in description_text:
                    fuel_type = 'Petrol'
                elif 'diesel' in description_text:
                    fuel_type = 'Diesel'
                elif 'electric' in description_text:
                    fuel_type = 'Electric'
                elif 'hybrid' in description_text:
                    fuel_type = 'Hybrid'
                
                # Check for transmission
                if 'manual' in description_text:
                    transmission = 'Manual'
                elif 'automatic' in description_text or 'auto' in description_text:
                    transmission = 'Automatic'
            
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
