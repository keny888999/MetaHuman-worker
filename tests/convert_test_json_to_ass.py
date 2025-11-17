#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将 test_long_sentences_comma_split.json 转换为 ASS 字幕文件的示例脚本
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.json_to_ass_converter import json_to_ass


def convert_test_file():
    """转换测试文件"""
    # 输入JSON文件路径
    json_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "results",
        "test_long_sentences_comma_split.json"
    )

    # 输出ASS文件路径
    ass_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "results",
        "test_long_sentences_comma_split.ass"
    )

    # 转换文件
    json_to_ass(
        json_file_path=json_file_path,
        ass_file_path=ass_file_path,
        title="Test Long Sentences Subtitle",
        font_name="Microsoft YaHei",
        font_size=16,
        primary_color="&H00FFFFFF",  # 白色
        outline_color="&H00000000",  # 黑色
        outline=1,
        shadow=0,
        alignment=2,  # 底部居中
        margin_v=20   # 垂直边距
    )

    print(f"转换完成！ASS文件已保存到: {ass_file_path}")


if __name__ == "__main__":
    convert_test_file()
