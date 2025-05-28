# Kroger MCP Server

This project implements a Model Context Protocol (MCP) server that wraps the Kroger API. It allows Large Language Models (LLMs) like Anthropic's Claude to interact with Kroger's grocery services, enabling features such as product search, store lookup, and cart management.

## Features

*   **OAuth2 Authentication**: Handles client credentials for general data and user-based authorization for cart operations.
*   **Product Search**: Search for products by keyword at specific store locations.
*   **Product Details**: Retrieve detailed product information including price, availability, and fulfillment options.
*   **Store Locations**: Find Kroger store locations by ZIP code.
*   **Cart Management**: Add items to a user's Kroger shopping cart (requires user authorization).

## 1. Configuration

Before running the server, you need to configure your Kroger API credentials and OAuth2 settings.

### 1.1. API Credentials (Client ID & Secret)

1.  **Obtain Credentials**: Register an application on the [Kroger Developer Portal](https://developer.kroger.com/) to get a `Client ID` and `Client Secret`.
2.  **Set Credentials**: You can set these credentials in one of two ways:
    *   **`config.py` (Recommended for simplicity for local use)**:
        Open the `config.py` file and replace the placeholder values for `KROGER_CLIENT_ID` and `KROGER_CLIENT_SECRET` with your actual credentials.
        ```python
        # config.py
        KROGER_CLIENT_ID = "YOUR_ACTUAL_CLIENT_ID"
        KROGER_CLIENT_SECRET = "YOUR_ACTUAL_CLIENT_SECRET"
        ```
    *   **Environment Variables**: The `auth.py` script can be modified to also read `os.environ.get("KROGER_CLIENT_ID")` and `os.environ.get("KROGER_CLIENT_SECRET")` if you prefer managing secrets via environment variables. (Note: Current implementation in `tools.py` and `server.py` directly uses `config.py` values).

### 1.2. User Authorization (for Cart Operations)

To use tools that modify a user's cart (e.g., `add_to_cart`), the user must authorize the application. This server uses the OAuth2 Authorization Code Grant flow.

1.  **Redirect URI**: Ensure the `KROGER_REDIRECT_URI` in `config.py` matches the Redirect URI registered with your Kroger application. For local testing, `http://localhost:8080/callback` is a common default, but you'll need a way to capture the code from this redirect.
    ```python
    # config.py
    KROGER_REDIRECT_URI = "http://localhost:8080/callback" # Or your configured URI
    ```

2.  **Obtaining an Authorization Code & Refresh Token**:
    *   Run the `auth.py` script directly (`python auth.py`).
    *   It will print an "Authorization URL". Copy and paste this URL into your web browser.
    *   Log in with your Kroger account and grant access.
    *   You will be redirected to your `KROGER_REDIRECT_URI`. The URL in your browser's address bar will now contain an authorization `code` (e.g., `http://localhost:8080/callback?code=YOUR_AUTH_CODE&...`).
    *   Copy this `code`.
    *   Paste the `code` back into the `auth.py` script when prompted.
    *   The script will then exchange the code for an access token and a **refresh token**.
    *   **Crucially, securely store the displayed `refresh_token`**.

3.  **Configuring the Refresh Token**:
    *   To enable cart operations across server restarts without re-authenticating each time, you should set the obtained `refresh_token` in `config.py` or as an environment variable that `AuthManager` can load.
    *   Modify `AuthManager.__init__` in `auth.py` to load this `KROGER_USER_REFRESH_TOKEN` from `config.py` or environment:
        ```python
        # In auth.py -> AuthManager.__init__
        # self.user_refresh_token = os.environ.get("KROGER_USER_REFRESH_TOKEN") 
        # OR
        # from config import KROGER_USER_REFRESH_TOKEN # Add this to config.py
        # self.user_refresh_token = KROGER_USER_REFRESH_TOKEN 
        ```
        And then add `KROGER_USER_REFRESH_TOKEN = "YOUR_SAVED_REFRESH_TOKEN"` to `config.py`.
    *   When `get_user_token()` is called, if an access token is expired or missing, it will attempt to use this refresh token.

## 2. Running the Server

1.  **Install Dependencies**: If you haven't already, install the required Python libraries:
    ```bash
    pip install requests mcp
    ```
    (Note: The `mcp` library name is assumed; adjust if it's different, e.g., `modelcontextprotocol`).
2.  **Start the Server**:
    Run the `server.py` script from your terminal:
    ```bash
    python server.py
    ```
3.  **Server Operation**:
    *   The server uses **STDIO (standard input/output)** for communication with the MCP client. It does not open any network ports.
    *   Upon starting, it will print initialization messages, including a list of registered tools.
    *   It will then listen for JSON-RPC requests from the MCP client.
4.  **Stopping the Server**:
    Press `Ctrl+C` in the terminal where the server is running.

## 3. MCP Client Integration

### 3.1. Claude Desktop

*   Go to `Settings` in Claude Desktop.
*   Navigate to `Integrations` (or a similar section for MCP servers).
*   Click `Add MCP Server` (or equivalent).
*   Provide the command to run the server. This usually involves specifying the Python interpreter and the path to `server.py`. For example:
    *   If Python is in your PATH: `python /path/to/your/project/server.py`
    *   Otherwise: `/path/to/your/python /path/to/your/project/server.py`
*   Once added, Claude will be able to see and invoke the Kroger tools (e.g., `find_stores`, `search_products`).

### 3.2. Programmatic Use (Example)

Developers can also interact with the server programmatically using an MCP client library.

```python
# This is a conceptual example based on the MCP specification.
# The actual library might differ.
from modelcontext import Client, StdioClientTransport # Assuming library structure

async def main():
    client = Client(name="example-kroger-client", version="1.0", capabilities={})
    
    # Adjust command if python/server.py are not in PATH or need full paths
    python_executable = "python" # Or full path to python interpreter
    server_script_path = "server.py" # Or full path to server.py
    
    transport = StdioClientTransport(command=[python_executable, server_script_path])
    
    await client.connect(transport)
    
    # Example: Find stores
    try:
        store_results = await client.call_tool(
            "find_stores", 
            {"zip_code": "45202", "limit": 1}
        )
        print("Store Search Results:", store_results)

        if store_results and not store_results.get("error") and len(store_results) > 0:
            location_id = store_results[0].get("locationId")
            if location_id:
                # Example: Search products
                product_results = await client.call_tool(
                    "search_products",
                    {"query": "milk", "location_id": location_id, "limit": 2}
                )
                print("Product Search Results:", product_results)
                
                # Example: Add to cart (requires user auth token to be set up in server)
                # Ensure product_results[0] exists and has 'productId'
                if product_results and not product_results.get("error") and len(product_results) > 0:
                    product_id = product_results[0].get("productId")
                    cart_result = await client.call_tool(
                        "add_to_cart",
                        {"product_id": product_id, "quantity": 1, "location_id": location_id}
                    )
                    print("Add to Cart Result:", cart_result)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    # For asyncio if your client library uses it
    # import asyncio
    # asyncio.run(main())
    print("Run the async main() function with an asyncio event loop if needed by your MCP client library.")
```

## 4. Example Dialogue with LLM

**User**: "I need two gallons of organic whole milk and a dozen eggs from a Kroger near 90210."

**LLM (Assistant) Internal Steps**:
1.  *(Optional: LLM asks for user's ZIP code if not provided or ambiguous)*
2.  **LLM calls `find_stores`**: `{"zip_code": "90210", "limit": 1}`
    *   Server returns store details, e.g., `[{ "locationId": "01400123", "name": "Beverly Hills Kroger", ... }]`
3.  **LLM calls `search_products` (for milk)**: `{"query": "organic whole milk", "location_id": "01400123", "limit": 5}`
    *   Server returns list of milk products. LLM selects one, e.g., `{"productId": "0001111060404", "description": "Simple Truth Organic Milk...", ...}`.
4.  **LLM calls `search_products` (for eggs)**: `{"query": "dozen eggs", "location_id": "01400123", "limit": 3}`
    *   Server returns list of egg products. LLM selects one.
5.  *(User authorization for cart must be completed if not done already)*
6.  **LLM calls `add_to_cart` (for milk)**: `{"product_id": "0001111060404", "quantity": 2, "location_id": "01400123"}`
    *   Server confirms addition.
7.  **LLM calls `add_to_cart` (for eggs)**: `{"product_id": "...", "quantity": 1, "location_id": "01400123"}`
    *   Server confirms addition.

**LLM (Assistant) to User**: "Okay, I've found the Beverly Hills Kroger. I've added 2 gallons of Simple Truth Organic Whole Milk and one dozen eggs to your cart. Anything else?"

## 5. Error Scenarios

*   **Missing User Authorization**: If you attempt to use `add_to_cart` without the user having authorized the application, the tool will return an error:
    ```json
    {
      "error": "User authentication required.",
      "message": "No user access token found. The user needs to authorize the application...",
      "action_needed": "User must complete OAuth2 authorization flow." 
    }
    ```
    The LLM should guide the user to perform the authorization step (see Section 1.2). The authorization URL might be included in the error message.
*   **Invalid/Expired Tokens**: If an access token is expired, the `AuthManager` will attempt to refresh it. If the refresh token is also invalid (e.g., for user tokens after a 401 error on `add_to_cart`), re-authorization will be required.
*   **API Rate Limits**: Kroger's API has rate limits (e.g., see [developer.kroger.com/support/rate-limits/](https://developer.kroger.com/support/rate-limits/)). If the server hits these limits, API calls will fail. The server will return an error from Kroger, typically with an HTTP 429 status code. The LLM should inform the user to try again later.
*   **Other API Errors**: If Kroger's API returns other errors (e.g., invalid product ID, store not found for locationId), the tools will return a JSON dictionary containing `error`, `details`, `status_code` (the HTTP status from Kroger), and possibly `raw_response` or `kroger_error` fields.

## 6. Available Tools

The server exposes the following tools to the LLM:

*   **`find_stores(zip_code: str, radius_miles: int = 10, limit: int = 5) -> list | dict`**
    *   Description: Find Kroger store locations by ZIP code (returns nearest stores with IDs).
*   **`search_products(query: str, location_id: str, limit: int = 10) -> list | dict`**
    *   Description: Search Kroger products by keyword at a given store.
*   **`get_product(product_id: str, location_id: str) -> dict`**
    *   Description: Get detailed information for a product by ID (price, size, stock, fulfillment options).
*   **`add_to_cart(product_id: str, quantity: int, location_id: str) -> dict`**
    *   Description: Add a product to the user's Kroger cart (requires user authentication).

(The descriptions above are based on the `@tool` decorators in `tools.py`.)
