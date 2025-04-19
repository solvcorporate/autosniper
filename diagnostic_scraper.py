"""
Diagnostic tool for identifying bot detection mechanisms.
This script performs detailed tests on car listing websites to determine
what triggers their bot detection systems and logs additional information.
"""

import logging
import requests
import time
import random
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("diagnostic_scraper")

class ScraperDiagnostic:
    """Diagnostic class for analyzing bot detection on scraped websites."""
    
    def __init__(self, site_name):
        """Initialize the diagnostic tool.
        
        Args:
            site_name: Name of the site to test ("autotrader" or "gumtree")
        """
        self.site_name = site_name.lower()
        self.logger = logging.getLogger(f"diagnostic_scraper.{self.site_name}")
        
        # Set site-specific configuration
        if self.site_name == "autotrader":
            self.base_url = "https://www.autotrader.co.uk"
            self.search_path = "/car-search"
        elif self.site_name == "gumtree":
            self.base_url = "https://www.gumtree.com"
            self.search_path = "/cars-vans-motorbikes/cars"
        else:
            raise ValueError(f"Unsupported site name: {site_name}")
        
        # Common user agents
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
        
        # Common headers
        self.common_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "TE": "trailers",
            "DNT": "1",
        }
        
        # Test parameters
        self.car_make = "Ford"
        self.car_model = "Focus"
        
        # Session for maintaining cookies
        self.session = requests.Session()
    
    def run_diagnostics(self):
        """Run a series of diagnostic tests to identify bot detection mechanisms."""
        self.logger.info(f"Starting diagnostics for {self.site_name}")
        
        # Test 1: Basic request with default settings
        result_basic = self._test_basic_request()
        
        # Test 2: Request with randomized delays and headers
        result_random = self._test_with_random_delays_and_headers()
        
        # Test 3: Mimic browser behavior
        result_browser = self._test_mimic_browser_behavior()
        
        # Test 4: Test with referrer headers
        result_referrer = self._test_with_referrer()
        
        # Analyze results
        self._analyze_results({
            "basic": result_basic,
            "random": result_random,
            "browser": result_browser,
            "referrer": result_referrer
        })
    
    def _test_basic_request(self):
        """Test a basic request with minimal headers."""
        self.logger.info("Test 1: Basic request with minimal headers")
        
        # Reset session
        self.session = requests.Session()
        
        # Basic headers
        headers = {
            "User-Agent": self.user_agents[0]
        }
        
        # Create search URL
        url = self._create_search_url()
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            detected = self._is_bot_detected(response)
            
            self.logger.info(f"Basic request status: {response.status_code}")
            self.logger.info(f"Bot detected: {detected}")
            
            # Save response for analysis
            self._save_response(response, "basic")
            
            return {
                "success": response.status_code == 200 and not detected,
                "status_code": response.status_code,
                "detected": detected,
                "url": url,
                "headers": headers,
                "content_type": response.headers.get('Content-Type', ''),
                "content_length": len(response.text)
            }
        except Exception as e:
            self.logger.error(f"Error in basic request test: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "headers": headers
            }
    
    def _test_with_random_delays_and_headers(self):
        """Test with randomized delays and headers."""
        self.logger.info("Test 2: Request with randomized delays and headers")
        
        # Reset session
        self.session = requests.Session()
        
        # Random delay
        delay = 2 + random.random() * 3  # 2-5 seconds
        self.logger.info(f"Waiting for {delay:.2f} seconds before request")
        time.sleep(delay)
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        
        # Full headers
        headers = self.common_headers.copy()
        headers["User-Agent"] = user_agent
        
        # Create search URL
        url = self._create_search_url()
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            detected = self._is_bot_detected(response)
            
            self.logger.info(f"Random delay/headers request status: {response.status_code}")
            self.logger.info(f"Bot detected: {detected}")
            
            # Save response for analysis
            self._save_response(response, "random")
            
            return {
                "success": response.status_code == 200 and not detected,
                "status_code": response.status_code,
                "detected": detected,
                "url": url,
                "headers": headers,
                "user_agent": user_agent,
                "delay": delay,
                "content_type": response.headers.get('Content-Type', ''),
                "content_length": len(response.text)
            }
        except Exception as e:
            self.logger.error(f"Error in random delay/headers test: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "headers": headers,
                "user_agent": user_agent,
                "delay": delay
            }
    
    def _test_mimic_browser_behavior(self):
        """Test mimicking browser behavior with multiple requests."""
        self.logger.info("Test 3: Mimic browser behavior with multiple requests")
        
        # Reset session
        self.session = requests.Session()
        
        # Start with the homepage
        user_agent = random.choice(self.user_agents)
        headers = self.common_headers.copy()
        headers["User-Agent"] = user_agent
        
        try:
            # First visit the homepage
            self.logger.info(f"Visiting homepage: {self.base_url}")
            home_response = self.session.get(self.base_url, headers=headers, timeout=30)
            time.sleep(2 + random.random() * 2)  # Wait 2-4 seconds
            
            # Then navigate to the cars section
            cars_url = f"{self.base_url}{self.search_path}"
            self.logger.info(f"Visiting cars section: {cars_url}")
            headers["Referer"] = self.base_url
            cars_response = self.session.get(cars_url, headers=headers, timeout=30)
            time.sleep(2 + random.random() * 2)  # Wait 2-4 seconds
            
            # Finally make the search request
            search_url = self._create_search_url()
            self.logger.info(f"Making search request: {search_url}")
            headers["Referer"] = cars_url
            search_response = self.session.get(search_url, headers=headers, timeout=30)
            
            detected = self._is_bot_detected(search_response)
            
            self.logger.info(f"Browser behavior request status: {search_response.status_code}")
            self.logger.info(f"Bot detected: {detected}")
            
            # Save response for analysis
            self._save_response(search_response, "browser")
            
            return {
                "success": search_response.status_code == 200 and not detected,
                "status_code": search_response.status_code,
                "detected": detected,
                "url": search_url,
                "headers": headers,
                "user_agent": user_agent,
                "content_type": search_response.headers.get('Content-Type', ''),
                "content_length": len(search_response.text),
                "home_status": home_response.status_code,
                "cars_status": cars_response.status_code
            }
        except Exception as e:
            self.logger.error(f"Error in browser behavior test: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": self.base_url,
                "headers": headers,
                "user_agent": user_agent
            }
    
    def _test_with_referrer(self):
        """Test using search engine referrers."""
        self.logger.info("Test 4: Test with search engine referrer")
        
        # Reset session
        self.session = requests.Session()
        
        # Random delay
        delay = 2 + random.random() * 3  # 2-5 seconds
        self.logger.info(f"Waiting for {delay:.2f} seconds before request")
        time.sleep(delay)
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        
        # Full headers with search engine referrer
        headers = self.common_headers.copy()
        headers["User-Agent"] = user_agent
        
        # Use Google as referrer
        referrer = "https://www.google.com/search?q=used+ford+focus+for+sale"
        headers["Referer"] = referrer
        
        # Create search URL
        url = self._create_search_url()
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            detected = self._is_bot_detected(response)
            
            self.logger.info(f"Referrer request status: {response.status_code}")
            self.logger.info(f"Bot detected: {detected}")
            
            # Save response for analysis
            self._save_response(response, "referrer")
            
            return {
                "success": response.status_code == 200 and not detected,
                "status_code": response.status_code,
                "detected": detected,
                "url": url,
                "headers": headers,
                "user_agent": user_agent,
                "referrer": referrer,
                "content_type": response.headers.get('Content-Type', ''),
                "content_length": len(response.text)
            }
        except Exception as e:
            self.logger.error(f"Error in referrer test: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "headers": headers,
                "user_agent": user_agent,
                "referrer": referrer
            }
    
    def _create_search_url(self):
        """Create a search URL for the tests."""
        if self.site_name == "autotrader":
            # AutoTrader URL
            params = {
                "make": self.car_make,
                "model": self.car_model,
                "postcode": "M11AA",  # Manchester
                "radius": 50,
                "sort": "date-desc",
                "page-size": 20
            }
            return f"{self.base_url}{self.search_path}?{urlencode(params)}"
        elif self.site_name == "gumtree":
            # Gumtree URL
            return f"{self.base_url}{self.search_path}/{self.car_make.lower()}?q={self.car_model.lower()}"
    
    def _is_bot_detected(self, response):
        """Check if the response indicates bot detection."""
        # Check for common bot detection indicators
        content_lower = response.text.lower()
        
        # Common detection indicators
        bot_indicators = [
            "captcha", "robot", "human verification", "are you a bot",
            "automated access", "detection", "blocked", "security check",
            "unusual traffic", "automated requests"
        ]
        
        # Check for indicators in content
        if any(indicator in content_lower for indicator in bot_indicators):
            return True
        
        # Check for suspiciously short content
        if len(response.text) < 5000 and response.status_code == 200:
            return True
        
        # Check for redirects to security pages
        if response.history and any('security' in r.url for r in response.history):
            return True
        
        # Site-specific checks
        if self.site_name == "autotrader":
            # Check if we can find car listings
            if not re.search(r'search-page__results', content_lower):
                return True
        elif self.site_name == "gumtree":
            # Check if we can find car listings
            if not re.search(r'listing-maxi', content_lower) and not re.search(r'car-list__result', content_lower):
                return True
        
        return False
    
    def _save_response(self, response, test_name):
        """Save the HTML response for analysis."""
        try:
            # Create a filename based on site and test
            filename = f"{self.site_name}_{test_name}_response.html"
            
            # Save the HTML content
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.logger.info(f"Saved response to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving response: {e}")
    
    def _analyze_results(self, results):
        """Analyze the test results and provide recommendations."""
        self.logger.info("Analyzing test results")
        
        successful_tests = []
        failed_tests = []
        
        for test_name, result in results.items():
            if result.get("success", False):
                successful_tests.append(test_name)
            else:
                failed_tests.append(test_name)
        
        # Log overall success/failure
        success_rate = len(successful_tests) / len(results) * 100
        self.logger.info(f"Success rate: {success_rate:.1f}%")
        self.logger.info(f"Successful tests: {successful_tests}")
        self.logger.info(f"Failed tests: {failed_tests}")
        
        # Recommendations based on results
        recommendations = []
        
        if not successful_tests:
            recommendations.append("All tests failed. Strong anti-bot measures are in place.")
            recommendations.append("Consider using Selenium with headless Chrome to better emulate a real browser.")
            recommendations.append("Implement rate limiting and longer delays between requests.")
            recommendations.append("Consider using proxy rotation to vary IP addresses.")
        else:
            if "browser" in successful_tests:
                recommendations.append("Browser behavior mimicking was successful. Implement multi-stage requests that mimic normal browsing patterns.")
            if "referrer" in successful_tests:
                recommendations.append("Using search engine referrers was successful. Add realistic referrer headers to requests.")
            if "random" in successful_tests:
                recommendations.append("Randomized delays and headers were successful. Implement more variation in request patterns.")
        
        if "basic" in failed_tests:
            recommendations.append("Basic requests failed. The site is definitely using bot detection.")
        
        # Site-specific recommendations
        if self.site_name == "autotrader":
            recommendations.append("AutoTrader has sophisticated bot detection. Consider implementing browser automation.")
        elif self.site_name == "gumtree":
            recommendations.append("Gumtree uses URL structure detection. Ensure your URLs match exactly what a real browser would use.")
        
        # Log recommendations
        self.logger.info("Recommendations:")
        for i, recommendation in enumerate(recommendations, 1):
            self.logger.info(f"{i}. {recommendation}")
        
        # Return analysis
        return {
            "success_rate": success_rate,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "recommendations": recommendations
        }


def run_diagnostics():
    """Run diagnostics for both sites."""
    # Test AutoTrader
    autotrader_diagnostic = ScraperDiagnostic("autotrader")
    autotrader_diagnostic.run_diagnostics()
    
    # Test Gumtree
    gumtree_diagnostic = ScraperDiagnostic("gumtree")
    gumtree_diagnostic.run_diagnostics()


if __name__ == "__main__":
    run_diagnostics()
