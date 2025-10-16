#!/bin/bash

# Load API keys from prototype .env.local
set -a
source /tmp/llmswap-tools-prototype/.env.local
set +a

# Change to production directory
cd /Users/sreenath/Code/PVC-hackathon-code-2025/any-llm

# Run the test
python3 test_tool_calling_production.py
