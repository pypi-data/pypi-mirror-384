"""
Debug example for the NetInt Agents SDK.

This example demonstrates how to enable debug logging to see
request headers, body, and response details.
"""

from netint_agents_sdk import NetIntClient, NetIntConfig
from netint_agents_sdk.models import TaskCreate


def main():
    print("=" * 80)
    print("NetInt Agents SDK - Debug Example")
    print("=" * 80)
    print("\nThis example shows how to enable debug logging to inspect")
    print("HTTP requests and responses.\n")

    # Method 1: Enable debug in configuration
    print("🔍 Method 1: Enable debug in NetIntConfig\n")
    config = NetIntConfig(
        base_url="http://localhost:8888/backend",
        api_token="svc_your_token_here",  # Replace with your token
        debug=True,  # Enable debug logging
    )
    client = NetIntClient(config)

    try:
        # This will print detailed request/response information
        print("Listing environments with debug enabled:")
        environments = client.environments.list()
        print(f"\n✓ Found {len(environments)} environments")

        # Create a task (will show POST request details)
        if environments:
            print("\n\nCreating a task with debug enabled:")
            task = client.tasks.create(
                TaskCreate(
                    title="Debug Test Task",
                    description="Testing debug output",
                    environment_id=environments[0].id,
                )
            )
            print(f"\n✓ Task created: {task.id}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        client.close()

    # Method 2: Enable debug via environment variable
    print("\n\n" + "=" * 80)
    print("🔍 Method 2: Enable debug via environment variable")
    print("=" * 80)
    print("\nSet NETINT_DEBUG=true in your environment:")
    print("  export NETINT_DEBUG=true")
    print("  export NETINT_API_TOKEN=your_token")
    print("  python examples/debug_example.py")

    # Method 3: Debug specific requests
    print("\n\n" + "=" * 80)
    print("📝 What Debug Output Shows")
    print("=" * 80)
    print("""
When debug=True, you'll see:

🔵 REQUEST: Shows every HTTP request
   - HTTP method and full URL
   - All request headers (sensitive data masked)
   - Request body (formatted JSON)

🟢 RESPONSE: Shows every HTTP response
   - Status code and reason
   - Response headers
   - Response body (formatted JSON)

This helps you:
   ✓ Debug API integration issues
   ✓ Verify request payloads
   ✓ Inspect response data
   ✓ Troubleshoot authentication
   ✓ Monitor API behavior
    """)


if __name__ == "__main__":
    main()
