#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""临时调试脚本：测试正则匹配"""
import json
import re
from pathlib import Path

# 手动模拟词汇组展开
vocab_groups = {
    "action_open": ["打开", "开启", "启动", "开"],
    "position_all": ["主驾驶", "主驾", "主驾驶位置", "驾驶位", "副驾驶", "副驾", "副驾驶位置", "副驾驶座", "后", "后排", "后座", "后面", "左", "右", "前"],
    "target_window": ["车窗", "车窗玻璃", "窗户玻璃", "窗户"]
}

def expand_pattern(pattern):
    """展开词汇组引用"""
    result = pattern
    for group_id, items in vocab_groups.items():
        # 转义特殊字符
        escaped_items = [re.escape(item) for item in items]
        # 按长度降序排列
        escaped_items.sort(key=len, reverse=True)
        # 组合成正则
        group_pattern = "|".join(escaped_items)
        # 替换
        result = result.replace(f"{{{{group_id}}}}", f"({group_pattern})")
    return result

# 读取车控规则
config_path = Path("configs/regex/车控.json")
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

pattern_config = config["patterns"][0]
original_pattern = pattern_config["pattern"]
print(f"原始模式: {original_pattern}")

# 手动展开
expanded = original_pattern
expanded = expanded.replace("{{action_open}}", f"({'|'.join([re.escape(i) for i in vocab_groups['action_open']])})")
expanded = expanded.replace("{{position_all}}", f"({'|'.join([re.escape(i) for i in sorted(vocab_groups['position_all'], key=len, reverse=True)])})")
expanded = expanded.replace("{{target_window}}", f"({'|'.join([re.escape(i) for i in sorted(vocab_groups['target_window'], key=len, reverse=True)])})")

print(f"\n展开模式（部分）: {expanded[:200]}...")

# 测试匹配
text = "打开主驾车窗"
print(f"\n测试文本: {text}")

# 简化的正则（只测试关键部分）
simple_pattern = r"(打开|开启|启动|开)(?P<target>(?:(主驾驶|主驾|主驾驶位置|驾驶位|副驾驶|副驾|副驾驶位置|副驾驶座|后|后排|后座|后面|左|右|前))?(?:(车窗|车窗玻璃|窗户玻璃|窗户)))"
match = re.search(simple_pattern, text)
if match:
    print(f"匹配成功!")
    print(f"  action: {match.group(1)}")
    print(f"  target: {match.group('target')}")
    print(f"  groups: {match.groups()}")
else:
    print("匹配失败!")

