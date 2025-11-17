#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级多语言字幕换行测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import (
    AdvancedMultilingualSubtitleProcessor,
    CharacterInfo,
    LanguageType
)


def test_language_detection():
    """测试语言检测功能"""
    print("=== 语言检测测试 ===")

    processor = AdvancedMultilingualSubtitleProcessor(1280, 720)

    test_cases = [
        ("Hello world", "英文文本"),
        ("你好世界", "中文文本"),
        ("こんにちは", "日文文本"),
        ("안녕하세요", "韩文文本"),
        ("Hello世界！こんにちは안녕", "混合文本"),
    ]

    for text, description in test_cases:
        char_infos = processor._analyze_text(text)
        primary_lang = processor._detect_primary_language(char_infos)
        print(f"{description}: '{text}' -> 主要语言: {primary_lang.value}")


def test_character_analysis():
    """测试字符分析功能"""
    print("\n=== 字符分析测试 ===")

    processor = AdvancedMultilingualSubtitleProcessor(1280, 720)

    text = "Hello世界！こんにちは안녕"
    char_infos = processor._analyze_text(text)

    print(f"分析文本: '{text}'")
    for info in char_infos:
        print(f"  '{info.char}' -> 宽度: {info.width}, 语言: {info.language.value}, "
              f"标点: {info.is_punctuation}, 空格: {info.is_space}")


def test_text_wrapping():
    """测试文本换行功能"""
    print("\n=== 文本换行测试 ===")

    processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)

    test_cases = [
        "这是一段很长的中文文本，用来测试我们的多语言字幕换行算法是否有效。",
        "This is a long English sentence used to test our multilingual subtitle wrapping algorithm.",
        "Hello世界！This is a混合text测试。Mixed languages are challenging, aren't they?",
        "こんにちは、これは日本語のテストです。This is a test in Japanese.",
        "안녕하세요, 이것은 한국어 테스트입니다. This is a test in Korean.",
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {text}")
        wrapped = processor.process_line(text)
        print(f"换行结果: {wrapped}")


def test_visual_width_calculation():
    """测试视觉宽度计算"""
    print("\n=== 视觉宽度计算测试 ===")

    processor = AdvancedMultilingualSubtitleProcessor(1280, 720, font_size=16)
    print(f"视频分辨率: 1280x720")
    print(f"字体大小: 16px")
    print(f"最大视觉宽度: {processor.max_visual_width:.2f}")

    # 测试不同文本的视觉宽度
    test_texts = [
        "中文测试",
        "English test",
        "こんにちは",
        "Mixed混合text"
    ]

    for text in test_texts:
        char_infos = processor._analyze_text(text)
        total_width = sum(info.width for info in char_infos)
        print(f"'{text}' -> 总视觉宽度: {total_width:.2f}")


def main():
    """主测试函数"""
    print("高级多语言字幕换行算法测试")
    print("=" * 50)

    test_language_detection()
    test_character_analysis()
    test_visual_width_calculation()
    test_text_wrapping()

    print("\n测试完成！")


if __name__ == "__main__":
    main()
