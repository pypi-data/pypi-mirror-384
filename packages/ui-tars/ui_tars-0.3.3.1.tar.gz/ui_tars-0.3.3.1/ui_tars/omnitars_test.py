# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0
# pip install ui-tars==0.2.3
import io
import os
import re
import json
import base64
from PIL import Image
from io import BytesIO
from openai import OpenAI
from ui_tars.action_parser import parse_xml_action, parsing_response_to_pyautogui_code

# Please set the API key here
# os.environ['OPENAI_API_KEY'] = 'your api key'
seed_vl_version = "ep-20250905175225-hlrvd"
api_key = "efa2ecef-c5eb-44e1-8853-86c592d7cdc2"
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=api_key,
)

def inference(messages):
    chat_completion = client.chat.completions.create(
        model=seed_vl_version,
        messages=messages,
        top_p=0.9,
        temperature=1.0,
        max_tokens=4096,
        stream=True,
    )

    response = ""
    for message in chat_completion:
        response += message.choices[0].delta.content
    return response

messages = [
    {
        "role": "system",
        "content": 'You should first think about the reasoning process in the mind and then provide the user with the answer. The reasoning process is enclosed within <think_never_used_51bce0c785ca2f68081bfa7d91973934> </think_never_used_51bce0c785ca2f68081bfa7d91973934> tags, i.e. <think_never_used_51bce0c785ca2f68081bfa7d91973934> reasoning process here </think_never_used_51bce0c785ca2f68081bfa7d91973934> answer here'
    },
    {
        "role": "system",
        "content": "You are an agent designed to accomplish tasks.\n\nAs a professional personal assistant (Doubao) capable of solving various user problems, you will first reason through a user's problem to devise a solution, flexibly using a series of tools in combination with your thinking to accomplish the task and provide an accurate, reliable answer. While thinking and using tools, you may continuously and flexibly adjust your solution approach based on the results of tool calls. \n\n\n<seed:cot_budget_reflect>\n</seed:cot_budget_reflect>\n"
    },
    {
        "role": "system",
        "content": """## Function Definition\n\n- You have access to the following functions:\n{\"type\": \"function\", \"name\": \"call_user\", \"parameters\": {\"type\": \"object\", \"properties\": {\"content\": {\"type\": \"string\", \"description\": \"Message or information displayed to the user to request their input, feedback, or guidance.\"}}, \"required\": []}, \"description\": \"This function is used to interact with the user by displaying a message and requesting their input, feedback, or guidance.\"}\n{\"type\": \"function\", \"name\": \"click\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Click coordinates. The format is: <point>x y</point>\"}}, \"required\": [\"point\"]}, \"description\": \"Mouse left single click action.\"}\n{\"type\": \"function\", \"name\": \"doubao_code_interpreter\", \"parameters\": {\"type\": \"object\", \"properties\": {\"id\": {\"type\": \"string\", \"description\": \"需要被运行的代码块 id，从 1 开始顺序计数，请用字符串类型\"}, \"code\": {\"type\": \"string\", \"description\": \"需要被运行的代码块，格式必须严格为```\\n{code_content}\\n```\"}}, \"required\": [\"id\", \"code\"]}, \"description\": \"当你需要通过编写并运行代码实现目标时(例如通过代码进行算术运算、数据分析、文本处理与分析、文件处理、绘制图表与图形等)，使用此工具。可以运行代码块内容，并返回运行结果。代码运行环境是一个支持对应 python 的沙盒环境（非联网环境，因此请勿进行网络请求或任何 API 调用请求）。\"}\n{\"type\": \"function\", \"name\": \"drag\", \"parameters\": {\"type\": \"object\", \"properties\": {\"start_point\": {\"type\": \"string\", \"description\": \"Drag start point. The format is: <point>x y</point>\"}, \"end_point\": {\"type\": \"string\", \"description\": \"Drag end point. The format is: <point>x y</point>\"}}, \"required\": [\"start_point\", \"end_point\"]}, \"description\": \"Mouse left button drag action.\"}\n{\"type\": \"function\", \"name\": \"execute_bash\", \"description\": \"Execute a bash command in the terminal.\\n* Long running commands: For commands that may run indefinitely, it should be run in the background and the output should be redirected to a file, e.g. command = `python3 app.py > server.log 2>&1 &`.\\n* One command at a time: You can only execute one bash command at a time. If you need to run multiple commands sequentially, you can use `&&` or `;` to chain them together.\\n\", \"parameters\": {\"type\": \"object\", \"properties\": {\"command\": {\"type\": \"string\", \"description\": \"The bash command to execute. Can be empty string to view additional logs when previous exit code is `-1`. Can be `C-c` (Ctrl+C) to interrupt the currently running process. Note: You can only execute one bash command at a time. If you need to run multiple commands sequentially, you can use `&&` or `;` to chain them together.\"}}, \"required\": [\"command\"]}}\n{\"type\": \"function\", \"name\": \"finished\", \"parameters\": {\"type\": \"object\", \"properties\": {\"content\": {\"type\": \"string\", \"description\": \"Provide the final answer or response to complete the task.\"}}, \"required\": []}, \"description\": \"This function is used to indicate the completion of a task by providing the final answer or response.\"}\n{\"type\": \"function\", \"name\": \"hotkey\", \"parameters\": {\"type\": \"object\", \"properties\": {\"key\": {\"type\": \"string\", \"description\": \"Hotkeys you want to press. Split keys with a space and use lowercase.\"}}, \"required\": [\"key\"]}, \"description\": \"Press hotkey.\"}\n{\"type\": \"function\", \"name\": \"left_double\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Click coordinates. The format is: <point>x y</point>\"}}, \"required\": [\"point\"]}, \"description\": \"Mouse left double click action.\"}\n{\"type\": \"function\", \"name\": \"mouse_down\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Mouse down position. If not specified, default to execute on the current mouse position. The format is: <point>x y</point>\"}, \"button\": {\"type\": \"string\", \"description\": \"Down button. Default to left.\", \"enum\": [\"left\", \"right\"]}}, \"required\": []}, \"description\": \"Mouse down action.\"}\n{\"type\": \"function\", \"name\": \"mouse_up\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Mouse up position. If not specified, default to execute on the current mouse position. The format is: <point>x y</point>\"}, \"button\": {\"type\": \"string\", \"description\": \"Up button. Default to left.\", \"enum\": [\"left\", \"right\"]}}, \"required\": []}, \"description\": \"Mouse up action.\"}\n{\"type\": \"function\", \"name\": \"move_to\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Target coordinates. The format is: <point>x y</point>\"}}, \"required\": [\"point\"]}, \"description\": \"Mouse move action.\"}\n{\"type\": \"function\", \"name\": \"open_computer\", \"parameters\": {}, \"description\": \"Open computer.\"}\n{\"type\": \"function\", \"name\": \"open_computer\", \"parameters\": {}, \"description\": \"Open computer.\"}\n{\"type\": \"function\", \"name\": \"open_terminal\", \"parameters\": {}, \"description\": \"Open terminal.\"}\n{\"type\": \"function\", \"name\": \"press\", \"parameters\": {\"type\": \"object\", \"properties\": {\"key\": {\"type\": \"string\", \"description\": \"Key you want to press. Only one key can be pressed at one time.\"}}, \"required\": [\"key\"]}, \"description\": \"Press key.\"}\n{\"type\": \"function\", \"name\": \"release\", \"parameters\": {\"type\": \"object\", \"properties\": {\"key\": {\"type\": \"string\", \"description\": \"Key you want to release. Only one key can be released at one time.\"}}, \"required\": [\"key\"]}, \"description\": \"Release key.\"}\n{\"type\": \"function\", \"name\": \"right_single\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Click coordinates. The format is: <point>x y</point>\"}}, \"required\": [\"point\"]}, \"description\": \"Mouse right single click action.\"}\n{\"type\": \"function\", \"name\": \"scroll\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Scroll start position. If not specified, default to execute on the current mouse position. The format is: <point>x y</point>\"}, \"direction\": {\"type\": \"string\", \"description\": \"Scroll direction.\", \"enum\": [\"up\", \"down\", \"left\", \"right\"]}}, \"required\": [\"direction\"]}, \"description\": \"Scroll action.\"}\n{\"type\": \"function\", \"name\": \"str_replace_editor\", \"description\": \"Custom editing tool for viewing, creating and editing files in plain-text format\\n* State is persistent across command calls and discussions with the user\\n* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep\\n* The `create` command cannot be used if the specified `path` already exists as a file\\n* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`\\n* The `undo_edit` command will revert the last edit made to the file at `path`\\n\\nNotes for using the `str_replace` command:\\n* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!\\n* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique\\n* The `new_str` parameter should contain the edited lines that should replace the `old_str`\\n\", \"parameters\": {\"type\": \"object\", \"properties\": {\"command\": {\"description\": \"The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.\", \"enum\": [\"view\", \"create\", \"str_replace\", \"insert\", \"undo_edit\"], \"type\": \"string\"}, \"path\": {\"description\": \"Absolute path to file or directory, e.g. `/workspace/file.py` or `/workspace`.\", \"type\": \"string\"}, \"file_text\": {\"description\": \"Required parameter of `create` command, with the content of the file to be created.\", \"type\": \"string\"}, \"old_str\": {\"description\": \"Required parameter of `str_replace` command containing the string in `path` to replace.\", \"type\": \"string\"}, \"new_str\": {\"description\": \"Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.\", \"type\": \"string\"}, \"insert_line\": {\"description\": \"Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.\", \"type\": \"integer\"}, \"view_range\": {\"description\": \"Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.\", \"items\": {\"type\": \"integer\"}, \"type\": \"array\"}}, \"required\": [\"command\", \"path\"]}}\n{\"type\": \"function\", \"name\": \"take_screenshot\", \"parameters\": {}, \"description\": \"Take screenshot.\"}\n{\"type\": \"function\", \"name\": \"type\", \"parameters\": {\"type\": \"object\", \"properties\": {\"content\": {\"type\": \"string\", \"description\": \"Type content. If you want to submit your input, use \\n at the end of content.\"}}, \"required\": [\"content\"]}, \"description\": \"Type content.\"}\n{\"type\": \"function\", \"name\": \"wait\", \"parameters\": {\"type\": \"object\", \"properties\": {\"time\": {\"type\": \"integer\", \"description\": \"Wait time in seconds.\"}}, \"required\": []}, \"description\": \"Wait for a while.\"}\n\n- To call a function, use the following structure without any suffix:\n\n<think_never_used_51bce0c785ca2f68081bfa7d91973934> reasoning process </think_never_used_51bce0c785ca2f68081bfa7d91973934>\n<seed:tool_call>\n<function=example_function_name>\n<parameter=example_parameter_1>value_1</parameter>\n<parameter=example_parameter_2>\nThis is the value for the second parameter\nthat can span\nmultiple lines\n</parameter>\n</function>\n</seed:tool_call>\n\n## Important Notes\n- Function calls must begin with <function= and end with </function>.\n- All required parameters must be explicitly provided.\n\n## Additional Notes\n- You can call multiple tools in one tool call, for example:\n<seed:tool_call>\n<function=example_function_1>\n<parameter=example_parameter_1>value_1</parameter>\n<parameter=example_parameter_2>\nThis is the value for the second parameter\nthat can span\nmultiple lines\n</parameter>\n</function>\n\n<function=example_function_2>\n<parameter=example_parameter_3>value_3</parameter>\n</function>\n</seed:tool_call>\n- Your reasoning process is contained in <think_never_used_51bce0c785ca2f68081bfa7d91973934></think_never_used_51bce0c785ca2f68081bfa7d91973934>, tool calls are in <seed:tool_call></seed:tool_call>. Note that tool calls cannot be nested inside the reasoning tags, so the common format is to have the reasoning process followed by a tool call, such as </think_never_used_51bce0c785ca2f68081bfa7d91973934><seed:tool_call>\nIf you want to provide the answer, simply place it directly after </think_never_used_51bce0c785ca2f68081bfa7d91973934>, such as </think_never_used_51bce0c785ca2f68081bfa7d91973934> answer here. Do not enclose the answer within any tags.","""
    },
    {
        "role": "user",
        # "content": "Help me write a file with hello world."
        "content": "Click on the top bar."
    },
    {
        "role": "assistant",
        "content": ""
    }
]
response = inference(messages)
print(response)

