# Kroger API Credentials
# Please replace with your actual Client ID and Client Secret from the Kroger Developer Portal.
# These are required for OAuth2 authentication.
KROGER_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
KROGER_CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"

# It's also good practice to have the Redirect URI here if you're using the Authorization Code flow.
KROGER_REDIRECT_URI = "http://localhost:8080/callback" # Example for local testing

# Kroger API Environment
# For development, use "https://api-ce.kroger.com" (Certification)
# For production, use "https://api.kroger.com"
KROGER_API_BASE_URL = "https://api.kroger.com" # Default to production
KROGER_AUTHORIZE_URL = f"{KROGER_API_BASE_URL}/v1/connect/oauth2/authorize"
KROGER_TOKEN_URL = f"{KROGER_API_BASE_URL}/v1/connect/oauth2/token"
KROGER_LOCATIONS_URL = f"{KROGER_API_BASE_URL}/v1/locations"
KROGER_PRODUCTS_URL = f"{KROGER_API_BASE_URL}/v1/products"
# The cart API endpoint might vary based on public vs partner API.
# This is a placeholder based on the documentation.
KROGER_CART_API_URL = f"{KROGER_API_BASE_URL}/v1/cart/addItem" 

# You can add other configuration details here as needed.
