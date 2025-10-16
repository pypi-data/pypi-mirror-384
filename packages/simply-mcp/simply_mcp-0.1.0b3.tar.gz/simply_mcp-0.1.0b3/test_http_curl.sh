#!/bin/bash

# MCP Inspector HTTP Testing Script
# Tests all MCP functionalities via HTTP JSON-RPC 2.0

echo "========================================"
echo "MCP INSPECTOR HTTP TESTING"
echo "========================================"
echo ""

BASE_URL="http://localhost:8080"

echo "Test 1: List Tools"
echo "===================="
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -m json.tool
echo ""
echo ""

echo "Test 2: Call add_numbers (5 + 3)"
echo "=================================="
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"add_numbers","arguments":{"a":5,"b":3}}}' | python -m json.tool
echo ""
echo ""

echo "Test 3: Call format_greeting (formal)"
echo "======================================"
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"format_greeting","arguments":{"name":"Alice","style":"formal"}}}' | python -m json.tool
echo ""
echo ""

echo "Test 4: Call format_greeting (casual)"
echo "======================================"
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"format_greeting","arguments":{"name":"Bob","style":"casual"}}}' | python -m json.tool
echo ""
echo ""

echo "Test 5: Call format_greeting (friendly)"
echo "========================================"
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"format_greeting","arguments":{"name":"Charlie","style":"friendly"}}}' | python -m json.tool
echo ""
echo ""

echo "Test 6: Call calculate_statistics"
echo "=================================="
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"calculate_statistics","arguments":{"numbers":[1.0,2.0,3.0,4.0,5.0]}}}' | python -m json.tool
echo ""
echo ""

echo "Test 7: List Prompts"
echo "===================="
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":7,"method":"prompts/list","params":{}}' | python -m json.tool
echo ""
echo ""

echo "Test 8: Get code_review prompt"
echo "==============================="
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":8,"method":"prompts/get","params":{"name":"code_review","arguments":{"language":"python","focus":"security"}}}' | python -m json.tool
echo ""
echo ""

echo "Test 9: Get generate_docs prompt"
echo "================================="
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":9,"method":"prompts/get","params":{"name":"generate_docs","arguments":{"component_type":"class"}}}' | python -m json.tool
echo ""
echo ""

echo "Test 10: List Resources"
echo "======================="
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":10,"method":"resources/list","params":{}}' | python -m json.tool
echo ""
echo ""

echo "Test 11: Read config://server"
echo "=============================="
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":11,"method":"resources/read","params":{"uri":"config://server"}}'  | python -m json.tool
echo ""
echo ""

echo "Test 12: Read system://info"
echo "============================="
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":12,"method":"resources/read","params":{"uri":"system://info"}}' | python -m json.tool
echo ""
echo ""

echo "========================================"
echo "ALL TESTS COMPLETED"
echo "========================================"
