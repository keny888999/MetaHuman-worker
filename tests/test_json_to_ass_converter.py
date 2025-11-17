#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 json_to_ass_converter 模块
"""

import os
import sys
import json
import tempfile
import unittest

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.json_to_ass_converter import json_to_ass, seconds_to_ass_timestamp


class TestJsonToAssConverter(unittest.TestCase):

    def setUp(self):
        """测试前准备"""
        # 创建临时JSON文件用于测试
        self.test_data = [
            {
                "text": "这是一个测试句子。",
                "start": 0.0,
                "end": 2.5
            },
            {
                "text": "这是另一个测试句子。",
                "start": 3.0,
                "end": 5.0
            }
        ]

        # 创建临时文件
        self.temp_json = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8')
        json.dump(self.test_data, self.temp_json, ensure_ascii=False, indent=2)
        self.temp_json.close()

        # 输出ASS文件路径
        self.temp_ass = tempfile.NamedTemporaryFile(suffix='.ass', delete=False)
        self.temp_ass.close()
        os.unlink(self.temp_ass.name)  # 删除空文件，让转换函数创建

    def tearDown(self):
        """测试后清理"""
        # 删除临时文件
        os.unlink(self.temp_json.name)
        if os.path.exists(self.temp_ass.name):
            os.unlink(self.temp_ass.name)

    def test_seconds_to_ass_timestamp(self):
        """测试时间戳转换函数"""
        self.assertEqual(seconds_to_ass_timestamp(0), "00:00:00.00")
        self.assertEqual(seconds_to_ass_timestamp(2.5), "00:00:02.50")
        self.assertEqual(seconds_to_ass_timestamp(3661.75), "01:01:01.75")

    def test_json_to_ass_conversion(self):
        """测试JSON到ASS的转换"""
        # 执行转换
        output_path = json_to_ass(
            json_file_path=self.temp_json.name,
            ass_file_path=self.temp_ass.name,
            title="Test Subtitle",
            font_name="Arial",
            font_size=12
        )

        # 检查输出文件是否存在
        self.assertTrue(os.path.exists(output_path))

        # 读取生成的ASS文件
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查ASS文件基本结构
        self.assertIn("[Script Info]", content)
        self.assertIn("[V4+ Styles]", content)
        self.assertIn("[Events]", content)

        # 检查是否包含字幕内容
        self.assertIn("这是一个测试句子。", content)
        self.assertIn("这是另一个测试句子。", content)

        # 检查时间戳
        self.assertIn("00:00:00.00,00:00:02.50", content)
        self.assertIn("00:00:03.00,00:00:05.00", content)


if __name__ == "__main__":
    unittest.main()
