#!/usr/bin/env python3
"""
Test script for ToolChoice class functionality
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

from argoproxy.tool_calls.handler import NamedTool, ToolChoice


def test_openai_chatcompletion_format():
    """Test OpenAI Chat Completions API format"""
    print("=== Testing OpenAI Chat Completions Format ===")

    # Test string formats
    tc1 = ToolChoice.from_entry("auto", api_format="openai-chatcompletion")
    print(f"auto -> {tc1}")
    assert tc1.choice == "optional"

    tc2 = ToolChoice.from_entry("required", api_format="openai-chatcompletion")
    print(f"required -> {tc2}")
    assert tc2.choice == "any"

    tc3 = ToolChoice.from_entry("none", api_format="openai-chatcompletion")
    print(f"none -> {tc3}")
    assert tc3.choice == "none"

    # Test named tool format
    named_tool_data = {"type": "function", "function": {"name": "get_weather"}}
    tc4 = ToolChoice.from_entry(named_tool_data, api_format="openai-chatcompletion")
    print(f"named tool -> {tc4}")
    assert isinstance(tc4.choice, NamedTool)
    assert tc4.choice.name == "get_weather"

    # Test conversion back to OpenAI format
    result1 = tc1.to_tool_choice("openai-chatcompletion")
    print(f"Convert back to openai-chatcompletion: {result1}")
    assert result1 == "auto"

    result4 = tc4.to_tool_choice("openai-chatcompletion")
    print(f"Convert back to openai-chatcompletion (named): {result4}")
    print(f"Serialized: {result4.model_dump()}")

    print("✅ OpenAI Chat Completions format test passed")


def test_openai_response_format():
    """Test OpenAI Responses API format"""
    print("\n=== Testing OpenAI Responses Format ===")

    # Test string formats
    tc1 = ToolChoice.from_entry("auto", api_format="openai-response")
    print(f"auto -> {tc1}")
    assert tc1.choice == "optional"

    # Test named tool format
    named_tool_data = {"type": "function", "name": "calculate_sum"}
    tc2 = ToolChoice.from_entry(named_tool_data, api_format="openai-response")
    print(f"named tool -> {tc2}")
    assert isinstance(tc2.choice, NamedTool)
    assert tc2.choice.name == "calculate_sum"

    # Test conversion back to OpenAI Response format
    result2 = tc2.to_tool_choice("openai-response")
    print(f"Convert back to openai-response (named): {result2}")
    print(f"Serialized: {result2.model_dump()}")

    print("✅ OpenAI Responses format test passed")


def test_anthropic_format():
    """Test Anthropic API format"""
    print("\n=== Testing Anthropic Format ===")

    # Test various types
    tc1 = ToolChoice.from_entry({"type": "auto"}, api_format="anthropic")
    print(f"auto -> {tc1}")
    assert tc1.choice == "optional"

    tc2 = ToolChoice.from_entry({"type": "any"}, api_format="anthropic")
    print(f"any -> {tc2}")
    assert tc2.choice == "any"

    tc3 = ToolChoice.from_entry({"type": "none"}, api_format="anthropic")
    print(f"none -> {tc3}")
    assert tc3.choice == "none"

    tc4 = ToolChoice.from_entry(
        {"type": "tool", "name": "search_web"}, api_format="anthropic"
    )
    print(f"tool -> {tc4}")
    assert isinstance(tc4.choice, NamedTool)
    assert tc4.choice.name == "search_web"

    # Test conversion back to Anthropic format
    result1 = tc1.to_tool_choice("anthropic")
    print(f"Convert back to anthropic (auto): {result1}")
    print(f"Serialized: {result1.model_dump()}")

    result4 = tc4.to_tool_choice("anthropic")
    print(f"Convert back to anthropic (tool): {result4}")
    print(f"Serialized: {result4.model_dump()}")

    print("✅ Anthropic format test passed")


def test_cross_format_conversion():
    """Test cross-format conversion"""
    print("\n=== Testing Cross-Format Conversion ===")

    # From OpenAI to Anthropic
    openai_data = {"type": "function", "function": {"name": "translate_text"}}
    tc = ToolChoice.from_entry(openai_data, api_format="openai-chatcompletion")

    anthropic_result = tc.to_tool_choice("anthropic")
    print(f"OpenAI -> Anthropic: {anthropic_result.model_dump()}")

    # From Anthropic to OpenAI
    anthropic_data = {"type": "tool", "name": "analyze_sentiment"}
    tc2 = ToolChoice.from_entry(anthropic_data, api_format="anthropic")

    openai_result = tc2.to_tool_choice("openai-chatcompletion")
    print(f"Anthropic -> OpenAI: {openai_result.model_dump()}")

    print("✅ Cross-format conversion test passed")


def test_string_choices():
    """Test string-type tool choices"""
    print("\n=== Testing String Tool Choices ===")

    # Test auto
    choice_auto = ToolChoice.from_entry("auto", api_format="openai")
    assert choice_auto.choice == "optional"

    # Test required
    choice_required = ToolChoice.from_entry("required", api_format="openai")
    assert choice_required.choice == "any"

    # Test none
    choice_none = ToolChoice.from_entry("none", api_format="openai")
    assert choice_none.choice == "none"

    print("✅ String tool choices test passed")


def test_serialization():
    """Test serialization functionality"""
    print("\n=== Testing Serialization ===")

    # String choice serialization
    choice = ToolChoice.from_entry("auto", api_format="openai")
    serialized = choice.serialize("openai")
    assert serialized == "auto"

    # Named tool serialization
    named_choice_data = {"type": "function", "function": {"name": "test_func"}}
    named_choice = ToolChoice.from_entry(
        named_choice_data, api_format="openai-chatcompletion"
    )
    serialized = named_choice.serialize("openai-chatcompletion")
    assert serialized["function"]["name"] == "test_func"

    print("✅ Serialization test passed")


def test_error_cases():
    """Test error cases"""
    print("\n=== Testing Error Cases ===")

    # Test invalid string choice
    try:
        ToolChoice.from_entry("invalid_choice", api_format="openai-chatcompletion")
        assert False, "Should raise exception"
    except ValueError as e:
        print(f"Correctly caught error: {e}")

    # Test invalid OpenAI format
    try:
        ToolChoice.from_entry({"invalid": "data"}, api_format="openai-chatcompletion")
        assert False, "Should raise exception"
    except ValueError as e:
        print(f"Correctly caught error: {e}")

    # Test Anthropic tool without name
    try:
        ToolChoice.from_entry({"type": "tool"}, api_format="anthropic")
        assert False, "Should raise exception"
    except ValueError as e:
        print(f"Correctly caught error: {e}")

    # Test unsupported API format
    try:
        ToolChoice.from_entry("auto", api_format="unsupported")
        assert False, "Should raise exception"
    except ValueError as e:
        print(f"Correctly caught error: {e}")

    # Test Google format (not implemented)
    choice = ToolChoice(choice="optional")
    try:
        choice.to_tool_choice("google")
        assert False, "Should raise NotImplementedError"
    except NotImplementedError as e:
        print(f"Correctly caught error: {e}")

    print("✅ Error cases test passed")


def test_named_tool():
    """Test NamedTool functionality"""
    print("\n=== Testing NamedTool ===")

    named_tool = NamedTool(name="my_function")
    assert named_tool.name == "my_function"
    assert str(named_tool) == "NamedTool(name=my_function)"
    assert repr(named_tool) == "NamedTool(name=my_function)"

    print("✅ NamedTool test passed")


if __name__ == "__main__":
    test_openai_chatcompletion_format()
    test_openai_response_format()
    test_anthropic_format()
    test_cross_format_conversion()
    test_string_choices()
    test_serialization()
    test_error_cases()
    test_named_tool()
    print("\n🎉 All ToolChoice tests passed!")
