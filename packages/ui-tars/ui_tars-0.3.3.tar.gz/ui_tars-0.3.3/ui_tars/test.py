import re
import json

def parse_structure_to_tree(input_text):
    # Step 1: 提取所有标签信息
    def extract_tags(text):
        tag_pattern = r"<(/?)(\w+)(?:=([^>]+))?>"
        tags = []
        for match in re.finditer(tag_pattern, text):
            is_closing = match.group(1) == "/"
            tag_name = match.group(2)
            tag_param = match.group(3)
            start_idx = match.start()
            end_idx = match.end()
            tags.append({
                "is_closing": is_closing,
                "tag_name": tag_name,
                "tag_param": tag_param,
                "start_idx": start_idx,
                "end_idx": end_idx
            })
        return tags

    # Step 2: 构建树结构
    def build_tree(tags, text):
        """
        构建树结构，包含开始标签和闭合标签。
        :param tags: 提取的标签列表。
        :param text: 原始文本，用于提取内容。
        :return: 构建的树结构。
        """
        # 引入一个虚拟根节点
        root = {
            "tag_name": "root",
            "tag_param": None,
            "start_idx": None,
            "end_idx": None,
            "children": []
        }
        stack = [root]  # 用于管理当前的标签层级，初始栈中包含虚拟根节点

        for tag in tags:
            if not tag["is_closing"]:
                # 开始标签
                node = {
                    "tag_name": tag["tag_name"],
                    "tag_param": tag["tag_param"],
                    "start_idx": tag["start_idx"],
                    "end_idx": tag["end_idx"],
                    "children": []
                }
                # 将当前节点添加到栈顶节点的 children 中
                stack[-1]["children"].append(node)
                # 将当前节点压入栈
                stack.append(node)
            else:
                # 闭合标签
                if stack:
                    # 将闭合标签信息添加到栈顶节点
                    stack[-1]["close_tag_name"] = "/" + tag["tag_name"]
                    stack[-1]["close_tag_param"] = None
                    stack[-1]["close_tag_start_idx"] = tag["start_idx"]
                    stack[-1]["close_tag_end_idx"] = tag["end_idx"]
                    # 弹出栈顶
                    stack.pop()

        return root

    # Step 3: 提取标签内容
    def extract_content(node, text):
        import pdb;pdb.set_trace()
        if node["tag_name"] == "parameter":
            # 提取 <parameter=key>value</parameter> 的内容
            param_key = node["tag_param"]
            param_value = text[node["start_idx"]:node["end_idx"]]
            return {param_key: param_value}
        elif node["tag_name"] == "list":
            # 提取 <list>...</list> 的内容
            return [extract_content(child, text) for child in node["children"]]
        elif node["tag_name"] == "object":
            # 提取 <object>...</object> 的内容
            return {child["tag_param"]: extract_content(child, text) for child in node["children"]}
        else:
            return text[node["start_idx"]:node["end_idx"]]

    # 执行解析
    tags = extract_tags(input_text)
    tree = build_tree(tags, input_text)
    final_result = {}
    for child in tree["children"]:
        result = parse_tree(child, input_text)
        final_result.update(result)
    return final_result

