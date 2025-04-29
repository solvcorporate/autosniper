"""
Scheduler for periodic tasks.
"""

import logging
import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta

from scraper_manager import get_scraper_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scheduler")

class Scheduler:
    """Scheduler for running periodic tasks."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.logger = logging.getLogger("scheduler")
        self.thread = None
        self.running = False
        self.logger.info("Scheduler initialized")
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.thread and self.thread.is_alive():
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler)
        self.thread.daemon = True  # This will allow the thread to exit when the main program exits
        self.thread.start()
        self.logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        self.logger.info("Scheduler thread started")
        
        # Schedule jobs
        schedule.every(15).minutes.do(self._run_scraper_job)
        
        # Run the scraper once at startup (after a short delay)
        schedule.every(1).minutes.do(self._run_initial_scraper_job).tag('startup')
        
        # Add this line to check for expired subscriptions daily
        schedule.every().day.at("00:00").do(self._check_expired_subscriptions)
        
        self.logger.info("Jobs scheduled")
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
        
        self.logger.info("Scheduler thread stopped")
    
    def _run_scraper_job(self):
        """Run the scraper job."""
        try:
            self.logger.info("Running scheduled scraper job")
            scraper_manager = get_scraper_manager()
            stats = scraper_manager.run_scraper_job()
            self.logger.info(f"Scheduled scraper job completed: {stats}")
            return stats
        except Exception as e:
            self.logger.error(f"Error running scheduled scraper job: {e}")
            return None
    
    def _run_initial_scraper_job(self):
        """Run the initial scraper job at startup."""
        self.logger.info("Running initial scraper job")
        result = self._run_scraper_job()
        
        # Clear the startup job after it runs once
        schedule.clear('startup')
        
        return result
    
    def _check_expired_subscriptions(self):
        """Check for expired subscriptions and update status."""
        try:
            self.logger.info("Checking for expired subscriptions")
            
            # Get sheets manager
            from sheets import get_sheets_manager
            sheets_manager = get_sheets_manager()
            
            if not sheets_manager:
                self.logger.error("Failed to get sheets_manager")
                return
            
            # Check for expired subscriptions
            count = sheets_manager.check_subscriptions_expiry()
            
            self.logger.info(f"Updated {count} expired subscriptions")
            return count
        except Exception as e:
            self.logger.error(f"Error checking expired subscriptions: {e}")
            return 0

# Global scheduler instance
_scheduler = None

def get_scheduler():
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler
