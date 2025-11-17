#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from sentence_timestamp_converter import (
    convert_word_to_sentence_timestamps,
    convert_with_custom_splitter
)


class TestSentenceTimestampConverter(unittest.TestCase):

    def setUp(self):
        """测试前的准备工作"""
        self.sample_data = [
            ["您", 0.075, 0.255], ["知", 0.255, 0.425], ["道", 0.425, 0.555], ["吗？", 0.555, 0.895],
            ["我", 1.095, 1.255], ["这", 1.255, 1.365], ["双", 1.365, 1.585], ["手", 1.585, 1.785],
            ["啊，", 1.785, 2.165], ["能", 2.245, 2.445], ["同", 2.445, 2.685], ["时", 2.685, 2.925],
            ["玩", 2.925, 3.105], ["转", 3.105, 3.335], ["五", 3.335, 3.525], ["种", 3.525, 3.705],
            ["乐", 3.705, 3.845], ["器。", 3.845, 4.115]
        ]

        self.expected_result = [
            {
                "text": "您知道吗？",
                "start": 0.075,
                "end": 0.895,
                "words": [["您", 0.075, 0.255], ["知", 0.255, 0.425], ["道", 0.425, 0.555], ["吗？", 0.555, 0.895]]
            },
            {
                "text": "我这双手啊，能同时玩转五种乐器。",
                "start": 1.095,
                "end": 4.115,
                "words": [["我", 1.095, 1.255], ["这", 1.255, 1.365], ["双", 1.365, 1.585], ["手", 1.585, 1.785],
                          ["啊，", 1.785, 2.165], ["能", 2.245, 2.445], ["同", 2.445, 2.685], ["时", 2.685, 2.925],
                          ["玩", 2.925, 3.105], ["转", 3.105, 3.335], ["五", 3.335, 3.525], ["种", 3.525, 3.705],
                          ["乐", 3.705, 3.845], ["器。", 3.845, 4.115]]
            }
        ]

    def test_basic_conversion(self):
        """测试基本转换功能"""
        result = convert_word_to_sentence_timestamps(self.sample_data)
        self.assertEqual(len(result), len(self.expected_result))

        for i, sentence_data in enumerate(result):
            expected_data = self.expected_result[i]
            self.assertEqual(sentence_data["text"], expected_data["text"])
            self.assertAlmostEqual(sentence_data["start"], expected_data["start"], places=3)
            self.assertAlmostEqual(sentence_data["end"], expected_data["end"], places=3)
            self.assertEqual(sentence_data["words"], expected_data["words"])

    def test_empty_input(self):
        """测试空输入"""
        result = convert_word_to_sentence_timestamps([])
        self.assertEqual(result, [])

    def test_invalid_data_format(self):
        """测试无效数据格式"""
        invalid_data = [["您", 0.075], ["知", 0.255, 0.425, 0.5]]  # 错误的数组长度
        result = convert_word_to_sentence_timestamps(invalid_data)
        # 应该忽略无效数据，但仍能处理有效数据
        self.assertEqual(len(result), 0)  # 因为没有完整的句子

    def test_custom_splitter(self):
        """测试自定义分隔符"""
        result = convert_with_custom_splitter(self.sample_data)
        self.assertEqual(len(result), len(self.expected_result))

        for i, sentence_data in enumerate(result):
            expected_data = self.expected_result[i]
            self.assertEqual(sentence_data["text"], expected_data["text"])
            self.assertAlmostEqual(sentence_data["start"], expected_data["start"], places=3)
            self.assertAlmostEqual(sentence_data["end"], expected_data["end"], places=3)
            # 注意：自定义分隔符函数的words字段可能略有不同，所以我们只检查文本和时间

    def test_no_ending_punctuation(self):
        """测试没有结束标点的句子"""
        data = [
            ["这", 0.0, 0.5], ["是", 0.5, 1.0], ["一个", 1.0, 1.5],
            ["没有", 1.5, 2.0], ["标点", 2.0, 2.5], ["的", 2.5, 3.0],
            ["句子", 3.0, 3.5]
        ]
        result = convert_word_to_sentence_timestamps(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "这是一个没有标点的句子")
        self.assertAlmostEqual(result[0]["start"], 0.0, places=3)
        self.assertAlmostEqual(result[0]["end"], 3.5, places=3)
        self.assertEqual(result[0]["words"], data)

    def test_multiple_punctuation_in_one_word(self):
        """测试一个词中包含多个标点符号"""
        data = [
            ["你好", 0.0, 1.0], ["世界", 1.0, 2.0], ["！！！", 2.0, 3.0]
        ]
        result = convert_word_to_sentence_timestamps(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "你好世界！！！")
        self.assertAlmostEqual(result[0]["start"], 0.0, places=3)
        self.assertAlmostEqual(result[0]["end"], 3.0, places=3)
        self.assertEqual(result[0]["words"], data)

    def test_comma_pause_and_char_limit(self):
        """测试逗号停顿和字符限制功能"""
        # 创建测试数据：一个长句子，中间有逗号，逗号后有较长停顿
        data = [
            ["这", 0.0, 0.5], ["是", 0.5, 1.0], ["一个", 1.0, 1.5],
            ["很长", 1.5, 2.0], ["的", 2.0, 2.5], ["句子，", 2.5, 3.0],  # 逗号后有1.5秒停顿
            ["但是", 4.5, 5.0], ["我们", 5.0, 5.5], ["把它", 5.5, 6.0],
            ["分开了。", 6.0, 6.5]
        ]

        # 使用逗号停顿阈值（1.0秒），应该在逗号处分割
        result = convert_word_to_sentence_timestamps(data, comma_pause_threshold=1.0, max_chars_per_sentence=50)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["text"], "这是一个很长的句子，")
        self.assertEqual(result[1]["text"], "但是我们把它分开了。")

        # 创建测试数据：一个长句子，字符数超过限制
        data2 = [
            ["这", 0.0, 0.1], ["是", 0.1, 0.2], ["一个", 0.2, 0.3],
            ["非", 0.3, 0.4], ["常", 0.4, 0.5], ["非", 0.5, 0.6],
            ["常", 0.6, 0.7], ["非", 0.7, 0.8], ["常", 0.8, 0.9],
            ["非", 0.9, 1.0], ["常", 1.0, 1.1], ["非", 1.1, 1.2],
            ["常", 1.2, 1.3], ["长", 1.3, 1.4], ["的", 1.4, 1.5],
            ["句", 1.5, 1.6], ["子", 1.6, 1.7], ["。", 1.7, 1.8]
        ]

        # 字符数超过限制（10个字符），应该分割
        result2 = convert_word_to_sentence_timestamps(data2, comma_pause_threshold=5.0, max_chars_per_sentence=10)
        # 由于没有逗号，不会分割，会作为一个句子
        self.assertEqual(len(result2), 1)

        # 创建测试数据：包含逗号且字符数超过限制
        data3 = [
            ["这", 0.0, 0.1], ["是", 0.1, 0.2], ["一个", 0.2, 0.3],
            ["非", 0.3, 0.4], ["常", 0.4, 0.5], ["非", 0.5, 0.6],
            ["常", 0.6, 0.7], ["非", 0.7, 0.8], ["常", 0.8, 0.9],
            ["非", 0.9, 1.0], ["常", 1.0, 1.1], ["非", 1.1, 1.2],
            ["常", 1.2, 1.3], ["长", 1.3, 1.4], ["的", 1.4, 1.5],
            ["句", 1.5, 1.6], ["子，", 1.6, 1.7],  # 逗号结尾且字符数超过限制
            ["但", 1.7, 1.8], ["是", 1.8, 1.9], ["还", 1.9, 2.0],
            ["有", 2.0, 2.1], ["更", 2.1, 2.2], ["多", 2.2, 2.3],
            ["内", 2.3, 2.4], ["容", 2.4, 2.5], ["。", 2.5, 2.6]
        ]

        # 字符数超过限制（10个字符），应该分割
        result3 = convert_word_to_sentence_timestamps(data3, comma_pause_threshold=5.0, max_chars_per_sentence=10)
        self.assertEqual(len(result3), 2)

    def test_comma_duration_threshold(self):
        """测试以逗号结尾句子的持续时间阈值功能"""
        # 创建测试数据：一个以逗号结尾的句子，持续时间超过阈值
        data = [
            ["这", 0.0, 0.5], ["是", 0.5, 1.0], ["一个", 1.0, 1.5],
            ["很长", 1.5, 2.0], ["的", 2.0, 2.5], ["句子，", 2.5, 3.5]  # 持续时间3.5秒，超过默认阈值3.0秒
        ]

        # 使用默认阈值（3.0秒），应该作为独立句子处理
        result = convert_word_to_sentence_timestamps(data, comma_duration_threshold=3.0)
        self.assertEqual(len(result), 1)  # 作为独立句子

        # 创建测试数据：一个更复杂的场景，包含两个句子
        data2 = [
            ["这", 0.0, 0.5], ["是", 0.5, 1.0], ["一个", 1.0, 1.5],
            ["很长", 1.5, 2.0], ["的", 2.0, 2.5], ["句子，", 2.5, 5.7],  # 持续时间3.2秒，超过阈值3.0秒
            ["但是", 5.7, 6.2], ["还有", 6.2, 6.7], ["更多", 6.7, 7.2],
            ["内容。", 7.2, 7.7]
        ]

        # 第一个句子持续时间3.2秒，超过阈值3.0秒，应该在逗号处分割
        result2 = convert_word_to_sentence_timestamps(data2, comma_duration_threshold=3.0)
        # 现在应该得到两个句子
        self.assertEqual(len(result2), 2)
        # 验证第一个句子
        self.assertEqual(result2[0]["text"], "这是一个很长的句子，")
        # 验证第二个句子
        self.assertEqual(result2[1]["text"], "但是还有更多内容。")


if __name__ == "__main__":
    unittest.main()