def parse_tree(node, input_text):
    # 如果当前节点有子节点，递归解析子节点
    if "children" in node and node["children"]:
        # 如果当前节点是 "parameter" 且有 tag_param，构建一个键值对
        if node["tag_name"] == "parameter" and node["tag_param"]:
            # 如果只有一个子节点，直接解析子节点
            if len(node["children"]) == 1:
                return {node["tag_param"]: parse_tree(node["children"][0], input_text)}
            # 如果有多个子节点，解析为列表
            else:
                return {node["tag_param"]: [parse_tree(child, input_text) for child in node["children"]]}
        # 如果当前节点是 "list"，返回子节点的列表
        elif node["tag_name"] == "list":
            result = [parse_tree(child, input_text) for child in node["children"]]
            # import pdb;pdb.set_trace()
            return result
        # 如果当前节点是 "object" 或其他容器类型，返回子节点的合并结果
        elif node["tag_name"] == "object":
            result = {}
            for child in node["children"]:
                child_result = parse_tree(child, input_text)
                # 确保子节点返回的是字典
                if isinstance(child_result, dict):
                    result.update(child_result)
                else:
                    raise RuntimeError("Object return not dict!!!")
                # import pdb;pdb.set_trace()
            return result
        elif node["tag_name"] == "item":
            dict_result = {}
            list_result = []
            is_dict = False
            is_list = False
            for child in node["children"]:
                child_result = parse_tree(child, input_text)
                # 确保子节点返回的是字典
                if isinstance(child_result, dict):
                    dict_result.update(child_result)
                    is_dict = True
                elif isinstance(child_result, list):
                    list_result.extend(child_result)
                    is_list = True
                else:
                    raise RuntimeError("Item with children return not dict or list !!!")
                # import pdb;pdb.set_trace()
            if is_list:
                return list_result
            else:
                return dict_result
    else:
        # 如果当前节点没有子节点，提取实际的值
        end_idx = node["end_idx"]
        close_tag_start_idx = node["close_tag_start_idx"]
        value = input_text[end_idx:close_tag_start_idx]
        if node["tag_name"] == "parameter" and node["tag_param"]:
            return {node["tag_param"]: value}
        else:
            return value
    return {}

# 示例输入
input_text = """<parameter=attachments><list><item><object><parameter=attachment_name><object><parameter=attachment_name1>IT基础设施升级项目PPT111</parameter><parameter=attachment_name1.5><list><item>a</item><item>b</item><item><object><parameter=abc>i am abc</parameter></object></item></list></parameter></object></parameter><parameter=attachment_source>https://lf3-static.bytednsdoc.com/obj/eden-cn/upnbsw-tss/ljhwZthlaukjlkulzlp/super_doubao/c0cd897ac9785143aff5d6eca81b8244/41639896bd94a961288a28f44060cb18/IT基础设施升级项目汇报/index.html</parameter></object></item><item><object><parameter=attachment_name><object><parameter=attachment_name2>IT基础设施升级项目PPT222</parameter></object></parameter><parameter=attachment_source>https://lf3-static.bytednsdoc.com/obj/eden-cn/upnbsw-tss/ljhwZthlaukjlkulzlp/super_doubao/c0cd897ac9785143aff5d6eca81b8244/41639896bd94a961288a28f44060cb18/IT基础设施升级项目汇报/index.html</parameter></object></item><item>111</item><item><list><item>222</item><item>333</item></list></item></list></parameter><parameter=attachments2><object><parameter=attachment_name>json</parameter></object>"""


# input_text = """<parameter=attachments><list><item>1</item></list></parameter>"""

# 调用解析函数
parsed_result = parse_structure_to_tree(input_text)
# print(parsed_result)

# 预期输出
a = {
    "attachments": [
        {
            "attachment_name": {
                "attachment_name1": "IT基础设施升级项目PPT111",
                "attachment_name1.5": [
                    "a",
                    "b",
                    {
                        "abc": "i am abc"
                    }
                ]
            },
            "attachment_source": "https://lf3-static.bytednsdoc.com/obj/eden-cn/upnbsw-tss/ljhwZthlaukjlkulzlp/super_doubao/c0cd897ac9785143aff5d6eca81b8244/41639896bd94a961288a28f44060cb18/IT基础设施升级项目汇报/index.html"
        },
        {
            "attachment_name": {
                "attachment_name2": "IT基础设施升级项目PPT222"
            },
            "attachment_source": "https://lf3-static.bytednsdoc.com/obj/eden-cn/upnbsw-tss/ljhwZthlaukjlkulzlp/super_doubao/c0cd897ac9785143aff5d6eca81b8244/41639896bd94a961288a28f44060cb18/IT基础设施升级项目汇报/index.html"
        },
        "111",
        [
            "222",
            "333"
        ]
    ],
    "attachments2": {
        "attachment_name": "json"
    }
}

# 输出结果
import json
print(json.dumps(parsed_result, ensure_ascii=False, indent=4))