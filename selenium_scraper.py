"""
Advanced scraper using Selenium for browser emulation.
This scraper mimics real browser behavior to bypass bot detection systems.
"""

import os
import logging
import time
import random
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("selenium_scraper")

class SeleniumScraper:
    """Base class for Selenium-based scrapers."""
    
    def __init__(self, headless=True):
        """Initialize the Selenium scraper.
        
        Args:
            headless: Whether to run in headless mode (no visible browser)
        """
        self.logger = logging.getLogger("selenium_scraper.base")
        self.headless = headless
        self.driver = None
        
        # User agents for rotation
        self.user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            # Safari on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            # Chrome on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]
    
    def initialize_driver(self):
        """Initialize the Chrome WebDriver."""
        try:
            # Set up Chrome options
            chrome_options = Options()
            
            # Choose a random user agent
            user_agent = random.choice(self.user_agents)
            
            # Set up various options to make the browser more realistic
            chrome_options.add_argument(f"user-agent={user_agent}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Initialize the Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Additional CDP commands to evade detection
            # This is a more modern approach for evading bot detection
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Overwrite the 'plugins' property to use a custom getter
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Overwrite the 'languages' property to use a custom getter
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                """
            })
            
            self.logger.info(f"Initialized Chrome WebDriver with user agent: {user_agent}")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing Chrome WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver when done."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("WebDriver closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")
    
    def navigate_with_realistic_behavior(self, url):
        """Navigate to a URL with realistic human-like behavior."""
        if not self.driver:
            if not self.initialize_driver():
                return False
        
        try:
            self.logger.info(f"Navigating to: {url}")
            
            # Navigate to the URL
            self.driver.get(url)
            
            # Add a random delay to simulate human reading
            read_delay = 2 + random.random() * 3  # 2-5 seconds
            self.logger.info(f"Waiting {read_delay:.2f} seconds to simulate reading")
            time.sleep(read_delay)
            
            # Scroll down a bit to simulate human behavior
            scroll_script = "window.scrollTo(0, document.body.scrollHeight / {})"
            scroll_points = [4, 3, 2, 1.5]  # Scroll to 25%, 33%, 50%, 66% of the page
            
            for point in scroll_points:
                self.driver.execute_script(scroll_script.format(point))
                scroll_delay = 1 + random.random() * 2  # 1-3 seconds
                self.logger.info(f"Scrolling and waiting {scroll_delay:.2f} seconds")
                time.sleep(scroll_delay)
            
            # Scroll back up a bit
            self.driver.execute_script(scroll_script.format(3))
            time.sleep(1 + random.random())
            
            return True
        except Exception as e:
            self.logger.error(f"Error during navigation with realistic behavior: {e}")
            return False
    
    def get_page_source(self):
        """Get the current page source."""
        if not self.driver:
            self.logger.error("WebDriver not initialized")
            return None
        
        try:
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"Error getting page source: {e}")
            return None
    
    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be present on the page.
        
        Args:
            by: Selenium By strategy (e.g., By.ID, By.CSS_SELECTOR)
            value: Element identifier
            timeout: Maximum time to wait in seconds
            
        Returns:
            The WebElement if found, None otherwise
        """
        if not self.driver:
            self.logger.error("WebDriver not initialized")
            return None
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for element: {by}={value}")
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for element: {e}")
            return None
    
    def take_screenshot(self, filename):
        """Take a screenshot for debugging purposes."""
        if not self.driver:
            self.logger.error("WebDriver not initialized")
            return False
        
        try:
            self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot saved to: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return False


class AutoTraderSeleniumScraper(SeleniumScraper):
    """Selenium-based scraper for AutoTrader."""
    
    def __init__(self, headless=True):
        """Initialize the AutoTrader Selenium scraper."""
        super().__init__(headless)
        self.logger = logging.getLogger("selenium_scraper.autotrader")
        self.base_url = "https://www.autotrader.co.uk"
    
    def search_cars(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for cars on AutoTrader based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            List of car listing dictionaries
        """
        self.logger.info(f"Searching AutoTrader with preferences: {preferences}")
        
        # Initialize the driver if needed
        if not self.driver:
            if not self.initialize_driver():
                return []
        
        try:
            # First visit the homepage with realistic behavior
            self.navigate_with_realistic_behavior(self.base_url)
            
            # Then navigate to the car search page
            search_url = self._construct_search_url(preferences)
            self.navigate_with_realistic_behavior(search_url)
            
            # Check if we're facing a CAPTCHA or security check
            if self._is_security_page():
                self.logger.warning("Security check or CAPTCHA detected")
                self.take_screenshot("autotrader_security_check.png")
                return []
            
            # Wait for the search results to load
            results_element = self.wait_for_element(By.CSS_SELECTOR, ".search-page__results")
            if not results_element:
                self.logger.warning("Search results not found")
                self.take_screenshot("autotrader_no_results.png")
                return []
            
            # Extract car listings
            return self._extract_listings()
            
        except Exception as e:
            self.logger.error(f"Error during AutoTrader search: {e}")
            return []
        finally:
            # Close the driver to free resources
            self.close_driver()
    
    def _construct_search_url(self, preferences: Dict[str, Any]) -> str:
        """Construct a search URL based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            String URL for searching
        """
        # Extract search parameters from preferences
        make = preferences.get('make', '')
        model = preferences.get('model', '')
        min_year = preferences.get('min_year', '')
        max_year = preferences.get('max_year', '')
        min_price = preferences.get('min_price', '')
        max_price = preferences.get('max_price', '')
        location = preferences.get('location', '')
        
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
        
        # Handle location
        if location:
            # Extract city/region from format like "UK: London"
            if ':' in location:
                parts = location.split(':')
                if len(parts) > 1:
                    city = parts[1].strip()
                    if city.lower() not in ['any', 'other']:
                        params['postcode'] = city
                        params['radius'] = 50  # 50 mile radius
        
        # Sorting by newest first is better for finding fresh deals
        params['sort'] = 'date-desc'
        
        # Add page size parameter
        params['page-size'] = 100
        
        # Construct the URL with parameters
        url_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/car-search?{url_params}"
    
    def _is_security_page(self) -> bool:
        """Check if the current page is a security check or CAPTCHA page."""
        # Look for common indicators of security challenges
        security_indicators = [
            "captcha",
            "security check",
            "verification",
            "please verify",
            "unusual traffic",
            "automated access"
        ]
        
        # Check page source for these indicators
        page_source = self.get_page_source().lower()
        if any(indicator in page_source for indicator in security_indicators):
            return True
        
        # Check for specific elements
        try:
            captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                                                       "iframe[src*='captcha'], iframe[src*='recaptcha']")
            if captcha_elements:
                return True
        except:
            pass
        
        return False
    
    def _extract_listings(self) -> List[Dict[str, Any]]:
        """Extract car listings from the search results page.
        
        Returns:
            List of dictionaries with car details
        """
        listings = []
        
        try:
            # Find all listing cards
            listing_elements = self.driver.find_elements(By.CSS_SELECTOR, ".search-page__results .search-card")
            self.logger.info(f"Found {len(listing_elements)} listing elements")
            
            # Process each listing
            for element in listing_elements:
                try:
                    # Skip sponsored/featured listings
                    if element.find_elements(By.CSS_SELECTOR, ".search-card__banner"):
                        continue
                    
                    # Extract listing details
                    listing = self._extract_listing_details(element)
                    if listing:
                        listings.append(listing)
                    
                except Exception as e:
                    self.logger.error(f"Error extracting listing details: {e}")
                    continue
            
            return listings
        except Exception as e:
            self.logger.error(f"Error finding listing elements: {e}")
            return []
    
    def _extract_listing_details(self, element) -> Optional[Dict[str, Any]]:
        """Extract details from a single listing element.
        
        Args:
            element: Selenium WebElement for a single listing
            
        Returns:
            Dictionary with listing details or None if extraction failed
        """
        try:
            # Title (make and model)
            title_element = element.find_element(By.CSS_SELECTOR, ".product-card-details__title")
            title = title_element.text.strip()
            
            # Extract make and model from title
            make_model = title.split(' ', 1)
            make = make_model[0] if len(make_model) > 0 else ""
            model = make_model[1] if len(make_model) > 1 else ""
            
            # URL
            url_element = element.find_element(By.CSS_SELECTOR, "a.tracking-standard-link")
            url = url_element.get_attribute("href")
            
            # Price
            price_element = element.find_element(By.CSS_SELECTOR, ".product-card-pricing__price")
            price_text = price_element.text.strip()
            price = self._extract_price(price_text)
            
            # Skip suspicious listings with very low prices
            if price and price < 500:  # £500 threshold
                return None
            
            # Year
            year = None
            subtitle = element.find_element(By.CSS_SELECTOR, ".product-card-details__subtitle").text
            year_match = re.search(r'\b(19[9][0-9]|20[0-2][0-9])\b', subtitle)
            if year_match:
                year = int(year_match.group(1))
            
            # Mileage
            mileage = None
            specs = element.find_elements(By.CSS_SELECTOR, ".atc-field")
            for spec in specs:
                text = spec.text.strip().lower()
                if 'miles' in text:
                    mileage_match = re.search(r'(\d[\d,]*)', text)
                    if mileage_match:
                        mileage = int(mileage_match.group(1).replace(',', ''))
            
            # Location
            location_element = element.find_element(By.CSS_SELECTOR, ".product-card__distance-location")
            location = location_element.text.strip()
            
            # Fuel type and transmission
            fuel_type = None
            transmission = None
            for spec in specs:
                text = spec.text.strip().lower()
                if any(fuel in text for fuel in ['petrol', 'diesel', 'electric', 'hybrid']):
                    fuel_type = text.capitalize()
                elif any(trans in text for trans in ['manual', 'automatic']):
                    transmission = text.capitalize()
            
            # Construct the listing dictionary
            return {
                'source': 'AutoTrader',
                'make': make,
                'model': model,
                'year': year,
                'price': price,
                'mileage': mileage,
                'location': location,
                'fuel_type': fuel_type,
                'transmission': transmission,
                'url': url,
                'title': title,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            self.logger.error(f"Error extracting details from listing element: {e}")
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


class GumtreeSeleniumScraper(SeleniumScraper):
    """Selenium-based scraper for Gumtree."""
    
    def __init__(self, headless=True):
        """Initialize the Gumtree Selenium scraper."""
        super().__init__(headless)
        self.logger = logging.getLogger("selenium_scraper.gumtree")
        self.base_url = "https://www.gumtree.com"
    
    def search_cars(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for cars on Gumtree based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            List of car listing dictionaries
        """
        self.logger.info(f"Searching Gumtree with preferences: {preferences}")
        
        # Initialize the driver if needed
        if not self.driver:
            if not self.initialize_driver():
                return []
        
        try:
            # First visit the homepage with realistic behavior
            self.navigate_with_realistic_behavior(self.base_url)
            
            # Then navigate to the car section
            cars_url = f"{self.base_url}/cars-vans-motorbikes"
            self.navigate_with_realistic_behavior(cars_url)
            
            # Finally make the search
            search_url = self._construct_search_url(preferences)
            self.navigate_with_realistic_behavior(search_url)
            
            # Check if we're facing a CAPTCHA or security check
            if self._is_security_page():
                self.logger.warning("Security check or CAPTCHA detected")
                self.take_screenshot("gumtree_security_check.png")
                return []
            
            # Wait for the search results to load
            results_element = self.wait_for_element(By.CSS_SELECTOR, "article.listing-maxi")
            if not results_element:
                self.logger.warning("Search results not found")
                self.take_screenshot("gumtree_no_results.png")
                return []
            
            # Extract car listings
            return self._extract_listings()
            
        except Exception as e:
            self.logger.error(f"Error during Gumtree search: {e}")
            return []
        finally:
            # Close the driver to free resources
            self.close_driver()
    
    def _construct_search_url(self, preferences: Dict[str, Any]) -> str:
        """Construct a search URL based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            String URL for searching
        """
        # Extract search parameters from preferences
        make = preferences.get('make', '').lower()
        model = preferences.get('model', '').lower() if preferences.get('model') else ''
        min_year = preferences.get('min_year', '')
        max_year = preferences.get('max_year', '')
        min_price = preferences.get('min_price', '')
        max_price = preferences.get('max_price', '')
        location = preferences.get('location', '')
        
        # The URL structure is: /cars-vans-motorbikes/cars/{make}?q={model}&other_params
        search_path = "/cars-vans-motorbikes/cars"
        
        # Add make to path if provided
        if make and make.lower() != 'any':
            search_path += f"/{make}"
        
        # Build query parameters
        params = {}
        
        # Add model as search query if provided
        if model and model.lower() != 'any':
            params['q'] = model
        
        # Add price range if provided
        if min_price:
            params['min_price'] = min_price
        if max_price and max_price < 9999999:
            params['max_price'] = max_price
        
        # Add year range if provided
        if min_year:
            params['min_vehicle_year'] = min_year
        if max_year and max_year < 9999:
            params['max_vehicle_year'] = max_year
            
        # Handle location
        if location:
            # Extract city/region from format like "UK: London"
            if ':' in location:
                parts = location.split(':')
                if len(parts) > 1:
                    city = parts[1].strip()
                    if city.lower() not in ['any', 'other']:
                        params['search_location'] = city
                        params['distance'] = 20  # 20 mile radius
        
        # Sort by newest first
        params['sort'] = 'date'
        
        # Construct the URL with parameters
        url_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}{search_path}?{url_params}"
    
    def _is_security_page(self) -> bool:
        """Check if the current page is a security check or CAPTCHA page."""
        # Look for common indicators of security challenges
        security_indicators = [
            "captcha",
            "security check",
            "verification",
            "please verify",
            "unusual traffic",
            "automated access"
        ]
        
        # Check page source for these indicators
        page_source = self.get_page_source().lower()
        if any(indicator in page_source for indicator in security_indicators):
            return True
        
        # Check for specific elements
        try:
            captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                                                      "iframe[src*='captcha'], iframe[src*='recaptcha']")
            if captcha_elements:
                return True
        except:
            pass
        
        return False
    
    def _extract_listings(self) -> List[Dict[str, Any]]:
        """Extract car listings from the search results page.
        
        Returns:
            List of dictionaries with car details
        """
        listings = []
        
        try:
            # Find all listing cards
            listing_elements = self.driver.find_elements(By.CSS_SELECTOR, "article.listing-maxi")
            self.logger.info(f"Found {len(listing_elements)} listing elements")
            
            # Process each listing
            for element in listing_elements:
                try:
                    # Skip promoted listings
                    if element.find_elements(By.CSS_SELECTOR, ".listing-promoted-label"):
                        continue
                    
                    # Extract listing details
                    listing = self._extract_listing_details(element)
                    if listing:
                        listings.append(listing)
                    
                except Exception as e:
                    self.logger.error(f"Error extracting listing details: {e}")
                    continue
            
            return listings
        except Exception as e:
            self.logger.error(f"Error finding listing elements: {e}")
            return []
    
    def _extract_listing_details(self, element) -> Optional[Dict[str, Any]]:
        """Extract details from a single listing element.
        
        Args:
            element: Selenium WebElement for a single listing
            
        Returns:
            Dictionary with listing details or None if extraction failed
        """
        try:
            # Title (make and model)
            title_element = element.find_element(By.CSS_SELECTOR, "h2.listing-title")
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
            
            # URL
            url_element = element.find_element(By.CSS_SELECTOR, "a.listing-link")
            url = url_element.get_attribute("href")
            
            # Price
            price_element = element.find_element(By.CSS_SELECTOR, ".listing-price")
            price_text = price_element.text.strip()
            price = self._extract_price(price_text)
            
            # Skip suspicious listings with very low prices
            if price and price < 500:  # £500 threshold
                return None
            
            # Year from title or description
            year = None
            year_match = re.search(r'\b(19[9][0-9]|20[0-2][0-9])\b', title)
            if year_match:
                year = int(year_match.group(1))
            
            # Description for more details
            description_element = element.find_element(By.CSS_SELECTOR, ".listing-description")
            description = description_element.text.lower()
            
            # If year not found in title, look in description
            if not year:
                year_match = re.search(r'\b(19[9][0-9]|20[0-2][0-9])\b', description)
                if year_match:
                    year = int(year_match.group(1))
            
            # Mileage from description
            mileage = None
            mileage_pattern = r'(\d[\d,]*)\s*(?:miles|mile)'
            mileage_match = re.search(mileage_pattern, description)
            if mileage_match:
                mileage = int(mileage_match.group(1).replace(',', ''))
            
            # Location
            location_element = element.find_element(By.CSS_SELECTOR, ".listing-location")
            location = location_element.text.strip()
            
            # Fuel type and transmission from description
            fuel_type = None
            transmission = None
            
            if 'petrol' in description:
                fuel_type = 'Petrol'
            elif 'diesel' in description:
                fuel_type = 'Diesel'
            elif 'electric' in description:
                fuel_type = 'Electric'
            elif 'hybrid' in description:
                fuel_type = 'Hybrid'
            
            if 'manual' in description:
                transmission = 'Manual'
            elif 'automatic' in description or 'auto' in description:
                transmission = 'Automatic'
            
            # Construct the listing dictionary
            return {
                'source': 'Gumtree',
                'make': make,
                'model': model,
                'year': year,
                'price': price,
                'mileage': mileage,
                'location': location,
                'fuel_type': fuel_type,
                'transmission': transmission,
                'url': url,
                'title': title,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            self.logger.error(f"Error extracting details from listing element: {e}")
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


# Example usage
def test_selenium_scrapers():
    """Test the Selenium-based scrapers with sample preferences."""
    # Sample preferences
    preferences = {
        'make': 'Ford',
        'model': 'Focus',
        'min_year': 2015,
        'max_year': 2021,
        'min_price': 5000,
        'max_price': 15000,
        'location': 'UK: Manchester'
    }
    
    # Test AutoTrader scraper
    logger.info("Testing AutoTrader scraper...")
    autotrader_scraper = AutoTraderSeleniumScraper(headless=True)
    autotrader_listings = autotrader_scraper.search_cars(preferences)
    logger.info(f"Found {len(autotrader_listings)} listings on AutoTrader")
    
    # Test Gumtree scraper
    logger.info("Testing Gumtree scraper...")
    gumtree_scraper = GumtreeSeleniumScraper(headless=True)
    gumtree_listings = gumtree_scraper.search_cars(preferences)
    logger.info(f"Found {len(gumtree_listings)} listings on Gumtree")
    
    # Combine results
    all_listings = autotrader_listings + gumtree_listings
    logger.info(f"Found {len(all_listings)} listings in total")
    
    # Save results to a JSON file for review
    try:
        with open('selenium_scraper_results.json', 'w') as f:
            json.dump(all_listings, f, indent=2)
        logger.info("Saved results to selenium_scraper_results.json")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
    
    return all_listings


if __name__ == "__main__":
    test_selenium_scrapers()
"""
Advanced scraper using Selenium for browser emulation.
This scraper mimics real browser behavior to bypass bot detection systems.
"""

import os
import logging
import time
import random
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("selenium_scraper")

class SeleniumScraper:
    """Base class for Selenium-based scrapers."""
    
    def __init__(self, headless=True):
        """Initialize the Selenium scraper.
        
        Args:
            headless: Whether to run in headless mode (no visible browser)
        """
        self.logger = logging.getLogger("selenium_scraper.base")
        self.headless = headless
        self.driver = None
        
        # User agents for rotation
        self.user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            # Safari on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            # Chrome on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]
    
    def initialize_driver(self):
        """Initialize the Chrome WebDriver."""
        try:
            # Set up Chrome options
            chrome_options = Options()
            
            # Choose a random user agent
            user_agent = random.choice(self.user_agents)
            
            # Set up various options to make the browser more realistic
            chrome_options.add_argument(f"user-agent={user_agent}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Initialize the Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Additional CDP commands to evade detection
            # This is a more modern approach for evading bot detection
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Overwrite the 'plugins' property to use a custom getter
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Overwrite the 'languages' property to use a custom getter
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                """
            })
            
            self.logger.info(f"Initialized Chrome WebDriver with user agent: {user_agent}")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing Chrome WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver when done."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("WebDriver closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")
    
    def navigate_with_realistic_behavior(self, url):
        """Navigate to a URL with realistic human-like behavior."""
        if not self.driver:
            if not self.initialize_driver():
                return False
        
        try:
            self.logger.info(f"Navigating to: {url}")
            
            # Navigate to the URL
            self.driver.get(url)
            
            # Add a random delay to simulate human reading
            read_delay = 2 + random.random() * 3  # 2-5 seconds
            self.logger.info(f"Waiting {read_delay:.2f} seconds to simulate reading")
            time.sleep(read_delay)
            
            # Scroll down a bit to simulate human behavior
            scroll_script = "window.scrollTo(0, document.body.scrollHeight / {})"
            scroll_points = [4, 3, 2, 1.5]  # Scroll to 25%, 33%, 50%, 66% of the page
            
            for point in scroll_points:
                self.driver.execute_script(scroll_script.format(point))
                scroll_delay = 1 + random.random() * 2  # 1-3 seconds
                self.logger.info(f"Scrolling and waiting {scroll_delay:.2f} seconds")
                time.sleep(scroll_delay)
            
            # Scroll back up a bit
            self.driver.execute_script(scroll_script.format(3))
            time.sleep(1 + random.random())
            
            return True
        except Exception as e:
            self.logger.error(f"Error during navigation with realistic behavior: {e}")
            return False
    
    def get_page_source(self):
        """Get the current page source."""
        if not self.driver:
            self.logger.error("WebDriver not initialized")
            return None
        
        try:
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"Error getting page source: {e}")
            return None
    
    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be present on the page.
        
        Args:
            by: Selenium By strategy (e.g., By.ID, By.CSS_SELECTOR)
            value: Element identifier
            timeout: Maximum time to wait in seconds
            
        Returns:
            The WebElement if found, None otherwise
        """
        if not self.driver:
            self.logger.error("WebDriver not initialized")
            return None
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for element: {by}={value}")
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for element: {e}")
            return None
    
    def take_screenshot(self, filename):
        """Take a screenshot for debugging purposes."""
        if not self.driver:
            self.logger.error("WebDriver not initialized")
            return False
        
        try:
            self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot saved to: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return False


class AutoTraderSeleniumScraper(SeleniumScraper):
    """Selenium-based scraper for AutoTrader."""
    
    def __init__(self, headless=True):
        """Initialize the AutoTrader Selenium scraper."""
        super().__init__(headless)
        self.logger = logging.getLogger("selenium_scraper.autotrader")
        self.base_url = "https://www.autotrader.co.uk"
    
    def search_cars(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for cars on AutoTrader based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            List of car listing dictionaries
        """
        self.logger.info(f"Searching AutoTrader with preferences: {preferences}")
        
        # Initialize the driver if needed
        if not self.driver:
            if not self.initialize_driver():
                return []
        
        try:
            # First visit the homepage with realistic behavior
            self.navigate_with_realistic_behavior(self.base_url)
            
            # Then navigate to the car search page
            search_url = self._construct_search_url(preferences)
            self.navigate_with_realistic_behavior(search_url)
            
            # Check if we're facing a CAPTCHA or security check
            if self._is_security_page():
                self.logger.warning("Security check or CAPTCHA detected")
                self.take_screenshot("autotrader_security_check.png")
                return []
            
            # Wait for the search results to load
            results_element = self.wait_for_element(By.CSS_SELECTOR, ".search-page__results")
            if not results_element:
                self.logger.warning("Search results not found")
                self.take_screenshot("autotrader_no_results.png")
                return []
            
            # Extract car listings
            return self._extract_listings()
            
        except Exception as e:
            self.logger.error(f"Error during AutoTrader search: {e}")
            return []
        finally:
            # Close the driver to free resources
            self.close_driver()
    
    def _construct_search_url(self, preferences: Dict[str, Any]) -> str:
        """Construct a search URL based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            String URL for searching
        """
        # Extract search parameters from preferences
        make = preferences.get('make', '')
        model = preferences.get('model', '')
        min_year = preferences.get('min_year', '')
        max_year = preferences.get('max_year', '')
        min_price = preferences.get('min_price', '')
        max_price = preferences.get('max_price', '')
        location = preferences.get('location', '')
        
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
        
        # Handle location
        if location:
            # Extract city/region from format like "UK: London"
            if ':' in location:
                parts = location.split(':')
                if len(parts) > 1:
                    city = parts[1].strip()
                    if city.lower() not in ['any', 'other']:
                        params['postcode'] = city
                        params['radius'] = 50  # 50 mile radius
        
        # Sorting by newest first is better for finding fresh deals
        params['sort'] = 'date-desc'
        
        # Add page size parameter
        params['page-size'] = 100
        
        # Construct the URL with parameters
        url_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/car-search?{url_params}"
