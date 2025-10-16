#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from MarkdownConverter import MarkdownConverter

# 测试用例：模拟用户提供的HTML结构
test_markdown = """
临停收费规则

节假日临时车（免费）

车辆类型：临时车
车牌类型：临时车
免费时间：不限
计费规则：免费
有效期：长期有效

2022年8月起临停车规则

车辆类型：临时车
车牌类型：临时车
免费时间：不限
计费规则：免费
有效期：长期有效
"""

def test_markdown_to_html():
    print("=== 测试Markdown转HTML ===")
    
    # 创建转换器
    converter = MarkdownConverter(test_markdown)
    
    # 转换为HTML
    html_content = converter.to_html()
    
    print("生成的HTML内容：")
    print(html_content)
    print("\n" + "="*50 + "\n")
    
    # 测试转换为Word
    print("=== 测试Markdown转Word ===")
    try:
        word_file = converter.to_word("test_output")
        print(f"Word文件已生成: {word_file}")
    except Exception as e:
        print(f"Word转换出错: {e}")
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    test_markdown_to_html()