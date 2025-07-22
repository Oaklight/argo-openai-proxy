#!/usr/bin/env python3
"""
Test script for Tool class functionality
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

from argoproxy.tool_calls.handler import Tool


def test_openai_chatcompletion_format():
    """Test OpenAI Chat Completions tool format"""
    print("=== Testing OpenAI Chat Completions Tool Format ===")

    openai_tool = {
        "name": "get_weather",
        "description": "Get current weather information",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }

    tool = Tool.from_entry(openai_tool, api_format="openai-chatcompletion")
    assert tool.name == "get_weather"
    assert tool.description == "Get current weather information"
    assert tool.parameters["type"] == "object"
    assert "location" in tool.parameters["properties"]

    # Convert back to OpenAI format
    back_to_openai = tool.to_tool("openai-chatcompletion")
    assert back_to_openai.name == "get_weather"
    assert back_to_openai.description == "Get current weather information"

    print("✅ OpenAI Chat Completions tool format test passed")


def test_openai_response_format():
    """Test OpenAI Responses tool format"""
    print("=== Testing OpenAI Responses Tool Format ===")

    response_tool = {
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
        },
        "type": "function",
        "strict": True,
    }

    tool = Tool.from_entry(response_tool, api_format="openai-response")
    assert tool.name == "calculate"
    assert tool.description == "Perform mathematical calculations"

    # Convert back to Response format
    back_to_response = tool.to_tool("openai-response")
    assert back_to_response.name == "calculate"
    assert back_to_response.strict == False  # Default value

    print("✅ OpenAI Responses tool format test passed")


def test_anthropic_format():
    """Test Anthropic tool format"""
    print("=== Testing Anthropic Tool Format ===")

    anthropic_tool = {
        "name": "file_search",
        "description": "Search for files in the system",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "directory": {"type": "string"},
            },
            "required": ["pattern"],
        },
    }

    tool = Tool.from_entry(anthropic_tool, api_format="anthropic")
    assert tool.name == "file_search"
    assert tool.description == "Search for files in the system"
    assert tool.parameters["type"] == "object"

    # Convert back to Anthropic format
    back_to_anthropic = tool.to_tool("anthropic")
    assert back_to_anthropic.name == "file_search"
    # Check input_schema is correctly set
    if hasattr(back_to_anthropic.input_schema, "type"):
        assert back_to_anthropic.input_schema.type == "object"
    else:
        assert back_to_anthropic.input_schema["type"] == "object"

    print("✅ Anthropic tool format test passed")


def test_cross_format_conversion():
    """Test cross-format tool conversion"""
    print("=== Testing Cross-Format Tool Conversion ===")

    # Create from OpenAI, convert to Anthropic
    openai_tool = {
        "name": "send_email",
        "description": "Send an email message",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
        },
    }

    tool = Tool.from_entry(openai_tool, api_format="openai")
    anthropic_tool = tool.to_tool("anthropic")

    assert anthropic_tool.name == "send_email"
    assert anthropic_tool.description == "Send an email message"

    # Check input_schema properties
    if hasattr(anthropic_tool.input_schema, "properties"):
        assert anthropic_tool.input_schema.properties["to"]["type"] == "string"
    else:
        assert anthropic_tool.input_schema["properties"]["to"]["type"] == "string"

    print("✅ Cross-format tool conversion test passed")


def test_general_format():
    """Test general tool format"""
    print("=== Testing General Tool Format ===")

    tool = Tool(
        name="test_tool", description="A test tool", parameters={"type": "object"}
    )

    general_result = tool.to_tool("general")
    assert general_result is tool

    print("✅ General tool format test passed")


def test_serialization():
    """Test tool serialization"""
    print("=== Testing Tool Serialization ===")

    tool = Tool(
        name="example_tool",
        description="An example tool for testing",
        parameters={"type": "object", "properties": {"input": {"type": "string"}}},
    )

    # Test serialization to different formats
    openai_serialized = tool.serialize("openai-chatcompletion")
    assert openai_serialized["name"] == "example_tool"
    assert openai_serialized["description"] == "An example tool for testing"

    anthropic_serialized = tool.serialize("anthropic")
    assert anthropic_serialized["name"] == "example_tool"
    assert anthropic_serialized["description"] == "An example tool for testing"

    print("✅ Tool serialization test passed")


def test_error_cases():
    """Test error cases"""
    print("=== Testing Error Cases ===")

    # Test unsupported API format
    try:
        Tool.from_entry({}, api_format="unsupported")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Invalid API format" in str(e)

    # Test Google format (not implemented)
    try:
        Tool.from_entry({}, api_format="google")
        assert False, "Should raise NotImplementedError"
    except NotImplementedError:
        pass

    tool = Tool(name="test", description="test", parameters={})
    try:
        tool.to_tool("google")
        assert False, "Should raise NotImplementedError"
    except NotImplementedError:
        pass

    print("✅ Error cases test passed")


if __name__ == "__main__":
    test_openai_chatcompletion_format()
    test_openai_response_format()
    test_anthropic_format()
    test_cross_format_conversion()
    test_general_format()
    test_serialization()
    test_error_cases()
    print("\n🎉 All Tool tests passed!")
