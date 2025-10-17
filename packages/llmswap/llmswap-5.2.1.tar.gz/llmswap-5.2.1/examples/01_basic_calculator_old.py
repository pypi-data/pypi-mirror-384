#!/usr/bin/env python3
"""
Example 1: Basic Calculator

Demonstrates basic tool calling with a simple calculator function.
"""

from llmswap import LLMClient, Tool


def create_calculator_tool():
    """Create a calculator tool definition."""
    return Tool(
        name="calculate",
        description="Perform mathematical calculations",
        parameters={
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5', '100 / 4')"
            }
        },
        required=["expression"]
    )


def execute_calculation(expression: str) -> str:
    """
    Execute a mathematical calculation.

    Args:
        expression: Mathematical expression as a string

    Returns:
        Result as a string, or error message
    """
    try:
        # Note: eval() is used here for simplicity
        # In production, use a safer alternative like ast.literal_eval or a math parser
        result = eval(expression)
        return str(result)
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    """Run the calculator example."""
    print("="*60)
    print("Basic Calculator Example")
    print("="*60)

    # Create tool and client
    calculator = create_calculator_tool()
    client = LLMClient(provider="anthropic")

    # User question
    user_query = "What is 123 multiplied by 456? Use the calculate tool."
    print(f"\nUser: {user_query}")

    # First request to LLM
    response = client.chat(user_query, tools=[calculator])

    # Check if LLM wants to use a tool
    tool_calls = response.metadata.get('tool_calls', [])

    if not tool_calls:
        # LLM answered directly without using tool
        print(f"\nAssistant: {response.content}")
        return

    # LLM wants to use the calculator tool
    tool_call = tool_calls[0]
    print(f"\n[Tool Call Requested]")
    print(f"Tool: {tool_call.name}")
    print(f"Arguments: {tool_call.arguments}")

    # Execute the calculation
    result = execute_calculation(tool_call.arguments['expression'])
    print(f"\n[Tool Execution]")
    print(f"Result: {result}")

    # Send result back to LLM for natural language response
    messages = [
        {"role": "user", "content": user_query},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": tool_call.id,
             "name": tool_call.name, "input": tool_call.arguments}
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tool_call.id, "content": result}
        ]}
    ]

    final_response = client.chat(messages, tools=[calculator])
    print(f"\nAssistant: {final_response.content}")

    print("\n" + "="*60)
    print("Example completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()
