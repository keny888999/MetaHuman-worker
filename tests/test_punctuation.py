#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试标点符号保留功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def main():
    """测试标点符号保留"""
    print("测试标点符号保留功能")
    print("=" * 25)

    # 创建处理器
    processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)

    # 测试包含各种标点符号的文本
    test_cases = [
        "你好，世界！",
        "Hello, World!",
        "Hello世界！This is a混合text测试。",
        "これは日本語のテストです。",
        "이것은 한국어 테스트입니다."
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n测试 {i}: '{text}'")
        try:
            result = processor.process_line(text)
            print(f"结果: '{result}'")

            # 检查是否保留了关键标点符号
            original_punctuation = set(char for char in text if char in "，。！？；：、,.!?;:-")
            result_punctuation = set(char for char in result if char in "，。！？；：、,.!?;:-")

            if original_punctuation.issubset(result_punctuation):
                print("✓ 标点符号正确保留")
            else:
                print("✗ 标点符号可能丢失")
                print(f"  原始标点: {original_punctuation}")
                print(f"  结果标点: {result_punctuation}")

        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n测试完成！")


if __name__ == "__main__":
    main()
