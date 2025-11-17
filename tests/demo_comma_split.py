#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示如何使用新增的根据逗号或顿号分割字幕功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import split_subtitle_json_by_comma


def main():
    print("演示根据逗号或顿号分割字幕功能")
    print("=" * 50)

    # 示例1: 处理原始的sentences_output.json文件
    print("示例1: 处理原始的sentences_output.json文件")
    split_subtitle_json_by_comma(
        input_json_file="sentences_output.json",
        output_json_file="./results/sentences_output_comma_split.json",
        video_width=358,
        video_height=512,
        font_size=16
    )

    # 示例2: 处理长句子测试文件
    print("\n示例2: 处理长句子测试文件")
    split_subtitle_json_by_comma(
        input_json_file="test_long_sentences.json",
        output_json_file="./results/test_long_sentences_comma_split.json",
        video_width=358,
        video_height=512,
        font_size=16
    )

    print("\n处理完成! 请查看results目录下的输出文件。")


if __name__ == "__main__":
    main()
