#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证死循环修复的测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def main():
    """简单测试"""
    print("验证死循环修复")
    print("=" * 20)

    try:
        # 创建处理器
        processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)

        # 测试简单的英文文本处理
        test_text = "Hello world this is a test"
        print(f"原文: {test_text}")

        result = processor.process_line(test_text)
        print(f"处理后: {result}")

        print("\n测试完成！没有出现死循环。")

    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