if "<seed:tool_call>" not in response:
    # no tool calls, considered as finish answer or chat with user
    answer = response.split("</think_never_used_51bce0c785ca2f68081bfa7d91973934>")[-1]
else:
    # parse tool calls
    gui_schemas = json.load(open("gui_tool_schemas.json"))
    code_schemas = json.load(open("code_tool_schemas.json"))
    gui_tool_names = [schema["function"]["name"] for schema in gui_schemas]
    code_tool_names = [schema["function"]["name"] for schema in code_schemas]
    all_schemas = gui_schemas + code_schemas

    # 需要根据实际图片分辨率设置
    image_height = 1080
    image_width = 1920
    parsed_functions = parse_xml_action(response, all_schemas)
    for function_dict in parsed_functions:
        function_name = function_dict["function"]
        function_parameters = function_dict["parameters"]
        if function_name in gui_tool_names:
            actions = [
                {
                    "action_type": function_name,
                    "action_inputs": function_parameters
                }
            ]
            pyautogui_codes = parsing_response_to_pyautogui_code(actions, image_height, image_width)
            print(pyautogui_codes)
        elif function_name in code_tool_names:
            # 根据实际工具接入
            print(function_name, function_parameters)
        else:
            raise RuntimeError(f"Unexpected function call: {function_name}")
