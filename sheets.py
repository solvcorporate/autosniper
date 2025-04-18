import os
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class SheetsManager:
    """Class to handle all Google Sheets operations."""
    
    def __init__(self, credentials_path, spreadsheet_id):
        """Initialize the Google Sheets manager.
        
        Args:
            credentials_path: Path to the Google API credentials JSON file
            spreadsheet_id: ID of the Google Spreadsheet
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.users_sheet = None  # Sheet for user information
        self.cars_sheet = None   # Sheet for car preferences
        self.connect()
    
    def connect(self):
        """Connect to Google Sheets API and open the spreadsheet."""
        try:
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            # Authenticate using the service account credentials
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, scope)
            
            # Create a gspread client
            self.client = gspread.authorize(credentials)
            
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            # Get or create the Users sheet
            try:
                self.users_sheet = spreadsheet.worksheet("Users")
                print("Connected to Users sheet")
            except gspread.exceptions.WorksheetNotFound:
                # Create Users sheet if it doesn't exist
                self.users_sheet = spreadsheet.add_worksheet(title="Users", rows=1000, cols=20)
                # Add headers
                self.users_sheet.append_row([
                    "user_id", "first_name", "last_name", "username", 
                    "join_date", "subscription_tier"
                ])
                print("Created new Users sheet")
            
            # Get or create the Cars sheet
            try:
                self.cars_sheet = spreadsheet.worksheet("Cars")
                print("Connected to Cars sheet")
            except gspread.exceptions.WorksheetNotFound:
                # Create Cars sheet if it doesn't exist
                self.cars_sheet = spreadsheet.add_worksheet(title="Cars", rows=1000, cols=20)
                # Add headers
                self.cars_sheet.append_row([
                    "user_id", "make", "model", "min_year", "max_year",
                    "min_price", "max_price", "location", "fuel_type", "transmission",
                    "created_at", "updated_at", "status"
                ])
                print("Created new Cars sheet")
            
            print("Connected to Google Sheets successfully!")
            return True
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            return False
    
    def add_user(self, user_id, first_name, last_name=None, username=None):
        """Add a new user to the spreadsheet.
        
        Args:
            user_id: Telegram user ID
            first_name: User's first name
            last_name: User's last name (optional)
            username: User's Telegram username (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if user already exists
            if self.user_exists(user_id):
                print(f"User {user_id} already exists in the spreadsheet.")
                return True
            
            # Prepare the new user data
            join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subscription_tier = "None"  # Default value for new users
            
            # Append the new user to the spreadsheet
            self.users_sheet.append_row([
                user_id,
                first_name,
                last_name if last_name else "",
                username if username else "",
                join_date,
                subscription_tier
            ])
            
            print(f"Added user {user_id} to the spreadsheet.")
            return True
        except Exception as e:
            print(f"Error adding user to Google Sheets: {e}")
            return False
    
    def user_exists(self, user_id):
        """Check if a user already exists in the spreadsheet.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if user exists, False otherwise
        """
        try:
            # Get all user_ids from column A
            user_ids = self.users_sheet.col_values(1)
            
            # Skip the header row and convert to strings for comparison
            return str(user_id) in [str(id) for id in user_ids[1:]]
        except Exception as e:
            print(f"Error checking if user exists: {e}")
            return False
    
    def update_subscription(self, user_id, subscription_tier):
        """Update a user's subscription tier.
        
        Args:
            user_id: Telegram user ID
            subscription_tier: New subscription tier ('Basic', 'Premium', or 'None')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all user_ids from column A
            user_ids = self.users_sheet.col_values(1)
            
            # Find the row index for this user
            try:
                row_idx = [str(id) for id in user_ids].index(str(user_id)) + 1  # +1 because sheets are 1-indexed
            except ValueError:
                print(f"User {user_id} not found in spreadsheet.")
                return False
            
            # Update the subscription_tier cell (column F)
            self.users_sheet.update_cell(row_idx, 6, subscription_tier)
            
            print(f"Updated subscription for user {user_id} to {subscription_tier}.")
            return True
        except Exception as e:
            print(f"Error updating subscription: {e}")
            return False
    
    def add_car_preferences(self, user_id, make, model, min_year, max_year, min_price, max_price, location, fuel_type="Any", transmission="Any"):
        """Add or update car preferences for a user.
        
        Args:
            user_id: Telegram user ID
            make: Car make (e.g., BMW, Toyota)
            model: Car model (e.g., 3 Series, Corolla)
            min_year: Minimum year
            max_year: Maximum year
            min_price: Minimum price
            max_price: Maximum price
            location: User's location preference
            fuel_type: Fuel type preference (optional)
            transmission: Transmission preference (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add new preferences with 'active' status
            self.cars_sheet.append_row([
                user_id,
                make,
                model,
                min_year,
                max_year,
                min_price,
                max_price,
                location,
                fuel_type,
                transmission,
                timestamp,  # created_at
                timestamp,  # updated_at
                'active'    # status
            ])
            
            print(f"Added car preferences for user {user_id}.")
            return True
        except Exception as e:
            print(f"Error adding car preferences: {e}")
            return False
    
    def get_car_preferences(self, user_id):
        """Get all car preferences for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            list: List of dictionaries containing car preferences, or empty list if none found
        """
        try:
            # Get all data from Cars sheet
            all_data = self.cars_sheet.get_all_records()
            
            # Filter for rows with matching user_id and active status
            user_preferences = [
                row for row in all_data 
                if str(row['user_id']) == str(user_id) and row.get('status', '') == 'active'
            ]
            
            return user_preferences
        except Exception as e:
            print(f"Error getting car preferences: {e}")
            return []
    
    def set_preference_inactive(self, user_id, make, model):
        """Set a specific car preference to inactive
        
        Args:
            user_id: Telegram user ID
            make: Car make to match
            model: Car model to match
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all data from Cars sheet
            all_records = self.cars_sheet.get_all_records()
            
            # Find the specific preference
            for idx, row in enumerate(all_records):
                if (str(row['user_id']) == str(user_id) and 
                    row['make'] == make and 
                    row['model'] == model and
                    row.get('status', '') == 'active'):
                    
                    # Add 2 to account for header row and 0-indexing to 1-indexing
                    row_idx = idx + 2
                    # Update timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # Updated_at is in column L (12)
                    self.cars_sheet.update_cell(row_idx, 12, timestamp)
                    # Status is in column M (13)
                    self.cars_sheet.update_cell(row_idx, 13, 'inactive')
                    print(f"Set preference inactive for user {user_id}: {make} {model}")
                    return True
            
            print(f"No matching active preference found for user {user_id}: {make} {model}")
            return False
        except Exception as e:
            print(f"Error setting preference inactive: {e}")
            return False
    
    def get_active_preferences_count(self, user_id):
        """Get the count of active preferences for a user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            int: Number of active preferences
        """
        try:
            preferences = self.get_car_preferences(user_id)
            return len(preferences)
        except Exception as e:
            print(f"Error counting active preferences: {e}")
            return 0

def setup_listings_sheet(self):
    """Set up the Listings sheet if it doesn't exist.
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        
        # Get or create the Listings sheet
        try:
            self.listings_sheet = spreadsheet.worksheet("Listings")
            print("Connected to Listings sheet")
            return True
        except gspread.exceptions.WorksheetNotFound:
            # Create Listings sheet if it doesn't exist
            self.listings_sheet = spreadsheet.add_worksheet(title="Listings", rows=1000, cols=20)
            # Add headers
            self.listings_sheet.append_row([
                "listing_id", "source", "make", "model", "year", "price", 
                "mileage", "location", "fuel_type", "transmission",
                "url", "title", "scraped_at", "matched_to", "notified_at", "score"
            ])
            print("Created new Listings sheet")
            return True
    except Exception as e:
        print(f"Error setting up Listings sheet: {e}")
        return False

def add_listing(self, listing):
    """Add a new car listing to the spreadsheet.
    
    Args:
        listing: Dictionary containing listing details
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Make sure Listings sheet is available
        if not hasattr(self, 'listings_sheet') or not self.listings_sheet:
            if not self.setup_listings_sheet():
                return False
        
        # Check if this listing already exists
        listing_id = self._generate_listing_id(listing)
        if self.listing_exists(listing_id):
            print(f"Listing {listing_id} already exists in the spreadsheet.")
            return True
        
        # Prepare the listing data
        row_data = [
            listing_id,
            listing.get('source', ''),
            listing.get('make', ''),
            listing.get('model', ''),
            listing.get('year', ''),
            listing.get('price', ''),
            listing.get('mileage', ''),
            listing.get('location', ''),
            listing.get('fuel_type', ''),
            listing.get('transmission', ''),
            listing.get('url', ''),
            listing.get('title', ''),
            listing.get('scraped_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            '',  # matched_to (user_id) - will be filled later
            '',  # notified_at - will be filled later
            ''   # score - will be calculated later
        ]
        
        # Append the new listing to the spreadsheet
        self.listings_sheet.append_row(row_data)
        
        print(f"Added listing {listing_id} to the spreadsheet.")
        return True
    except Exception as e:
        print(f"Error adding listing to Google Sheets: {e}")
        return False

def listing_exists(self, listing_id):
    """Check if a listing already exists in the spreadsheet.
    
    Args:
        listing_id: Unique ID for the listing
        
    Returns:
        bool: True if listing exists, False otherwise
    """
    try:
        # Make sure Listings sheet is available
        if not hasattr(self, 'listings_sheet') or not self.listings_sheet:
            if not self.setup_listings_sheet():
                return False
        
        # Get all listing_ids from column A
        listing_ids = self.listings_sheet.col_values(1)
        
        # Skip the header row
        return listing_id in listing_ids[1:]
    except Exception as e:
        print(f"Error checking if listing exists: {e}")
        return False

def _generate_listing_id(self, listing):
    """Generate a unique ID for a listing.
    
    Args:
        listing: Dictionary containing listing details
        
    Returns:
        str: Unique listing ID
    """
    # Use source, make, model, year, price, and mileage to create a unique ID
    source = listing.get('source', '').lower()
    make = listing.get('make', '').lower()
    model = listing.get('model', '').lower()
    year = str(listing.get('year', ''))
    price = str(listing.get('price', ''))
    mileage = str(listing.get('mileage', ''))
    url = listing.get('url', '')
    
    # Extract a unique identifier from the URL if possible
    url_id = ''
    if url:
        # Try to extract ID from different URL patterns
        if 'autotrader.co.uk' in url or 'autotrader.ie' in url:
            # AutoTrader URLs often have a listing ID in the path
            import re
            match = re.search(r'/([0-9]+)$', url)
            if match:
                url_id = match.group(1)
    
    # If we found a URL ID, use it
    if url_id:
        listing_id = f"{source}_{url_id}"
    else:
        # Otherwise create a hash from the listing details
        import hashlib
        # Combine the key fields
        combined = f"{source}_{make}_{model}_{year}_{price}_{mileage}"
        # Create a hash
        listing_id = hashlib.md5(combined.encode()).hexdigest()[:12]
    
    return listing_id

# Helper function to create a sheets manager from environment variables
def get_sheets_manager():
    """Create a SheetsManager instance using environment variables.
    
    Returns:
        SheetsManager: Instance of the SheetsManager class
    """
    creds_content = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
    
    if not creds_content or not spreadsheet_id:
        print("Missing environment variables for Google Sheets integration.")
        return None
    
    # Create a temporary credentials file from the environment variable
    try:
        creds_dict = json.loads(creds_content)
        temp_creds_path = 'temp_credentials.json'
        
        with open(temp_creds_path, 'w') as f:
            json.dump(creds_dict, f)
        
        # Create the sheets manager
        manager = SheetsManager(temp_creds_path, spreadsheet_id)
        return manager
    except Exception as e:
        print(f"Error creating sheets manager: {e}")
        return None
