#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试修复后的多语言字幕换行功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def test_chinese_text():
    """测试中文文本处理"""
    print("=== 测试中文文本处理 ===")
    processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)

    # 测试文本
    text = "这是一段很长的中文文本，用来测试我们的多语言字幕换行算法是否有效。"
    print(f"原文: {text}")

    result = processor.process_line(text)
    print(f"处理后: {result}")
    print()


def test_english_text():
    """测试英文文本处理"""
    print("=== 测试英文文本处理 ===")
    processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)

    # 测试文本
    text = "This is a long English sentence used to test our multilingual subtitle wrapping algorithm."
    print(f"原文: {text}")

    result = processor.process_line(text)
    print(f"处理后: {result}")
    print()


def test_mixed_text():
    """测试混合文本处理"""
    print("=== 测试混合文本处理 ===")
    processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)

    # 测试文本
    text = "Hello世界！This is a混合text测试。Mixed languages are challenging, aren't they?"
    print(f"原文: {text}")

    result = processor.process_line(text)
    print(f"处理后: {result}")
    print()


def test_punctuation_preservation():
    """测试标点符号保留"""
    print("=== 测试标点符号保留 ===")
    processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)

    # 测试文本
    text = "你好，世界！这是一个测试。"
    print(f"原文: {text}")

    result = processor.process_line(text)
    print(f"处理后: {result}")

    # 检查标点符号是否保留
    if "，" in result and "！" in result and "。" in result:
        print("✓ 标点符号正确保留")
    else:
        print("✗ 标点符号丢失")
    print()


def main():
    """主测试函数"""
    print("多语言字幕换行BUG修复测试")
    print("=" * 40)

    try:
        test_chinese_text()
        test_english_text()
        test_mixed_text()
        test_punctuation_preservation()

        print("所有测试完成！")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
