import requests
# Assuming 'mcp' library has a 'tool' decorator or similar mechanism.
# We will define the tool decorator if it's not available or adjust as needed.
# For now, let's assume a placeholder decorator.
try:
    from mcp import tool
except ImportError:
    # Fallback if mcp.tool is not available (e.g., during standalone testing)
    def tool(name, description):
        def decorator(func):
            func.tool_name = name
            func.tool_description = description
            return func
        return decorator

from auth import AuthManager
# Ensure KROGER_PRODUCTS_URL, KROGER_CART_API_URL, KROGER_REDIRECT_URI are imported
from config import (
    KROGER_CLIENT_ID, KROGER_CLIENT_SECRET, 
    KROGER_LOCATIONS_URL, KROGER_PRODUCTS_URL,
    KROGER_CART_API_URL, KROGER_REDIRECT_URI 
)

# Initialize AuthManager.
auth_manager = None
if not KROGER_CLIENT_ID or KROGER_CLIENT_ID == "YOUR_CLIENT_ID_HERE" or \
   not KROGER_CLIENT_SECRET or KROGER_CLIENT_SECRET == "YOUR_CLIENT_SECRET_HERE":
    print("Warning: KROGER_CLIENT_ID or KROGER_CLIENT_SECRET is not configured in config.py. Kroger API tool functionality will be limited.")
else:
    auth_manager = AuthManager(client_id=KROGER_CLIENT_ID, client_secret=KROGER_CLIENT_SECRET)

@tool(name="find_stores", description="Find Kroger store locations by ZIP code (returns nearest stores with IDs).")
def find_stores(zip_code: str, radius_miles: int = 10, limit: int = 5) -> list | dict:
    """
    Returns a list of stores near the given ZIP code. 
    Each entry includes locationId, name, address, distance.
    Returns a dict with an error key if an error occurs.
    """
    if not auth_manager:
        return {"error": "AuthManager not initialized. Configure KROGER_CLIENT_ID and KROGER_CLIENT_SECRET in config.py."}

    token = auth_manager.get_app_token()
    if not token:
        return {"error": "Failed to obtain application access token. Check credentials and Kroger API connectivity."}

    url = KROGER_LOCATIONS_URL 
    params = {
        "filter.zipCode.near": zip_code,
        "filter.radiusInMiles": str(radius_miles), 
        "filter.limit": str(limit) 
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json" 
    }

    try:
        print(f"Calling Kroger API: GET {url} with params {params}")
        resp = requests.get(url, headers=headers, params=params, timeout=10) 
        resp.raise_for_status()  
        data = resp.json()
        stores = data.get("data", [])
        
        return stores
    except requests.exceptions.HTTPError as http_err:
        # Refined error handling for find_stores
        error_message_for_print = f"HTTP error occurred for find_stores: {http_err}"
        error_response = {
            "error": "API request to Kroger for find_stores failed.",
            "details": str(http_err)
        }
        if http_err.response is not None:
            error_response["status_code"] = http_err.response.status_code
            error_response["raw_response"] = http_err.response.text
            error_message_for_print += f" - Status Code: {http_err.response.status_code}, Response: {http_err.response.text}"
        print(error_message_for_print)
        return error_response
    except requests.exceptions.Timeout as timeout_err:
        print(f"Request timed out for find_stores: {timeout_err}")
        return {"error": "Network request to Kroger timed out.", "details": str(timeout_err)}
    except requests.exceptions.RequestException as req_err:
        print(f"Request exception occurred for find_stores: {req_err}")
        return {"error": "Network request to Kroger failed.", "details": str(req_err)}
    except Exception as e:
        print(f"An unexpected error occurred in find_stores: {e}")
        return {"error": "An unexpected error occurred while finding stores.", "details": str(e)}

