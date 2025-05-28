import os
import requests
import time
import urllib.parse

# Import URLs from config - assuming config.py is in the same directory or accessible via PYTHONPATH
from config import KROGER_TOKEN_URL, KROGER_AUTHORIZE_URL, KROGER_REDIRECT_URI


class AuthManager:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.app_access_token = None
        self.app_token_expires_at = 0
        self.user_access_token = None
        self.user_token_expires_at = 0
        self.user_refresh_token = None

    def _fetch_app_token(self):
        print("Fetching new application access token...")
        data = {
            "grant_type": "client_credentials",
            "scope": "product.compact"  # Or other relevant app scopes
        }
        try:
            response = requests.post(
                KROGER_TOKEN_URL,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            response.raise_for_status()
            token_data = response.json()
            self.app_access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 1800) - 60
            self.app_token_expires_at = time.time() + expires_in
            print("Successfully fetched application access token.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching application access token: {e}")
            self.app_access_token = None
            self.app_token_expires_at = 0

    def get_app_token(self):
        if not self.app_access_token or time.time() >= self.app_token_expires_at:
            self._fetch_app_token()
        return self.app_access_token

    def generate_authorize_url(self, redirect_uri, state=None, scopes=None):
        if scopes is None:
            scopes = ["cart.basic:write", "profile.compact"]
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes)
        }
        if state:
            params["state"] = state
        
        return f"{KROGER_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code, redirect_uri):
        print("Exchanging authorization code for user token...")
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        try:
            response = requests.post(
                KROGER_TOKEN_URL,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            response.raise_for_status()
            token_data = response.json()
            self.user_access_token = token_data["access_token"]
            self.user_refresh_token = token_data.get("refresh_token") # Ensure it's fetched
            expires_in = token_data.get("expires_in", 1800) - 60 
            self.user_token_expires_at = time.time() + expires_in
            print("Successfully exchanged code for user token.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error exchanging code for token: {e}")
            self.user_access_token = None
            self.user_refresh_token = None
            self.user_token_expires_at = 0
            return False

    def refresh_user_token(self):
        if not self.user_refresh_token:
            print("No refresh token available. Cannot refresh user token.")
            return False
        
        print("Refreshing user access token...")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.user_refresh_token
        }
        try:
            response = requests.post(
                KROGER_TOKEN_URL,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            response.raise_for_status()
            token_data = response.json()
            self.user_access_token = token_data["access_token"]
            # Kroger's OAuth might or might not return a new refresh token.
            # If it does, update it. Otherwise, the old one might still be valid.
            new_refresh_token = token_data.get("refresh_token")
            if new_refresh_token:
                self.user_refresh_token = new_refresh_token
            expires_in = token_data.get("expires_in", 1800) - 60
            self.user_token_expires_at = time.time() + expires_in
            print("Successfully refreshed user access token.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error refreshing user token: {e}")
            # Depending on the error (e.g., invalid_grant for expired refresh token),
            # we might need to clear all user tokens and force re-authorization.
            self.user_access_token = None
            self.user_token_expires_at = 0
            # Optionally clear self.user_refresh_token if it's definitively invalid
            # For now, let's assume it might be a temporary issue unless error indicates otherwise
            return False

    def get_user_token(self):
        if self.user_access_token and time.time() < self.user_token_expires_at:
            return self.user_access_token
        
        if self.user_refresh_token:
            print("User token expired or not found, attempting refresh...")
            if self.refresh_user_token():
                return self.user_access_token
        
        print("No valid user token or refresh failed. User needs to authorize.")
        return None


if __name__ == '__main__':
    # Load from config.py - ensure KROGER_CLIENT_ID and KROGER_CLIENT_SECRET are set there
    # or fall back to environment variables if config.py values are placeholders.
    try:
        from config import KROGER_CLIENT_ID, KROGER_CLIENT_SECRET
        CLIENT_ID = KROGER_CLIENT_ID if KROGER_CLIENT_ID != "YOUR_CLIENT_ID_HERE" else os.environ.get("KROGER_CLIENT_ID")
        CLIENT_SECRET = KROGER_CLIENT_SECRET if KROGER_CLIENT_SECRET != "YOUR_CLIENT_SECRET_HERE" else os.environ.get("KROGER_CLIENT_SECRET")
    except ImportError:
        print("config.py not found. Please ensure it exists or set environment variables.")
        CLIENT_ID = os.environ.get("KROGER_CLIENT_ID")
        CLIENT_SECRET = os.environ.get("KROGER_CLIENT_SECRET")


    if not CLIENT_ID or not CLIENT_SECRET:
        print("Please set KROGER_CLIENT_ID and KROGER_CLIENT_SECRET in config.py or as environment variables.")
    else:
        auth_manager = AuthManager(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        
        print("--- Testing App Token ---")
        app_token = auth_manager.get_app_token()
        if app_token:
            print(f"App Token: {app_token[:20]}...")
        else:
            print("Failed to retrieve app token.")

        if auth_manager.app_access_token:
            print("\nSimulating app token expiry...")
            auth_manager.app_token_expires_at = time.time() - 1 
            app_token = auth_manager.get_app_token()
            if app_token:
                print(f"Refreshed App Token: {app_token[:20]}...")
            else:
                print("Failed to refresh app token.")

        print("\n--- Testing User Auth Flow (Conceptual) ---")
        # 1. Generate Authorization URL
        # KROGER_REDIRECT_URI should be defined in your config.py
        auth_url = auth_manager.generate_authorize_url(redirect_uri=KROGER_REDIRECT_URI, state="teststate123")
        print(f"Authorization URL: {auth_url}")
        print("Please open the above URL in a browser, authorize, and paste the 'code' from the redirect URL here:")
        
        # Simulating the callback part - In a real app, a web server would handle this.
        # For this test, we'll manually input the code.
        # Example: If redirect is http://localhost:8080/callback?code=YOUR_CODE&state=teststate123
        
        # The following lines are for manual testing and would typically not be part of an automated script
        # as they require user interaction and copy-pasting.
        # mock_code = input("Enter the authorization code: ").strip()
        # if mock_code:
        #     print(f"\nAttempting to exchange code '{mock_code}' for token...")
        #     if auth_manager.exchange_code_for_token(mock_code, KROGER_REDIRECT_URI):
        #         user_token = auth_manager.get_user_token()
        #         print(f"User Token: {user_token[:20]}..." if user_token else "Failed to get user token.")
                
        #         if user_token:
        #             print("\nSimulating user token expiry...")
        #             auth_manager.user_token_expires_at = time.time() - 1
        #             refreshed_user_token = auth_manager.get_user_token()
        #             if refreshed_user_token:
        #                 print(f"Refreshed User Token: {refreshed_user_token[:20]}...")
        #                 print(f"New Refresh Token (if changed): {auth_manager.user_refresh_token[:20] if auth_manager.user_refresh_token else 'N/A'}...")
        #             else:
        #                 print("Failed to refresh user token.")
        #     else:
        #         print("Failed to exchange code for token.")
        # else:
        #     print("No code entered, skipping token exchange test.")

        print("\nUser auth flow test conceptualized. Manual interaction needed for full test.")
        print("To fully test, set a valid KROGER_REDIRECT_URI in config.py,")
        print("ensure it's registered in your Kroger Developer App settings,")
        print("and then manually run the exchange_code_for_token part after browser auth.")
