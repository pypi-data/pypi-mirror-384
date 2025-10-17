#!/usr/bin/env python3
"""
Example 3: Customer Support Bot

Demonstrates a real-world use case with multiple tools for customer support.
"""

from llmswap import LLMClient, Tool
from typing import Dict, Any
import json


# Mock database
ORDERS_DB = {
    "ORD-12345": {
        "status": "shipped",
        "items": ["Laptop", "Mouse"],
        "total": 1299.99,
        "tracking": "1Z999AA10123456784",
        "shipping_address": "123 Main St, San Francisco, CA 94102"
    },
    "ORD-67890": {
        "status": "processing",
        "items": ["Phone Case", "Screen Protector"],
        "total": 29.99,
        "tracking": None,
        "shipping_address": "456 Oak Ave, New York, NY 10001"
    }
}


def create_support_tools():
    """Create customer support tools."""
    return [
        Tool(
            name="lookup_order",
            description="Look up order status and details by order ID",
            parameters={
                "order_id": {
                    "type": "string",
                    "description": "Order ID (e.g., 'ORD-12345')"
                }
            },
            required=["order_id"]
        ),
        Tool(
            name="update_shipping_address",
            description="Update the shipping address for an order",
            parameters={
                "order_id": {
                    "type": "string",
                    "description": "Order ID to update"
                },
                "new_address": {
                    "type": "string",
                    "description": "New shipping address"
                }
            },
            required=["order_id", "new_address"]
        ),
        Tool(
            name="request_refund",
            description="Initiate a refund request for an order",
            parameters={
                "order_id": {
                    "type": "string",
                    "description": "Order ID to refund"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for refund"
                }
            },
            required=["order_id", "reason"]
        )
    ]


def lookup_order(order_id: str) -> str:
    """Look up order in database."""
    order = ORDERS_DB.get(order_id)

    if not order:
        return f"Order {order_id} not found"

    return json.dumps({
        "order_id": order_id,
        "status": order["status"],
        "items": order["items"],
        "total": order["total"],
        "tracking": order["tracking"],
        "shipping_address": order["shipping_address"]
    })


def update_shipping_address(order_id: str, new_address: str) -> str:
    """Update shipping address."""
    if order_id not in ORDERS_DB:
        return f"Order {order_id} not found"

    order = ORDERS_DB[order_id]

    if order["status"] == "shipped":
        return f"Cannot update address - order already shipped"

    old_address = order["shipping_address"]
    order["shipping_address"] = new_address

    return f"Shipping address updated from '{old_address}' to '{new_address}'"


def request_refund(order_id: str, reason: str) -> str:
    """Process refund request."""
    if order_id not in ORDERS_DB:
        return f"Order {order_id} not found"

    order = ORDERS_DB[order_id]

    return json.dumps({
        "refund_status": "initiated",
        "order_id": order_id,
        "amount": order["total"],
        "reason": reason,
        "ticket_id": f"REF-{order_id[-5:]}"
    })


def execute_tool(tool_call) -> str:
    """Execute the appropriate tool based on the tool call."""
    if tool_call.name == "lookup_order":
        return lookup_order(**tool_call.arguments)

    elif tool_call.name == "update_shipping_address":
        return update_shipping_address(**tool_call.arguments)

    elif tool_call.name == "request_refund":
        return request_refund(**tool_call.arguments)

    return "Unknown tool"


def handle_customer_query(query: str, tools: list, client: LLMClient):
    """Handle a customer support query."""
    print(f"\nCustomer: {query}")
    print("-" * 60)

    # Initial request
    response = client.chat(query, tools=tools)

    # Check for tool calls
    tool_calls = response.metadata.get('tool_calls', [])

    if not tool_calls:
        print(f"Agent: {response.content}")
        return

    # Execute all tool calls
    results = []
    for tool_call in tool_calls:
        print(f"[Calling {tool_call.name} with {tool_call.arguments}]")
        result = execute_tool(tool_call)
        results.append((tool_call, result))
        print(f"[Result: {result}]")

    # Send results back to LLM for natural language response
    messages = [
        {"role": "user", "content": query}
    ]

    # Add tool use
    tool_content = []
    for tool_call, _ in results:
        tool_content.append({
            "type": "tool_use",
            "id": tool_call.id,
            "name": tool_call.name,
            "input": tool_call.arguments
        })

    messages.append({"role": "assistant", "content": tool_content})

    # Add tool results
    result_content = []
    for tool_call, result in results:
        result_content.append({
            "type": "tool_result",
            "tool_use_id": tool_call.id,
            "content": result
        })

    messages.append({"role": "user", "content": result_content})

    # Get final response
    final_response = client.chat(messages, tools=tools)
    print(f"\nAgent: {final_response.content}")


def main():
    """Run customer support examples."""
    print("="*60)
    print("Customer Support Bot with Tool Calling")
    print("="*60)

    # Create client and tools
    client = LLMClient(provider="anthropic")
    tools = create_support_tools()

    # Example queries
    queries = [
        "What's the status of my order ORD-12345?",
        "I need to change the shipping address for ORD-67890 to '789 Pine St, Austin, TX 78701'",
        "I want to return order ORD-12345 because it's damaged"
    ]

    for query in queries:
        handle_customer_query(query, tools, client)
        print()

    print("="*60)
    print("Demo Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
