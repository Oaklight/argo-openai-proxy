import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from argoproxy.utils.tool_call import (
    convert_tool_calls_to_openai_format,
    handle_tools,
    parse_tool_call_response,
)


def test_handle_tools():
    """测试 handle_tools 函数"""
    print("=== 测试 handle_tools 函数 ===")

    # 测试数据
    tools = [
        {
            "name": "calculate",
            "description": "执行数学计算",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"],
            },
        }
    ]

    # 测试 1: 带 messages 的输入
    input_data_1 = {
        "messages": [{"role": "user", "content": "计算 2 + 3"}],
        "tools": tools,
        "tool_choice": "auto",
    }

    result_1 = handle_tools(input_data_1.copy())
    print("测试 1 - 带 messages:")
    print(f"系统消息长度: {len(result_1['messages'][0]['content'])}")
    print(f"工具字段已移除: {'tools' not in result_1}")

    # 测试 2: 带现有系统消息的输入
    input_data_2 = {
        "messages": [
            {"role": "system", "content": "你是一个有用的助手。"},
            {"role": "user", "content": "计算 2 + 3"},
        ],
        "tools": tools,
        "tool_choice": "auto",
    }

    result_2 = handle_tools(input_data_2.copy())
    print("\n测试 2 - 带现有系统消息:")
    print(
        f"系统消息包含原内容: {'你是一个有用的助手' in result_2['messages'][0]['content']}"
    )
    print(
        f"系统消息包含工具提示: {'Available tools' in result_2['messages'][0]['content']}"
    )

    # 测试 3: 没有工具的输入
    input_data_3 = {"messages": [{"role": "user", "content": "你好"}]}

    result_3 = handle_tools(input_data_3.copy())
    print("\n测试 3 - 没有工具:")
    print(f"数据未改变: {result_3 == input_data_3}")


def test_parse_tool_call_response():
    """测试 parse_tool_call_response 函数"""
    print("\n=== 测试 parse_tool_call_response 函数 ===")

    # 测试 1: 单个工具调用
    response_1 = """<tool_call>
{
  "name": "calculate",
  "arguments": {"expression": "2 + 3"}
}
</tool_call>

计算结果是 5。"""

    tool_calls_1, remaining_1 = parse_tool_call_response(response_1)
    print("测试 1 - 单个工具调用:")
    print(f"解析成功: {tool_calls_1 is not None}")
    print(f"工具名称: {tool_calls_1[0]['name'] if tool_calls_1 else 'None'}")
    print(f"剩余文本: {remaining_1}")

    # 测试 2: 多个工具调用
    response_2 = """<tool_call>
{
  "tool_calls": [
    {"name": "calculate", "arguments": {"expression": "2 + 3"}},
    {"name": "calculate", "arguments": {"expression": "4 * 5"}}
  ]
}
</tool_call>

计算完成。"""

    tool_calls_2, remaining_2 = parse_tool_call_response(response_2)
    print("\n测试 2 - 多个工具调用:")
    print(f"解析成功: {tool_calls_2 is not None}")
    print(f"工具调用数量: {len(tool_calls_2) if tool_calls_2 else 0}")

    # 测试 3: 没有工具调用
    response_3 = "这是一个普通的回复，没有工具调用。"

    tool_calls_3, remaining_3 = parse_tool_call_response(response_3)
    print("\n测试 3 - 没有工具调用:")
    print(f"正确返回 None: {tool_calls_3 is None}")
    print(f"文本保持不变: {remaining_3 == response_3}")


def test_convert_tool_calls_to_openai_format():
    """测试 convert_tool_calls_to_openai_format 函数"""
    print("\n=== 测试 convert_tool_calls_to_openai_format 函数 ===")

    tool_calls = [
        {"name": "calculate", "arguments": {"expression": "2 + 3"}},
        {"name": "get_weather", "arguments": {"location": "北京"}},
    ]

    openai_format = convert_tool_calls_to_openai_format(tool_calls)

    print(f"转换成功: {len(openai_format) == 2}")
    print(f"第一个调用 ID: {openai_format[0]['id']}")
    print(f"第一个调用类型: {openai_format[0]['type']}")
    print(f"第一个调用函数名: {openai_format[0]['function']['name']}")


if __name__ == "__main__":
    test_handle_tools()
    test_parse_tool_call_response()
    test_convert_tool_calls_to_openai_format()
    print("\n所有测试完成！")
