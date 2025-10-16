#!/usr/bin/env python3
"""
Test tool calling with production llmswap across all providers.
Tests Anthropic, OpenAI, and Groq with real API calls.
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


def test_anthropic():
    """Test Anthropic tool calling."""
    print("\n" + "="*60)
    print("Testing Anthropic (Claude)")
    print("="*60)

    client = LLMClient(provider="anthropic")
    calculator = create_calculator_tool()

    # Initial request
    response = client.chat(
        "What is 123 multiplied by 456? Use the calculate tool.",
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

    # Send result back
    # Build assistant content - only include text block if content is not empty
    assistant_content = []
    if response.content and response.content.strip():
        assistant_content.append({"type": "text", "text": response.content})
    assistant_content.append({"type": "tool_use", "id": tool_call.id, "name": tool_call.name, "input": tool_call.arguments})

    messages = [
        {"role": "user", "content": "What is 123 multiplied by 456? Use the calculate tool."},
        {"role": "assistant", "content": assistant_content},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tool_call.id, "content": result}
        ]}
    ]

    final_response = client.chat(messages, tools=[calculator])
    print(f"\n4. Final Response: {final_response.content}")

    # Validate answer
    if "56088" in final_response.content or "56,088" in final_response.content:
        print("\n✅ ANTHROPIC TEST PASSED - Correct answer!")
        return True
    else:
        print(f"\n❌ ANTHROPIC TEST FAILED - Expected 56088, got: {final_response.content}")
        return False


def test_openai():
    """Test OpenAI tool calling."""
    print("\n" + "="*60)
    print("Testing OpenAI (GPT)")
    print("="*60)

    client = LLMClient(provider="openai")
    calculator = create_calculator_tool()

    # Initial request
    response = client.chat(
        "What is 789 multiplied by 654? Use the calculate tool.",
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

    # Send result back
    messages = [
        {"role": "user", "content": "What is 789 multiplied by 654? Use the calculate tool."},
        {"role": "assistant", "content": response.content, "tool_calls": [
            {"id": tool_call.id, "type": "function", "function": {"name": tool_call.name, "arguments": str(tool_call.arguments)}}
        ]},
        {"role": "tool", "tool_call_id": tool_call.id, "content": result}
    ]

    final_response = client.chat(messages, tools=[calculator])
    print(f"\n4. Final Response: {final_response.content}")

    # Validate answer
    if "516006" in final_response.content or "516,006" in final_response.content:
        print("\n✅ OPENAI TEST PASSED - Correct answer!")
        return True
    else:
        print(f"\n❌ OPENAI TEST FAILED - Expected 516006, got: {final_response.content}")
        return False


def test_groq():
    """Test Groq tool calling."""
    print("\n" + "="*60)
    print("Testing Groq (Llama)")
    print("="*60)

    client = LLMClient(provider="groq", model="llama-3.3-70b-versatile")
    calculator = create_calculator_tool()

    # Initial request
    response = client.chat(
        "What is 987 multiplied by 321? Use the calculate tool.",
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

    # Send result back (Groq uses OpenAI format)
    messages = [
        {"role": "user", "content": "What is 987 multiplied by 321? Use the calculate tool."},
        {"role": "assistant", "content": response.content, "tool_calls": [
            {"id": tool_call.id, "type": "function", "function": {"name": tool_call.name, "arguments": str(tool_call.arguments)}}
        ]},
        {"role": "tool", "tool_call_id": tool_call.id, "content": result}
    ]

    final_response = client.chat(messages, tools=[calculator])
    print(f"\n4. Final Response: {final_response.content}")

    # Validate answer
    if "316827" in final_response.content or "316,827" in final_response.content:
        print("\n✅ GROQ TEST PASSED - Correct answer!")
        return True
    else:
        print(f"\n❌ GROQ TEST FAILED - Expected 316827, got: {final_response.content}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Production llmswap Tool Calling Tests")
    print("="*60)

    results = {
        "anthropic": False,
        "openai": False,
        "groq": False
    }

    try:
        results["anthropic"] = test_anthropic()
    except Exception as e:
        print(f"\n❌ ANTHROPIC TEST ERROR: {e}")

    try:
        results["openai"] = test_openai()
    except Exception as e:
        print(f"\n❌ OPENAI TEST ERROR: {e}")

    try:
        results["groq"] = test_groq()
    except Exception as e:
        print(f"\n❌ GROQ TEST ERROR: {e}")

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
