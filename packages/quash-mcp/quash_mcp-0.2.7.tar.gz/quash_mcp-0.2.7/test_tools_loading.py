"""
Test script to verify tool functions are loaded correctly.
"""

import sys
sys.path.insert(0, '/Users/abhinavsai/POC/mahoraga-mac/quash-mcp')
sys.path.insert(0, '/Users/abhinavsai/POC/mahoraga-mac/mahoraga')

def test_tool_loading():
    print("Testing tool loading...")

    try:
        # Import mahoraga components
        from mahoraga.tools import Tools, describe_tools
        from mahoraga.tools.adb import AdbTools as MahoragaAdbTools
        from mahoraga.agent.context.personas import DEFAULT
        from mahoraga.agent.utils.async_utils import async_to_sync

        print("✅ All imports successful")

        # Create a mahoraga AdbTools instance
        print("\nCreating mahoraga AdbTools instance...")
        mahoraga_tools = MahoragaAdbTools(
            serial="emulator-5554",  # Use your device serial
            use_tcp=True,
            remote_tcp_port=8080
        )
        print(f"✅ Created mahoraga AdbTools instance")
        print(f"   - Serial: {mahoraga_tools.device.serial}")
        print(f"   - TCP forwarded: {mahoraga_tools.tcp_forwarded}")

        # Get tool list
        print("\nGetting tool list...")
        tool_list = describe_tools(mahoraga_tools, exclude_tools=None)
        print(f"✅ Got {len(tool_list)} tools:")
        for tool_name, tool_func in tool_list.items():
            print(f"   - {tool_name}: {tool_func}")

        # Filter by allowed tools
        print(f"\nFiltering by DEFAULT persona allowed tools...")
        allowed_tool_names = DEFAULT.allowed_tools
        print(f"   Allowed tools: {allowed_tool_names}")

        filtered_tools = {name: func for name, func in tool_list.items() if name in allowed_tool_names}
        print(f"✅ Filtered to {len(filtered_tools)} tools:")
        for tool_name in filtered_tools.keys():
            print(f"   - {tool_name}")

        # Test executor globals setup
        print("\nSetting up executor globals...")
        executor_globals = {"__builtins__": __builtins__}

        for tool_name, tool_function in filtered_tools.items():
            import asyncio
            if asyncio.iscoroutinefunction(tool_function):
                tool_function = async_to_sync(tool_function)
            executor_globals[tool_name] = tool_function

        print(f"✅ Executor globals set up with {len(executor_globals)} items")

        # Test that functions are callable
        print("\nTesting function availability...")
        test_functions = ['start_app', 'swipe', 'press_key', 'tap_by_index']
        for func_name in test_functions:
            if func_name in executor_globals:
                print(f"   ✅ {func_name} is available")
            else:
                print(f"   ❌ {func_name} is NOT available")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tool_loading()
    sys.exit(0 if success else 1)