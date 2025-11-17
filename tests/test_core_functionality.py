#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试核心功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.workers.video_utils.subtitle import SubtitleProcessor


def test_core():
    """测试核心功能"""
    # 创建处理器实例
    processor = SubtitleProcessor(video_width=100, video_height=100, font_size=16)

    # 简单测试
    text = "这是测试文本"
    result = processor._intelligent_split_text(text)
    print(f"简单文本分割结果: {result}")


if __name__ == "__main__":
    test_core()
