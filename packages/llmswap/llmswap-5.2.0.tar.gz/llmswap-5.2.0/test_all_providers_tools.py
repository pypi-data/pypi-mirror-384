#!/usr/bin/env python3
"""
Test tool calling with all main providers.
Tests: Anthropic, OpenAI, Groq, Gemini, XAI
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from llmswap import LLMClient, Tool


def create_calculator_tool():
    """Create calculator tool for testing."""
    return Tool(
        name="calculate",
        description="Perform mathematical calculations",
        parameters={
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
            }
        },
        required=["expression"]
    )


def execute_tool_call(tool_call):
    """Execute a tool call and return the result."""
    if tool_call.name == "calculate":
        expression = tool_call.arguments.get("expression", "")
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    return "Unknown tool"


def test_gemini():
    """Test Gemini tool calling."""
    print("\n" + "="*60)
    print("Testing Gemini (Google)")
    print("="*60)

    try:
        client = LLMClient(provider="gemini")
        calculator = create_calculator_tool()

        # Initial request
        response = client.chat(
            "What is 111 multiplied by 222? Use the calculate tool.",
            tools=[calculator]
        )

        print(f"\n1. Initial Response:")
        print(f"   Content: {response.content}")

        # Check for tool calls in metadata
        tool_calls = response.metadata.get('tool_calls', [])
        if not tool_calls:
            print("   ERROR: No tool calls found!")
            return False

        print(f"   Tool Calls: {len(tool_calls)}")

        # Execute tool
        tool_call = tool_calls[0]
        print(f"\n2. Tool Call:")
        print(f"   Name: {tool_call.name}")
        print(f"   Arguments: {tool_call.arguments}")

        result = execute_tool_call(tool_call)
        print(f"\n3. Tool Result: {result}")

        # Validate answer (111 * 222 = 24642)
        if "24642" in result or result == "24642":
            print(f"\n✅ GEMINI TEST PASSED - Correct answer: {result}")
            return True
        else:
            print(f"\n❌ GEMINI TEST FAILED - Expected 24642, got: {result}")
            return False

    except Exception as e:
        print(f"\n❌ GEMINI TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_xai():
    """Test XAI (Grok) tool calling."""
    print("\n" + "="*60)
    print("Testing XAI (Grok)")
    print("="*60)

    try:
        client = LLMClient(provider="xai", model="grok-3")
        calculator = create_calculator_tool()

        # Initial request
        response = client.chat(
            "What is 333 multiplied by 444? Use the calculate tool.",
            tools=[calculator]
        )

        print(f"\n1. Initial Response:")
        print(f"   Content: {response.content}")

        # Check for tool calls in metadata
        tool_calls = response.metadata.get('tool_calls', [])
        if not tool_calls:
            print("   ERROR: No tool calls found!")
            return False

        print(f"   Tool Calls: {len(tool_calls)}")

        # Execute tool
        tool_call = tool_calls[0]
        print(f"\n2. Tool Call:")
        print(f"   Name: {tool_call.name}")
        print(f"   Arguments: {tool_call.arguments}")

        result = execute_tool_call(tool_call)
        print(f"\n3. Tool Result: {result}")

        # Send result back (XAI uses OpenAI format)
        import json
        messages = [
            {"role": "user", "content": "What is 333 multiplied by 444? Use the calculate tool."},
            {"role": "assistant", "content": response.content, "tool_calls": [
                {"id": tool_call.id, "type": "function", "function": {"name": tool_call.name, "arguments": json.dumps(tool_call.arguments)}}
            ]},
            {"role": "tool", "tool_call_id": tool_call.id, "content": result}
        ]

        final_response = client.chat(messages, tools=[calculator])
        print(f"\n4. Final Response: {final_response.content}")

        # Validate answer (333 * 444 = 147852)
        if "147852" in final_response.content or "147,852" in final_response.content:
            print("\n✅ XAI TEST PASSED - Correct answer!")
            return True
        else:
            print(f"\n❌ XAI TEST FAILED - Expected 147852, got: {final_response.content}")
            return False

    except Exception as e:
        print(f"\n❌ XAI TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("All Providers Tool Calling Tests")
    print("="*60)

    results = {
        "gemini": False,
        "xai": False,
    }

    try:
        results["gemini"] = test_gemini()
    except Exception as e:
        print(f"\n❌ GEMINI TEST ERROR: {e}")

    try:
        results["xai"] = test_xai()
    except Exception as e:
        print(f"\n❌ XAI TEST ERROR: {e}")

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for provider, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{provider.upper()}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)
