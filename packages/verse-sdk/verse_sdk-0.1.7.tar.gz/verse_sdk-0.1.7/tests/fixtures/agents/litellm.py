import inspect
import json
from typing import Any, Callable, List

from litellm import Message, ModelResponse, acompletion, completion


def convert_functions_to_tools(functions: List[Callable]):
    tools = []

    for func in functions:
        params = {}
        required = []

        for param_name, param in inspect.signature(func).parameters.items():
            param_type = {
                bool: "boolean",
                dict: "object",
                int: "integer",
                list: "array",
            }.get(param.annotation, "string")

            params[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}",
            }
            required.append(param_name)

        tools.append(
            {
                "function": {
                    "description": func.__doc__ or f"Function {func.__name__}",
                    "name": func.__name__,
                    "parameters": {
                        "properties": params,
                        "required": required,
                        "type": "object",
                    },
                },
                "type": "function",
            }
        )

    return tools


def create_function_map(functions: List[Callable]):
    """Create a mapping from function names to actual functions."""
    return {func.__name__: func for func in functions}


def get_completion_text(response: ModelResponse):
    return response.choices[0].message.content


def run_completion(
    messages: List[Message],
    funcs: List[Callable],
):
    function_map = create_function_map(funcs)
    iteration = 0
    max_iterations = 10
    tools = convert_functions_to_tools(funcs)

    while iteration < max_iterations:
        response = completion(
            model="openai/gpt-5",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message
        tool_calls = message.tool_calls

        if tool_calls:
            messages.append(
                {
                    "content": message.content,
                    "role": "assistant",
                    "tool_calls": tool_calls,
                }
            )
            for tool_call in tool_calls:
                result = run_tool(tool_call, function_map)
                if result:
                    messages.append(result)
        else:
            break
        iteration += 1
    return response


async def run_completion_async(
    messages: List[Message],
    funcs: List[Callable],
):
    function_map = create_function_map(funcs)
    iteration = 0
    max_iterations = 10
    tools = convert_functions_to_tools(funcs)

    while iteration < max_iterations:
        response = await acompletion(
            model="openai/gpt-4o",  # note: account blocked from streaming newer models
            messages=messages,
            tools=tools,
            stream=True,
        )

        tool_calls_made = False
        tool_buffers = {}
        content_buffer = ""

        async for chunk in response:
            choice = chunk["choices"][0]
            delta = choice["delta"]

            if delta.get("content"):
                content_buffer += delta["content"]
                yield delta["content"]

            if delta.get("tool_calls"):
                tool_calls_made = True

                for tool_call in delta["tool_calls"]:
                    args_part = tool_call["function"].get("arguments", "")
                    call_id = tool_call["id"]
                    function_name = tool_call["function"].get("name", "")

                    if call_id is None and function_name is None:
                        if tool_buffers:
                            last_call_id = list(tool_buffers.keys())[-1]
                            tool_buffers[last_call_id]["function"]["arguments"] += (
                                args_part
                            )

                    else:
                        if call_id not in tool_buffers:
                            tool_buffers[call_id] = {
                                "id": call_id,
                                "function": {
                                    "name": function_name,
                                    "arguments": "",
                                },
                            }

                        tool_buffers[call_id]["function"]["arguments"] += args_part

        if content_buffer.strip():
            break

        if tool_calls_made and tool_buffers:
            tool_calls_for_message = []
            tool_results = []

            for call_id, tool_call_data in tool_buffers.items():
                if call_id is None:
                    continue

                try:
                    _ = json.loads(tool_call_data["function"]["arguments"])

                    # note: need to recreate the tool call object for run_tool
                    tool_call_obj = type(
                        "ToolCall",
                        (),
                        {
                            "id": call_id,
                            "function": type(
                                "Function",
                                (),
                                {
                                    "name": tool_call_data["function"]["name"],
                                    "arguments": tool_call_data["function"][
                                        "arguments"
                                    ],
                                },
                            )(),
                        },
                    )()

                    tool_result = run_tool(tool_call_obj, function_map)

                    if tool_result:
                        tool_results.append(tool_result)

                        tool_calls_for_message.append(
                            {
                                "id": call_id,
                                "function": {
                                    "arguments": tool_call_data["function"][
                                        "arguments"
                                    ],
                                    "name": tool_call_data["function"]["name"],
                                },
                                "type": "function",
                            }
                        )

                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

            if tool_calls_for_message:
                assistant_msg = {
                    "content": content_buffer,
                    "role": "assistant",
                    "tool_calls": tool_calls_for_message,
                }
                messages.append(assistant_msg)

                for tool_result in tool_results:
                    messages.append(tool_result)

        if not tool_calls_made and not content_buffer.strip():
            break

        iteration += 1


def run_tool(tool: Any, function_map: dict[str, Callable]):
    function_name = tool.function.name
    function_args = json.loads(tool.function.arguments)

    if function_name in function_map:
        try:
            result = function_map[function_name](**function_args)
            return {
                "content": json.dumps(result),
                "role": "tool",
                "tool_call_id": tool.id,
                "id": tool.id,
            }
        except Exception:
            return None
