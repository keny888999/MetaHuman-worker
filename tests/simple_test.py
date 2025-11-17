#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试多语言字幕换行
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def main():
    """简单测试"""
    print("简单测试多语言字幕换行")
    print("=" * 30)

    # 创建处理器
    processor = AdvancedMultilingualSubtitleProcessor(358, 512, font_size=16)

    # 测试字符宽度计算
    print(f"最大视觉宽度: {processor.max_visual_width:.2f}")

    # 测试简单的文本处理
    test_text = "不过最绝的是——---我还能边喝咖啡边用脚趾头写代码."
    print(f"\n原文: {test_text}")

    result = processor.process_line(test_text)
    print(f"处理后: {result}")

    print("\n测试完成！")


if __name__ == "__main__":
    main()
