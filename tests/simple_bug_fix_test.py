#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试修复后的多语言字幕换行功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def main():
    """简单测试"""
    print("简单测试修复后的多语言字幕换行功能")
    print("=" * 30)

    try:
        # 创建处理器
        processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)

        # 测试简单的文本处理
        test_text = "你好，世界！Hello, World!"
        print(f"原文: {test_text}")

        result = processor.process_line(test_text)
        print(f"处理后: {result}")

        # 检查标点符号是否保留
        if "，" in result and "！" in result and "," in result:
            print("✓ 标点符号正确保留")
        else:
            print("✗ 标点符号可能丢失")

        print("\n测试完成！")

    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
