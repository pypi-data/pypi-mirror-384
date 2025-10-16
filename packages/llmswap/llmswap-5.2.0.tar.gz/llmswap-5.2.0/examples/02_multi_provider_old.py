#!/usr/bin/env python3
"""
Example 2: Multi-Provider Tool Calling

Demonstrates that the same tool works across all providers.
"""

from llmswap import LLMClient, Tool


def create_calculator():
    """Create calculator tool."""
    return Tool(
        name="calculate",
        description="Perform mathematical calculations",
        parameters={
            "expression": {
                "type": "string",
                "description": "Math expression (e.g., '2 + 2')"
            }
        },
        required=["expression"]
    )


def test_provider(provider_name: str, model: str = None):
    """Test tool calling with a specific provider."""
    print(f"\n{'='*60}")
    print(f"Testing: {provider_name.upper()}")
    print(f"{'='*60}")

    try:
        # Create client
        if model:
            client = LLMClient(provider=provider_name, model=model)
        else:
            client = LLMClient(provider=provider_name)

        calculator = create_calculator()

        # Ask a question
        query = "What is 15 * 27? Use the calculate tool."
        print(f"Query: {query}")

        response = client.chat(query, tools=[calculator])

        # Check for tool calls
        tool_calls = response.metadata.get('tool_calls', [])

        if tool_calls:
            tool_call = tool_calls[0]
            expression = tool_call.arguments.get('expression', '')
            result = eval(expression)

            print(f"✅ Tool called: {tool_call.name}")
            print(f"   Expression: {expression}")
            print(f"   Result: {result}")
            print(f"   Expected: 405")

            if result == 405:
                print(f"   Status: CORRECT ✓")
            else:
                print(f"   Status: INCORRECT ✗")

        else:
            print(f"❌ No tool call - direct response: {response.content}")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Test tool calling across multiple providers."""
    print("\n" + "="*60)
    print("Multi-Provider Tool Calling Demo")
    print("="*60)
    print("\nThis example demonstrates that the SAME tool definition")
    print("works across all LLM providers - no provider-specific code!")
    print("\nTesting calculation: 15 * 27 = 405")

    # Test each provider
    providers = [
        ("anthropic", None),
        ("openai", None),
        ("groq", "llama-3.3-70b-versatile"),
        ("gemini", None),
        ("xai", "grok-3"),
    ]

    for provider, model in providers:
        test_provider(provider, model)

    print(f"\n{'='*60}")
    print("Multi-Provider Test Complete!")
    print(f"{'='*60}")
    print("\n💡 Key Takeaway: Same Tool object works everywhere!")
    print("   Just change provider - no code changes needed.\n")


if __name__ == "__main__":
    main()
