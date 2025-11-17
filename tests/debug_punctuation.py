#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试标点符号处理
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor, CharacterInfo, LanguageType


def debug_text_processing():
    """调试文本处理过程"""
    print("调试标点符号处理过程")
    print("=" * 30)
    
    # 创建处理器
    processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)
    
    # 测试文本
    text = "Hello, World!"
    print(f"原始文本: '{text}'")
    
    # 分析文本
    char_infos = processor._analyze_text(text)
    print("\n字符分析结果:")
    for i, info in enumerate(char_infos):
        print(f"  {i}: '{info.char}' - 宽度: {info.width}, 语言: {info.language.value}, "
              f"标点: {info.is_punctuation}, 空格: {info.is_space}")
    
    # 检测主要语言
    primary_language = processor._detect_primary_language(char_infos)
    print(f"\n主要语言: {primary_language.value}")
    
    # 处理文本
    result = processor.process_line(text)
    print(f"\n处理结果: '{result}'")


if __name__ == "__main__":
    debug_text_processing()