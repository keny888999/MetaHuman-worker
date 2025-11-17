#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多语言字幕换行测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_multilingual_subtitle import (
    MultilingualTextWrapper,
    get_char_visual_width,
    is_breakable_punctuation,
    multilingual_wrap_plain_text
)


def test_character_widths():
    """测试字符宽度计算"""
    print("=== 字符宽度测试 ===")

    test_chars = [
        ('A', "英文大写字母"),
        ('a', "英文小写字母"),
        ('中', "中文汉字"),
        ('。', "中文句号"),
        ('.', "英文句号"),
        ('ひ', "日文平假名"),
        ('カ', "日文片假名"),
        ('한', "韩文"),
        ('é', "拉丁文扩展字符"),
        (' ', "空格"),
    ]

    for char, description in test_chars:
        width = get_char_visual_width(char)
        print(f"'{char}' ({description}): {width}")


def test_punctuation_detection():
    """测试标点符号检测"""
    print("\n=== 标点符号检测测试 ===")

    test_chars = [
        '.', ',', '!', '?', ';', ':', '-',
        '。', '，', '！', '？', '；', '：', '、',
        '(', ')', '[', ']', '{', '}'
    ]

    for char in test_chars:
        is_breakable = is_breakable_punctuation(char)
        print(f"'{char}': {'可换行' if is_breakable else '不可换行'}")


def test_text_wrapping():
    """测试文本换行"""
    print("\n=== 文本换行测试 ===")

    # 测试中文文本
    chinese_text = "这是一段很长的中文文本，用来测试我们的多语言字幕换行算法是否有效。"
    print(f"原文: {chinese_text}")
    wrapped_chinese = multilingual_wrap_plain_text(chinese_text, 20)
    print(f"换行后: {wrapped_chinese}")

    # 测试英文文本
    english_text = "This is a long English sentence used to test our multilingual subtitle wrapping algorithm."
    print(f"\n原文: {english_text}")
    wrapped_english = multilingual_wrap_plain_text(english_text, 20)
    print(f"换行后: {wrapped_english}")

    # 测试混合文本
    mixed_text = "Hello世界！This is a混合text测试。Mixed languages are challenging, aren't they?"
    print(f"\n原文: {mixed_text}")
    wrapped_mixed = multilingual_wrap_plain_text(mixed_text, 20)
    print(f"换行后: {wrapped_mixed}")


def test_advanced_wrapper():
    """测试高级换行器"""
    print("\n=== 高级换行器测试 ===")

    wrapper = MultilingualTextWrapper(max_width=30.0)

    # 测试多语言混合文本
    text = """这是一个多语言测试。
This is an English test.
これは日本語のテストです。
이것은 한국어 테스트입니다.
Mixed content: Hello世界！"""

    lines = wrapper.wrap_text(text)
    print("换行结果:")
    for i, line in enumerate(lines, 1):
        print(f"{i:2d}. {line}")


def main():
    """主测试函数"""
    print("多语言字幕换行算法测试")
    print("=" * 50)

    test_character_widths()
    test_punctuation_detection()
    test_text_wrapping()
    test_advanced_wrapper()

    print("\n测试完成！")


if __name__ == "__main__":
    main()
