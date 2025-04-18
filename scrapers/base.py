import os
import logging
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseScraper(ABC):
    """Base class for all scrapers. Provides common functionality and defines the interface."""
    
    def __init__(self, name: str, base_url: str, user_agent: Optional[str] = None):
        """Initialize the base scraper with a name and base URL.
        
        Args:
            name: Name of the scraper (e.g., 'AutoTrader')
            base_url: Base URL for the site being scraped
            user_agent: Optional user agent string to use for requests
        """
        self.name = name
        self.base_url = base_url
        self.logger = logging.getLogger(f"scraper.{name.lower()}")
        
        # Set up session with appropriate headers
        self.session = requests.Session()
        if user_agent:
            self.user_agent = user_agent
        else:
            # Default user agent that mimics a regular browser
            self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        self.logger.info(f"Initialized {self.name} scraper for {self.base_url}")
    
    def make_request(self, url: str, params: Optional[Dict[str, Any]] = None, 
                     max_retries: int = 3, retry_delay: int = 5) -> Optional[requests.Response]:
        """Make an HTTP request with automatic retries and random delays.
        
        Args:
            url: URL to request
            params: Optional query parameters
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            
        Returns:
            Response object or None if all retries failed
        """
        attempt = 0
        
        while attempt < max_retries:
            try:
                # Add a randomized delay to avoid detection
                if attempt > 0:
                    sleep_time = retry_delay * (1 + random.random())
                    self.logger.info(f"Retry attempt {attempt}, waiting {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                
                self.logger.info(f"Making request to {url}")
                response = self.session.get(url, params=params, timeout=30)
                
                # Check if response is valid
                response.raise_for_status()  # Raise exception for 4XX/5XX status codes
                
                if "application/json" in response.headers.get("Content-Type", ""):
                    # If it's a JSON response, try to parse it
                    try:
                        response.json()
                    except ValueError:
                        self.logger.warning(f"Received invalid JSON from {url}")
                        attempt += 1
                        continue
                
                # Check for potential bot detection or captcha pages
                if self._is_bot_detected(response):
                    self.logger.warning(f"Bot detection triggered for {url}")
                    attempt += 1
                    continue
                    
                return response
                
            except requests.RequestException as e:
                self.logger.error(f"Request failed: {e}")
                attempt += 1
                
                if attempt >= max_retries:
                    self.logger.error(f"Max retries ({max_retries}) reached for {url}")
                    return None
        
        return None
    
    def _is_bot_detected(self, response: requests.Response) -> bool:
        """Check if the response indicates bot detection.
        
        Args:
            response: Response object to check
            
        Returns:
            True if bot detection is detected, False otherwise
        """
        # Look for common bot detection patterns in content
        content_lower = response.text.lower()
        
        # Check for common captcha and verification keywords
        bot_indicators = [
            "captcha", "robot", "human verification", "are you a bot",
            "automated access", "detection", "blocked", "security check"
        ]
        
        if any(indicator in content_lower for indicator in bot_indicators):
            return True
            
        # Check for unusually short content that might indicate a redirect or block
        if len(response.text) < 500 and response.status_code == 200:
            # This might be a bot detection page or redirect
            self.logger.warning(f"Suspiciously short content ({len(response.text)} bytes)")
            return True
            
        return False
    
    def _parse_html(self, html_content: str) -> Optional[BeautifulSoup]:
        """Parse HTML content with BeautifulSoup.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            BeautifulSoup object or None if parsing failed
        """
        try:
            return BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to parse HTML: {e}")
            return None
    
    @abstractmethod
    def construct_search_url(self, preferences: Dict[str, Any]) -> str:
        """Construct a search URL based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            String URL for searching
        """
        pass
    
    @abstractmethod
    def extract_listings(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract car listings from HTML content.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of dictionaries with car details
        """
        pass
    
    def format_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Format and standardize a listing.
        
        This ensures all listings from different sources have a consistent format.
        
        Args:
            listing: Raw listing dictionary
            
        Returns:
            Standardized listing dictionary
        """
        # Add source and timestamp to the listing
        formatted = listing.copy()
        formatted['source'] = self.name
        formatted['scraped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Ensure all required fields are present
        required_fields = ['make', 'model', 'year', 'price', 'mileage', 'url']
        for field in required_fields:
            if field not in formatted:
                formatted[field] = None
                self.logger.warning(f"Missing required field '{field}' in listing")
        
        return formatted
    
    def search(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for car listings based on user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            List of car listings
        """
        search_url = self.construct_search_url(preferences)
        self.logger.info(f"Searching with URL: {search_url}")
        
        response = self.make_request(search_url)
        if not response:
            self.logger.error("Failed to retrieve search results")
            return []
        
        listings = self.extract_listings(response.text)
        if not listings:
            self.logger.info("No listings found")
            return []
        
        # Format all listings to ensure consistency
        formatted_listings = [self.format_listing(listing) for listing in listings]
        self.logger.info(f"Found {len(formatted_listings)} listings")
        
        return formatted_listings
    
    def run_scraper(self, preferences_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run the scraper for multiple sets of preferences.
        
        Args:
            preferences_list: List of preference dictionaries
            
        Returns:
            List of car listings matching preferences
        """
        all_listings = []
        
        for preferences in preferences_list:
            try:
                self.logger.info(f"Running search for preferences: {preferences}")
                listings = self.search(preferences)
                all_listings.extend(listings)
                
                # Add a random delay between searches to avoid detection
                delay = 1 + random.random() * 2  # 1-3 seconds
                time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error running search for preferences {preferences}: {e}")
        
        return all_listings
