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
        self.sheet = None
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
            self.sheet = self.client.open_by_key(self.spreadsheet_id).sheet1
            
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
            self.sheet.append_row([
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
            user_ids = self.sheet.col_values(1)
            
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
            user_ids = self.sheet.col_values(1)
            
            # Find the row index for this user
            try:
                row_idx = [str(id) for id in user_ids].index(str(user_id)) + 1  # +1 because sheets are 1-indexed
            except ValueError:
                print(f"User {user_id} not found in spreadsheet.")
                return False
            
            # Update the subscription_tier cell (column F)
            self.sheet.update_cell(row_idx, 6, subscription_tier)
            
            print(f"Updated subscription for user {user_id} to {subscription_tier}.")
            return True
        except Exception as e:
            print(f"Error updating subscription: {e}")
            return False

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
