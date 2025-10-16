#!/usr/bin/env python3
"""
Test backward compatibility - ensure all existing features still work.
Tests v1.0-v5.1.9 features without tool calling.
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from llmswap import LLMClient


def test_basic_query():
    """Test basic query method (v1.0 feature)."""
    print("\n" + "="*60)
    print("Test 1: Basic Query (v1.0)")
    print("="*60)

    try:
        client = LLMClient(provider="anthropic")
        response = client.query("Say 'hello'")

        if response.content and len(response.content) > 0:
            print(f"✅ Basic query works: {response.content[:50]}...")
            return True
        else:
            print(f"❌ Basic query failed: empty response")
            return False
    except Exception as e:
        print(f"❌ Basic query failed: {e}")
        return False


def test_chat_without_tools():
    """Test chat method without tools (v3.0 feature)."""
    print("\n" + "="*60)
    print("Test 2: Chat Without Tools (v3.0)")
    print("="*60)

    try:
        client = LLMClient(provider="openai")

        # Single message as string
        response = client.chat("What is 2 + 2?")

        if response.content and "4" in response.content:
            print(f"✅ Chat without tools works: {response.content[:50]}...")
            return True
        else:
            print(f"❌ Chat without tools failed: {response.content}")
            return False
    except Exception as e:
        print(f"❌ Chat without tools failed: {e}")
        return False


def test_conversation_history():
    """Test conversation with message history (v3.0 feature)."""
    print("\n" + "="*60)
    print("Test 3: Conversation History (v3.0)")
    print("="*60)

    try:
        client = LLMClient(provider="anthropic")

        # Multi-turn conversation
        messages = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
            {"role": "user", "content": "What is my name?"}
        ]

        response = client.chat(messages)

        if response.content and "Alice" in response.content:
            print(f"✅ Conversation history works: {response.content[:50]}...")
            return True
        else:
            print(f"❌ Conversation history failed: {response.content}")
            return False
    except Exception as e:
        print(f"❌ Conversation history failed: {e}")
        return False


def test_provider_switching():
    """Test provider switching (v2.0 feature)."""
    print("\n" + "="*60)
    print("Test 4: Provider Switching (v2.0)")
    print("="*60)

    try:
        client = LLMClient(provider="anthropic")

        # Test with first provider
        response1 = client.query("Say 'test1'")
        provider1 = response1.provider

        # Switch provider
        client.set_provider("openai")

        # Test with second provider
        response2 = client.query("Say 'test2'")
        provider2 = response2.provider

        if provider1 == "anthropic" and provider2 == "openai":
            print(f"✅ Provider switching works: {provider1} -> {provider2}")
            return True
        else:
            print(f"❌ Provider switching failed: {provider1} -> {provider2}")
            return False
    except Exception as e:
        print(f"❌ Provider switching failed: {e}")
        return False


def test_response_metadata():
    """Test response metadata (v4.0 feature)."""
    print("\n" + "="*60)
    print("Test 5: Response Metadata (v4.0)")
    print("="*60)

    try:
        client = LLMClient(provider="groq")
        response = client.query("Say 'hello'")

        # Check for expected metadata fields
        has_provider = response.provider is not None
        has_model = response.model is not None
        has_latency = response.latency is not None
        has_usage = response.usage is not None
        has_metadata = response.metadata is not None

        if all([has_provider, has_model, has_latency, has_usage, has_metadata]):
            print(f"✅ Response metadata works:")
            print(f"   Provider: {response.provider}")
            print(f"   Model: {response.model}")
            print(f"   Latency: {response.latency:.3f}s")
            print(f"   Usage: {response.usage}")
            return True
        else:
            print(f"❌ Response metadata incomplete:")
            print(f"   Provider: {has_provider}")
            print(f"   Model: {has_model}")
            print(f"   Latency: {has_latency}")
            print(f"   Usage: {has_usage}")
            print(f"   Metadata: {has_metadata}")
            return False
    except Exception as e:
        print(f"❌ Response metadata failed: {e}")
        return False


def test_multiple_providers():
    """Test multiple providers work (v1.0-v5.0 feature)."""
    print("\n" + "="*60)
    print("Test 6: Multiple Providers (v1.0-v5.0)")
    print("="*60)

    providers_to_test = ["anthropic", "openai", "groq"]
    results = {}

    for provider in providers_to_test:
        try:
            client = LLMClient(provider=provider)
            response = client.query("Say 'hi'")
            results[provider] = response.content is not None and len(response.content) > 0
        except Exception as e:
            print(f"   {provider}: ❌ {e}")
            results[provider] = False

    all_passed = all(results.values())

    if all_passed:
        print(f"✅ All providers work:")
        for provider, passed in results.items():
            print(f"   {provider}: ✅")
        return True
    else:
        print(f"❌ Some providers failed:")
        for provider, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"   {provider}: {status}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Backward Compatibility Tests")
    print("Testing v1.0-v5.1.9 features without tool calling")
    print("="*60)

    tests = [
        ("Basic Query", test_basic_query),
        ("Chat Without Tools", test_chat_without_tools),
        ("Conversation History", test_conversation_history),
        ("Provider Switching", test_provider_switching),
        ("Response Metadata", test_response_metadata),
        ("Multiple Providers", test_multiple_providers),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} ERROR: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*60)
    print("Backward Compatibility Test Summary")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL BACKWARD COMPATIBILITY TESTS PASSED!")
        print("✅ No existing features were broken")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("❌ Some existing features may be broken")
        sys.exit(1)