@tool(name="search_products", description="Search Kroger products by keyword at a given store (locationId).")
def search_products(query: str, location_id: str, limit: int = 10) -> list | dict:
    """
    Returns a list of products matching the search query at the specified store.
    Each product in the list may include id, name, price, and availability info.
    Returns a dict with an error key if an error occurs.
    """
    if not auth_manager:
        return {"error": "AuthManager not initialized. Configure Client ID/Secret."}

    token = auth_manager.get_app_token()
    if not token:
        return {"error": "Failed to obtain application access token."}

    url = KROGER_PRODUCTS_URL 
    params = {
        "filter.term": query,
        "filter.locationId": location_id,
        "filter.limit": str(limit) 
    }
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    try:
        print(f"Calling Kroger API: GET {url} with params {params}")
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()  
        data = resp.json()
        products = data.get("data", [])
        return products
    except requests.exceptions.HTTPError as http_err:
        # Refined error handling for search_products
        error_message_for_print = f"HTTP error occurred for search_products: {http_err}"
        error_response = {
            "error": "API request to Kroger for product search failed.",
            "details": str(http_err)
        }
        if http_err.response is not None:
            error_response["status_code"] = http_err.response.status_code
            error_response["raw_response"] = http_err.response.text
            error_message_for_print += f" - Status Code: {http_err.response.status_code}, Response: {http_err.response.text}"
        print(error_message_for_print)
        return error_response
    except requests.exceptions.Timeout: 
        print("Request to Kroger API for search_products timed out.")
        return {"error": "API request to Kroger timed out.", "details": "Timeout after 10 seconds"}
    except requests.exceptions.RequestException as req_err:
        print(f"Request exception occurred during product search: {req_err}")
        return {"error": "Network request to Kroger for product search failed.", "details": str(req_err)}
    except Exception as e:
        print(f"An unexpected error occurred during product search: {e}")
        return {"error": "An unexpected error occurred while searching products.", "details": str(e)}

@tool(name="get_product", description="Get detailed information for a product by ID (price, size, stock, fulfillment options).")
def get_product(product_id: str, location_id: str) -> dict:
    """
    Returns a dictionary with detailed product information.
    Requires product_id and location_id for store-specific pricing and availability.
    """
    if not auth_manager:
        return {"error": "AuthManager not initialized. Configure Client ID/Secret."}

    token = auth_manager.get_app_token()
    if not token:
        return {"error": "Failed to obtain application access token."}

    url = f"{KROGER_PRODUCTS_URL}/{product_id}" 
    params = {
        "filter.locationId": location_id
    }
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    try:
        print(f"Calling Kroger API: GET {url} with params {params}")
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status() 
        data = resp.json()
        
        product_data_container = data.get("data")
        if isinstance(product_data_container, list):
            if product_data_container:
                return product_data_container[0]
            else:
                return {"error": "Product data list is empty in API response.", "details": f"Product ID {product_id} at location {location_id} returned an empty data list."}
        elif isinstance(product_data_container, dict):
            return product_data_container
        elif isinstance(data, dict) and "productId" in data:
            return data
        else:
            print(f"Unexpected data structure in get_product response for {product_id} at {location_id}: {str(data)[:500]}")
            return {"error": "Unexpected response structure from API.", "details": f"Product ID {product_id}. Raw response (truncated): {str(data)[:200]}"}

    except requests.exceptions.HTTPError as http_err:
        # Refined error handling for get_product
        error_message_for_print = f"HTTP error occurred for get_product: {http_err}"
        error_response = {
            "error": "API request to Kroger for get_product failed.",
            "details": str(http_err)
        }
        if http_err.response is not None:
            error_response["status_code"] = http_err.response.status_code
            error_response["raw_response"] = http_err.response.text
            error_message_for_print += f" - Status Code: {http_err.response.status_code}, Response Body: {http_err.response.text}"
            try:
                error_json = http_err.response.json()
                if "errors" in error_json: 
                    error_response["details"] = error_json["errors"] 
                    error_response["kroger_error"] = True
            except ValueError: 
                pass 
        print(error_message_for_print)
        return error_response
    except requests.exceptions.Timeout:
        print(f"Request to Kroger API for get_product ({product_id}) timed out.")
        return {"error": "API request to Kroger for get_product timed out.", "details": "Timeout after 10 seconds"}
    except requests.exceptions.RequestException as req_err:
        print(f"Request exception occurred during get_product ({product_id}): {req_err}")
        return {"error": "Network request to Kroger for get_product failed.", "details": str(req_err)}
    except Exception as e: 
        print(f"An unexpected error occurred during get_product ({product_id}): {e}")
        return {"error": "An unexpected error occurred while getting product details.", "details": str(e)}

