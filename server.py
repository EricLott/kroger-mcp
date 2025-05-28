from mcp import Server, stdio_server
# Assuming the mcp library is installed and provides these.
# If the library structure is different (e.g., mcp.server.Server), imports might need adjustment.

# Import the tools individually
from tools import find_stores, search_products, get_product, add_to_cart
# Import config to access KROGER_CLIENT_ID/SECRET for a check.
from config import KROGER_CLIENT_ID, KROGER_CLIENT_SECRET

# Note: The tools.py file initializes a global 'auth_manager'.
# If 'auth_manager' needed to be explicitly passed or if tools didn't rely on a global one,
# we might need to import it here and pass it during tool registration or server initialization.
# from tools import auth_manager # Example if it were needed

def run_server():
    # Check if essential configuration is present
    if not KROGER_CLIENT_ID or KROGER_CLIENT_ID == "YOUR_CLIENT_ID_HERE" or \
       not KROGER_CLIENT_SECRET or KROGER_CLIENT_SECRET == "YOUR_CLIENT_SECRET_HERE":
        print("ERROR: Kroger Client ID or Secret is not configured in config.py.")
        print("Please set KROGER_CLIENT_ID and KROGER_CLIENT_SECRET before running the server.")
        # In a real scenario, you might exit with a non-zero code:
        # import sys
        # sys.exit(1)
        return # Do not start the server if not configured

    print("Initializing Kroger MCP Server...")
    # Name and version for the server as per MCP guidelines
    kroger_mcp_server = Server(name="kroger-mcp-server", version="1.0.0")

    # Register the tools
    # Assuming an add_tool method on the Server instance as per the plan.
    # The @tool decorator in tools.py should have attached necessary metadata (name, description)
    # to the tool functions themselves, which add_tool will use.
    
    print("Registering tools...")
    kroger_mcp_server.add_tool(find_stores)
    kroger_mcp_server.add_tool(search_products)
    kroger_mcp_server.add_tool(get_product)
    kroger_mcp_server.add_tool(add_to_cart)
    # If more tools like view_cart, get_profile were implemented, they'd be added here.

    print("Kroger MCP Server initialized with the following tools:")
    # Assuming server.tools lists registered tool names or objects with a 'name' attribute
    # This part depends on the actual implementation of mcp.Server
    if hasattr(kroger_mcp_server, 'tools') and isinstance(kroger_mcp_server.tools, dict):
        for tool_name in kroger_mcp_server.tools.keys(): # If tools is a dict name:function
            print(f"- {tool_name}")
    elif hasattr(kroger_mcp_server, 'get_tool_names'): # Or if there's a method
         for tool_name in kroger_mcp_server.get_tool_names():
            print(f"- {tool_name}")
    else:
        # Fallback if we don't know how to list tools, list from what we tried to add
        print("- find_stores (assumed registered)")
        print("- search_products (assumed registered)")
        print("- get_product (assumed registered)")
        print("- add_to_cart (assumed registered)")
    
    print("\nStarting MCP server with STDIO transport...")
    print("Server is now listening for JSON-RPC requests on stdin/stdout.")
    print("Ensure MCP client (e.g., Claude Desktop) is configured to launch this script.")
    print("Press Ctrl+C to stop the server.")

    # Start the server using STDIO transport
    try:
        with stdio_server() as (input_stream, output_stream):
            kroger_mcp_server.run(input_stream, output_stream)
    except KeyboardInterrupt:
        print("\nServer stopped by user (Ctrl+C).")
    except ImportError as e:
        print(f"ImportError during server run: {e}. This might indicate the 'mcp' library is not installed or not found.")
        print("Please ensure 'mcp' is installed in your Python environment.")
    except Exception as e:
        # Log the full traceback for debugging if possible
        import traceback
        print(f"An unexpected error occurred while running the server: {e}")
        traceback.print_exc()
    finally:
        print("Kroger MCP Server has shut down.")

if __name__ == '__main__':
    run_server()
