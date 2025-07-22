#!/usr/bin/env python3
"""
Test script for ToolCall class functionality
"""

import json
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

from argoproxy.tool_calls.handler import ToolCall


def test_openai_chatcompletion_format():
    """Test OpenAI Chat Completions API format conversion"""
    print("=== Testing OpenAI Chat Completions Format ===")

    # Test data
    openai_tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {
            "name": "get_weather",
            "arguments": '{"location": "Beijing", "unit": "celsius"}',
        },
    }

    # Create from OpenAI format
    tool_call = ToolCall.from_entry(
        openai_tool_call, api_format="openai-chatcompletion"
    )
    assert tool_call.id == "call_123"
    assert tool_call.name == "get_weather"
    assert tool_call.arguments == '{"location": "Beijing", "unit": "celsius"}'

    # Convert back to OpenAI format
    back_to_openai = tool_call.to_tool_call("openai-chatcompletion")
    assert back_to_openai.id == "call_123"
    assert back_to_openai.function.name == "get_weather"
    assert (
        back_to_openai.function.arguments
        == '{"location": "Beijing", "unit": "celsius"}'
    )

    # Test serialization
    serialized = tool_call.serialize("openai-chatcompletion")
    assert serialized["id"] == "call_123"
    assert serialized["function"]["name"] == "get_weather"

    print("✅ OpenAI Chat Completions format test passed")


def test_openai_response_format():
    """Test OpenAI Responses API format conversion"""
    print("=== Testing OpenAI Responses Format ===")

    # Test data
    response_tool_call = {
        "call_id": "fc_123456",
        "name": "calculate_sum",
        "arguments": '{"numbers": [1, 2, 3, 4, 5]}',
        "type": "function_call",
    }

    # Create from Response format
    tool_call = ToolCall.from_entry(response_tool_call, api_format="openai-response")
    assert tool_call.id == "fc_123456"
    assert tool_call.name == "calculate_sum"
    assert tool_call.arguments == '{"numbers": [1, 2, 3, 4, 5]}'

    # Convert back to Response format
    back_to_response = tool_call.to_tool_call("openai-response")
    assert back_to_response.call_id == "fc_123456"
    assert back_to_response.name == "calculate_sum"
    assert back_to_response.arguments == '{"numbers": [1, 2, 3, 4, 5]}'

    print("✅ OpenAI Responses format test passed")


def test_anthropic_format():
    """Test Anthropic API format conversion"""
    print("=== Testing Anthropic Format ===")

    # Test data - dictionary input
    anthropic_tool_call = {
        "id": "toolu_123",
        "type": "tool_use",
        "name": "search_web",
        "input": {"query": "Python programming", "max_results": 10},
    }

    # Create from Anthropic format
    tool_call = ToolCall.from_entry(anthropic_tool_call, api_format="anthropic")
    assert tool_call.id == "toolu_123"
    assert tool_call.name == "search_web"

    # Verify arguments are correctly serialized as JSON string
    parsed_args = json.loads(tool_call.arguments)
    assert parsed_args["query"] == "Python programming"
    assert parsed_args["max_results"] == 10

    # Convert back to Anthropic format
    back_to_anthropic = tool_call.to_tool_call("anthropic")
    assert back_to_anthropic.id == "toolu_123"
    assert back_to_anthropic.name == "search_web"
    assert back_to_anthropic.input["query"] == "Python programming"

    print("✅ Anthropic format test passed")


def test_cross_format_conversion():
    """Test cross-format conversion"""
    print("=== Testing Cross-Format Conversion ===")

    # Create from OpenAI, convert to Anthropic
    openai_data = {
        "id": "call_abc",
        "type": "function",
        "function": {
            "name": "translate",
            "arguments": '{"text": "Hello", "target_lang": "zh"}',
        },
    }

    tool_call = ToolCall.from_entry(openai_data, api_format="openai")
    anthropic_result = tool_call.to_tool_call("anthropic")

    assert anthropic_result.id == "call_abc"
    assert anthropic_result.name == "translate"
    assert anthropic_result.input["text"] == "Hello"
    assert anthropic_result.input["target_lang"] == "zh"

    print("✅ Cross-format conversion test passed")


def test_invalid_json_handling():
    """Test invalid JSON handling"""
    print("=== Testing Invalid JSON Handling ===")

    # Create a tool call with invalid JSON
    tool_call = ToolCall(
        id="test_123", name="test_func", arguments="invalid json string"
    )

    # Converting to Anthropic format should handle invalid JSON
    anthropic_result = tool_call.to_tool_call("anthropic")
    assert anthropic_result.input == "invalid json string"

    print("✅ Invalid JSON handling test passed")


def test_error_cases():
    """Test error cases"""
    print("=== Testing Error Cases ===")

    # Test unsupported format
    tool_call = ToolCall(id="test", name="func", arguments="{}")

    try:
        tool_call.to_tool_call("google")
        assert False, "Should raise NotImplementedError"
    except NotImplementedError:
        pass

    try:
        tool_call.to_tool_call("invalid_format")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    print("✅ Error cases test passed")


if __name__ == "__main__":
    test_openai_chatcompletion_format()
    test_openai_response_format()
    test_anthropic_format()
    test_cross_format_conversion()
    test_invalid_json_handling()
    test_error_cases()
    print("\n🎉 All ToolCall tests passed!")