@tool(name="add_to_cart", description="Add a product to the user's Kroger cart (requires user authentication).")
def add_to_cart(product_id: str, quantity: int, location_id: str) -> dict:
    """
    Adds the specified product and quantity to the user's cart at the given store.
    Requires prior user authorization (OAuth2 Authorization Code Flow).
    Returns a confirmation message or error dictionary.
    """
    if not auth_manager:
        return {"error": "AuthManager not initialized. Configure Client ID/Secret."}

    token = auth_manager.get_user_token() 
    if not token:
        auth_url_message = ""
        if hasattr(auth_manager, 'generate_authorize_url') and KROGER_REDIRECT_URI:
            try:
                auth_url = auth_manager.generate_authorize_url(redirect_uri=KROGER_REDIRECT_URI)
                auth_url_message = f" Please authorize by visiting: {auth_url}"
            except Exception as e:
                print(f"Error generating auth URL: {e}") 
        return {
            "error": "User authentication required.",
            "message": "No user access token found. The user needs to authorize the application to access their cart." + auth_url_message,
            "action_needed": "User must complete OAuth2 authorization flow."
        }

    url = KROGER_CART_API_URL 
    payload = {
        "items": [{"productId": product_id, "quantity": quantity}],
        "locationId": location_id
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        print(f"Calling Kroger API: POST {url} with payload {payload}")
        resp = requests.post(url, headers=headers, json=payload, timeout=15)

        if resp.status_code == 401:
            auth_manager.user_access_token = None 
            auth_manager.user_refresh_token = None 
            return {
                "error": "User token expired or invalid.",
                "message": "The user access token is no longer valid. Please re-authorize the application.",
                "action_needed": "User must re-authenticate via OAuth2 authorization flow.",
                "status_code": 401 # Explicitly add status_code for 401
            }
        
        resp.raise_for_status()  

        if resp.status_code == 204: # Success, no content
            return {"success": True, "message": "Item(s) added to cart successfully."}
        
        try: # Success, with content
            response_data = resp.json()
            return {"success": True, "message": "Item(s) added to cart (response received).", "data": response_data}
        except ValueError: 
            return {"success": True, "message": "Item(s) added to cart (empty or non-JSON response).", "status_code": resp.status_code}

    except requests.exceptions.HTTPError as http_err:
        # Refined error handling for add_to_cart (for non-401 HTTP errors)
        error_message_for_print = f"HTTP error occurred for add_to_cart: {http_err}"
        error_response = {
            "error": "API request to Kroger for add_to_cart failed.",
            "details": str(http_err)
        }
        if http_err.response is not None:
            error_response["status_code"] = http_err.response.status_code
            raw_response_text = http_err.response.text 
            error_response["raw_response"] = raw_response_text
            error_message_for_print += f" - Status Code: {http_err.response.status_code}, Response Body: {raw_response_text}"
            try:
                error_json = http_err.response.json() 
                if "errors" in error_json: 
                    error_response["details"] = error_json["errors"] 
                    error_response["kroger_error"] = True
            except ValueError: 
                pass 
        print(error_message_for_print)
        return error_response
    except requests.exceptions.Timeout:
        print("Request to Kroger API for add_to_cart timed out.")
        return {"error": "API request to Kroger for add_to_cart timed out.", "details": "Timeout after 15 seconds"}
    except requests.exceptions.RequestException as req_err:
        print(f"Request exception occurred during add_to_cart: {req_err}")
        return {"error": "Network request to Kroger for add_to_cart failed.", "details": str(req_err)}
    except Exception as e:
        print(f"An unexpected error occurred during add_to_cart: {e}")
        return {"error": "An unexpected error occurred while adding to cart.", "details": str(e)}


if __name__ == '__main__':
    print("Executing tools.py directly for testing...")
    if not auth_manager:
        print("Skipping tool tests as AuthManager is not initialized (check KROGER_CLIENT_ID/SECRET in config.py).")
        print("To run these tests, replace 'YOUR_CLIENT_ID_HERE' and 'YOUR_CLIENT_SECRET_HERE' in config.py with actual credentials.")
    else:
        test_zip = "45202" 
        print(f"\n--- Test: find_stores (ZIP: {test_zip}) ---")
        stores_results = find_stores(zip_code=test_zip, limit=1) 
        
        test_location_id = None
        if isinstance(stores_results, dict) and "error" in stores_results:
            print(f"Error finding stores: {stores_results['error']}")
            if "details" in stores_results: print(f"Details: {stores_results['details']}")
            if "status_code" in stores_results: print(f"Status Code: {stores_results['status_code']}")
        elif stores_results: 
            print("Found stores:")
            for store in stores_results:
                store_name_parts = [store.get('chain'), store.get('name')]
                store_name = " - ".join(filter(None, store_name_parts))
                address_line = store.get('address', {}).get('addressLine1', 'N/A')
                print(f"  ID: {store.get('locationId', 'N/A')}, Name: {store_name}, Address: {address_line}")
                if not test_location_id: test_location_id = store.get('locationId')
        else:
             print("No stores found or empty result from find_stores.")

        test_product_id_from_search = None
        if test_location_id:
            print(f"\n--- Test: search_products (Query: milk, Location: {test_location_id}) ---")
            products_search_result = search_products(query="milk", location_id=test_location_id, limit=1) 
            
            if isinstance(products_search_result, dict) and "error" in products_search_result:
                print(f"Error searching products: {products_search_result['error']}")
                if "details" in products_search_result: print(f"Details: {products_search_result['details']}")
                if "status_code" in products_search_result: print(f"Status Code: {products_search_result['status_code']}")
            elif products_search_result: 
                print("Found products (from search):")
                for product_item in products_search_result: 
                    product_description = product_item.get('description', 'N/A')
                    current_product_id = product_item.get('productId', 'N/A')
                    if not test_product_id_from_search: test_product_id_from_search = current_product_id
                    
                    price_info = product_item.get('items', [{}])[0].get('price', {})
                    regular_price = price_info.get('regular', 'N/A')
                    promo_price = price_info.get('promo', 'N/A')
                    display_price = promo_price if promo_price not in [0, 'N/A', None] else regular_price
                    print(f"  ID: {current_product_id}, Name: {product_description}, Price: ${display_price}")
            else:
                print("No products found for 'milk' at this location from search, or empty result.")
        else:
            print("\nSkipping product search test as locationId was not found.")

        if test_product_id_from_search and test_location_id:
            print(f"\n--- Test: get_product (ID: {test_product_id_from_search}, Location: {test_location_id}) ---")
            product_details_result = get_product(product_id=test_product_id_from_search, location_id=test_location_id)
            
            if isinstance(product_details_result, dict) and "error" in product_details_result:
                print(f"Error getting product details: {product_details_result['error']}")
                if "details" in product_details_result: print(f"Details: {product_details_result['details']}")
                if "status_code" in product_details_result: print(f"Status Code: {product_details_result['status_code']}")
            elif product_details_result and product_details_result.get("productId"): 
                print("Found product details:")
                # (Full details printing omitted for brevity, it's extensive and unchanged from previous step)
                print(f"  ID: {product_details_result.get('productId', 'N/A')}, Name: {product_details_result.get('description', 'N/A')}")
            else:
                print(f"No product details found or empty/unexpected result for {test_product_id_from_search}.")
        else:
            print("\nSkipping get_product test as productId from search or locationId was not found.")

        print(f"\n--- Test: add_to_cart (Conceptual) ---")
        # Test for add_to_cart requires manual user auth, so this part remains conceptual in the test script
        if not auth_manager.get_user_token():
            print("  Skipping add_to_cart test: User token not available.")
            auth_url_message_test = ""
            if hasattr(auth_manager, 'generate_authorize_url') and KROGER_REDIRECT_URI:
                try:
                    auth_url_test = auth_manager.generate_authorize_url(redirect_uri=KROGER_REDIRECT_URI)
                    auth_url_message_test = f" To test this, first authenticate user by visiting: {auth_url_test}"
                except Exception as e:
                    print(f"  Error generating auth URL for test instructions: {e}")
            print(f" {auth_url_message_test}")
            print(f"  Then paste the authorization code into auth_manager.exchange_code_for_token(code, KROGER_REDIRECT_URI).")
            print(f"  Ensure KROGER_REDIRECT_URI ('{KROGER_REDIRECT_URI}') is registered in your Kroger Developer App.")
        
        elif test_product_id_from_search and test_location_id:
            print(f"  Attempting to add product {test_product_id_from_search} to cart at location {test_location_id} (requires valid user token).")
            cart_result = add_to_cart(product_id=test_product_id_from_search, quantity=1, location_id=test_location_id)
            print(f"  Add to cart result: {cart_result}")
            if isinstance(cart_result, dict) and cart_result.get("error"):
                 print(f"  Error adding to cart: {cart_result.get('error')}")
                 if "details" in cart_result: print(f"  Details: {cart_result['details']}")
                 if "status_code" in cart_result: print(f"  Status Code: {cart_result['status_code']}")
                 if cart_result.get("action_needed"): print(f"  Action Needed: {cart_result.get('action_needed')}")
            elif isinstance(cart_result, dict) and cart_result.get("success"):
                 print(f"  Success: {cart_result.get('message')}")
        else:
            print("  Skipping add_to_cart test: Missing product_id or location_id from previous tests, or user token not set up.")
