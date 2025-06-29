from time import time

from argoproxy.tool_calls.output_handle import ToolInterceptor

cs = ToolInterceptor()

response_text = '<tool_call> {"name": "test", "arguments": {"arg1": "value1"}}</tool_call> words <tool_call> {"name": "test2", "arguments": {"arg2": "value2"}}</tool_call>\n\nsomewords\n\n'


time_start = time()
for _ in range(10000):
    tool_calls, cleaned_text = cs.process(response_text)
time_end = time()
print(f"ToolInterceptor Time taken: {time_end - time_start}")
print(tool_calls)
print(cleaned_text)
