"""
Proxy manager for rotating proxies to avoid scraper detection.
"""

import logging
import random
import time
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("proxy_manager")

class ProxyManager:
    """Manager for rotating proxies to avoid detection."""
    
    def __init__(self, use_proxies: bool = False):
        """Initialize the proxy manager.
        
        Args:
            use_proxies: Whether to use proxies or not
        """
        self.use_proxies = use_proxies
        self.proxies = []
        self.current_proxy = None
        self.last_rotation = 0
        self.rotation_interval = 5 * 60  # 5 minutes
        
        if use_proxies:
            # Initialize with a list of free proxies for testing
            # In production, you would want to use a paid proxy service
            self.proxies = [
                # Add some free proxies here if needed
                # Format: "http://ip:port"
            ]
            self.rotate_proxy()
    
    def rotate_proxy(self) -> Dict[str, str]:
        """Rotate to a new proxy.
        
        Returns:
            Dictionary with proxy configuration
        """
        if not self.use_proxies or not self.proxies:
            return {}
        
        self.current_proxy = random.choice(self.proxies)
        self.last_rotation = time.time()
        
        proxy_dict = {
            "http": self.current_proxy,
            "https": self.current_proxy
        }
        
        logger.info(f"Rotated to new proxy: {self.current_proxy}")
        return proxy_dict
    
    def get_proxy(self) -> Dict[str, str]:
        """Get the current proxy configuration.
        
        Returns:
            Dictionary with proxy configuration
        """
        # Check if it's time to rotate
        if self.use_proxies and time.time() - self.last_rotation > self.rotation_interval:
            return self.rotate_proxy()
        
        if self.current_proxy:
            return {
                "http": self.current_proxy,
                "https": self.current_proxy
            }
        return {}
