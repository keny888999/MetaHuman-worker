#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单最终测试
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.workers.video_utils.subtitle import SubtitleProcessor


def test_simple_final():
    """简单最终测试"""
    # 创建处理器实例
    processor = SubtitleProcessor(video_width=100, video_height=100, font_size=16)

    # 测试文本
    test_text = "这是测试文本，包含逗号分割。"

    # 测试智能分割方法
    result = processor._intelligent_split_text(test_text)
    print(f"分割结果: {result}")
    print(f"片段数: {len(result)}")


if __name__ == "__main__":
    test_simple_final()
