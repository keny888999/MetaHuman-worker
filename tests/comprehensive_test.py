#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全面测试多语言字幕换行功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def test_various_texts():
    """测试各种文本"""
    print("全面测试多语言字幕换行功能")
    print("=" * 30)

    # 创建处理器
    processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)

    test_cases = [
        # 简单英文
        "Hello world",
        # 较长英文
        "This is a longer English sentence that should be wrapped properly",
        # 中文
        "这是一段中文文本",
        # 较长中文
        "这是一段很长的中文文本，用来测试我们的多语言字幕换行算法是否有效",
        # 混合文本
        "Hello世界！This is a混合text测试。",
        # 包含标点符号
        "你好，世界！这是一个测试。",
        # 空文本
        "",
        # 只有空格
        "   ",
        # 单个字符
        "A",
        "中"
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n测试 {i}: '{text}'")
        try:
            result = processor.process_line(text)
            print(f"结果: '{result}'")
        except Exception as e:
            print(f"错误: {e}")

    print("\n所有测试完成！")


if __name__ == "__main__":
    test_various_texts()
