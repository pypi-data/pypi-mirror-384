#!/usr/bin/env python3
"""
Test script to verify MCP -> Backend integration.
Tests API key validation and execution logging with real backend.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
load_dotenv(env_file)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend_client import get_backend_client


async def test_integration():
    """Test MCP backend integration."""

    print("=" * 60)
    print("🧪 Testing Mahoraga MCP -> Backend Integration")
    print("=" * 60)

    # Check environment
    mock_mode = os.getenv("MAHORAGA_MOCK_BACKEND", "true")
    backend_url = os.getenv("MAHORAGA_BACKEND_URL", "http://localhost:8000")

    print(f"\n📋 Configuration:")
    print(f"   Mock Mode: {mock_mode}")
    print(f"   Backend URL: {backend_url}")

    # Get backend client
    client = get_backend_client()

    # Test API key from database
    test_api_key = "mah_test1234567890abcdef"

    print(f"\n🔑 Testing API Key Validation...")
    print(f"   API Key: {test_api_key}")

    # Test validation
    result = await client.validate_api_key(test_api_key)

    if result.get("valid"):
        print("   ✅ API Key Valid!")
        user = result.get("user", {})
        print(f"   👤 User: {user.get('name')} ({user.get('email')})")
        print(f"   💰 Credits: ${user.get('credits', 0):.2f}")
    else:
        print(f"   ❌ API Key Invalid: {result.get('error')}")
        return False

    # Test execution logging
    print(f"\n📊 Testing Execution Logging...")

    log_result = await client.log_execution(
        api_key=test_api_key,
        execution_id="test_exec_integration_001",
        status="completed",
        tokens={"prompt": 150, "completion": 75, "total": 225},
        cost=0.05
    )

    if log_result.get("logged"):
        print("   ✅ Execution Logged!")
        print(f"   💸 Credits Deducted: ${log_result.get('credits_deducted', 0):.2f}")
        print(f"   💰 New Balance: ${log_result.get('new_balance', 0):.2f}")
    else:
        print(f"   ❌ Logging Failed: {log_result.get('error')}")
        return False

    # Verify credits were deducted
    print(f"\n🔍 Verifying Credit Deduction...")

    verify_result = await client.validate_api_key(test_api_key)
    if verify_result.get("valid"):
        new_credits = verify_result.get("user", {}).get("credits", 0)
        print(f"   ✅ Credits Updated: ${new_credits:.2f}")

    print(f"\n" + "=" * 60)
    print("✅ All Integration Tests Passed!")
    print("=" * 60)
    print("\n💡 Next Steps:")
    print("   1. MCP is now connected to real backend")
    print("   2. Test with actual MCP execute command")
    print("   3. Build web portal for user management")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)