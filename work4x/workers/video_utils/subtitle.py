#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级多语言字幕换行处理模块
支持中、英、日、韩等多种语言的智能换行

功能：
1. 根据视频分辨率和字体大小自动计算每行最大视觉宽度
2. 支持中、英、日、韩等多语言文本的智能换行
3. 提供基于视觉宽度和显示时间的字幕行分割功能
"""
from typing import Protocol, runtime_checkable
import pysubs2
import re
import unicodedata
import json
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json
from enum import Enum
from pydantic import BaseModel
from json import JSONEncoder


class EmployeeEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


@dataclass
class Test:
    a: str
    b: int


class LanguageType(Enum):
    """语言类型枚举"""
    CHINESE = "chinese"
    ENGLISH = "english"
    JAPANESE = "japanese"
    KOREAN = "korean"
    OTHER = "other"


@dataclass
class CharacterInfo:
    """字符信息"""
    char: str
    width: float
    language: LanguageType
    is_punctuation: bool
    is_break_punctuation: bool
    is_space: bool


@dataclass
class SubtitleSegment():
    """字幕片段信息"""
    text: str
    start: float
    end: float
    words: list[list] = None


@dataclass
class SegmentIndex:
    start: int
    end: int
    text: str


def dumps(obj, indent=None, ensure_ascii=False, **kwargs):
    return json.dumps(obj, ensure_ascii=ensure_ascii, indent=indent, ** kwargs, cls=EmployeeEncoder)


class SubtitleProcessor:
    """高级多语言字幕处理器"""

    def __init__(self, video_width: int, video_height: int, font_size: Optional[int] = None):
        self.video_width = video_width
        self.video_height = video_height
        self.font_size = font_size or 16

        # 计算每行最大视觉宽度
        self._calculate_max_visual_width()

        # 最小显示时间（秒）
        self.min_display_time = 1.0

    def _calculate_max_visual_width(self) -> float:
        """计算每行最大视觉宽度"""
        # 基于视频宽度和字体大小的经验公式
        import math

        ref_font_size = 16
        is_horiz = self.video_width >= self.video_height
        scale_factor = ref_font_size / self.font_size
        if is_horiz:
            self.max_visual_width = math.floor(22 * 1.8 * scale_factor)
        else:
            self.max_visual_width = math.floor(14 * 1.8 * scale_factor)

    def process_subtitle_file(self, input_file: str, output_file: str):
        """处理字幕文件"""
        subs = pysubs2.load(input_file)

        for line in subs:
            if line.text.strip():
                wrapped_text = self.process_line(line.text)
                line.text = wrapped_text

        # 更新样式
        self._update_styles(subs)

        subs.save(output_file)
        print(f"处理完成: 视频分辨率{self.video_width}x{self.video_height}, "
              f"字体大小{self.font_size}px, 最大视觉宽度{self.max_visual_width:.2f}")

    def process_line(self, text: str) -> str:
        """处理单行文本"""
        # 移除现有的换行符
        clean_text = text.replace('\\N', ' ')

        # 如果是带标签的文本
        if '{' in clean_text:
            return self._process_text_with_tags(clean_text)
        else:
            return self._process_plain_text(clean_text)

    def _process_plain_text(self, text: str) -> str:
        """处理纯文本"""
        if not text.strip():
            return text

        # 分析文本中的字符
        char_infos = self._analyze_text(text)

        # 检测主要语言
        primary_language = self._detect_primary_language(char_infos)

        # 根据主要语言选择换行策略
        if primary_language == LanguageType.CHINESE:
            return self._wrap_chinese_text(char_infos)
        elif primary_language == LanguageType.ENGLISH:
            return self._wrap_english_text(char_infos)
        else:
            return self._wrap_mixed_text(char_infos)

    def _process_text_with_tags(self, text: str) -> str:
        """处理带ASS标签的文本"""
        # 提取纯文本内容
        clean_text = re.sub(r'\{[^}]*\}', '', text)

        # 处理纯文本
        processed_clean_text = self._process_plain_text(clean_text)

        # 保留标签信息的简化处理
        # 在实际应用中，可能需要更复杂的标签保留逻辑
        if '{' in text:
            # 如果原文本包含标签，简单地返回处理后的纯文本
            # 更复杂的实现需要将标签重新插入到正确位置
            return processed_clean_text
        return processed_clean_text

    def _analyze_text(self, text: str) -> List[CharacterInfo]:
        """分析文本中的字符"""
        char_infos = []

        for char in text:
            width = self._get_char_visual_width(char)
            language = self._detect_char_language(char)
            is_punctuation = self._is_breakable_punctuation(char)
            is_break_punctuation = self._is_breakable_punctuation(char)
            is_space = char.isspace()

            char_infos.append(CharacterInfo(
                char=char,
                width=width,
                language=language,
                is_punctuation=is_punctuation,
                is_break_punctuation=is_break_punctuation,
                is_space=is_space
            ))

        return char_infos

    def _detect_char_language(self, char: str) -> LanguageType:
        """检测单个字符的语言"""
        # 中文字符
        if '\u4e00' <= char <= '\u9fff':
            return LanguageType.CHINESE

        # 日文平假名
        if '\u3040' <= char <= '\u309f':
            return LanguageType.JAPANESE

        # 日文片假名
        if '\u30a0' <= char <= '\u30ff':
            return LanguageType.JAPANESE

        # 韩文
        if '\uac00' <= char <= '\ud7af':
            return LanguageType.KOREAN

        # 英文字母
        if char.isascii() and char.isalpha():
            return LanguageType.ENGLISH

        return LanguageType.OTHER

    def _detect_primary_language(self, char_infos: List[CharacterInfo]) -> LanguageType:
        """检测文本的主要语言"""
        if not char_infos:
            return LanguageType.OTHER

        # 统计各种语言字符的数量
        language_counts = {
            LanguageType.CHINESE: 0,
            LanguageType.ENGLISH: 0,
            LanguageType.JAPANESE: 0,
            LanguageType.KOREAN: 0,
            LanguageType.OTHER: 0
        }

        total_chars = 0
        for info in char_infos:
            # 只统计非空格、非标点的字符
            if not info.is_space and not info.is_punctuation:
                language_counts[info.language] += 1
                total_chars += 1

        if total_chars == 0:
            return LanguageType.OTHER

        # 计算各语言占比
        language_ratios = {
            lang: count / total_chars
            for lang, count in language_counts.items()
        }

        # 根据阈值判断主要语言
        for lang, threshold in self.language_thresholds.items():
            if language_ratios.get(lang, 0) >= threshold:
                return lang

        # 默认返回英文
        return LanguageType.ENGLISH

    def _get_char_visual_width(self, char: str) -> float:
        """获取字符的视觉宽度"""
        # 确保只传递单个字符给 unicodedata.category
        if len(char) != 1:
            return 1.5  # 默认宽度

        # 控制字符宽度为0
        if unicodedata.category(char).startswith('C'):
            return 0.0

        # 空格
        if char.isspace():
            return 1.0

        # 英文字母和数字
        if char.isascii() and (char.isalpha() or char.isdigit()):
            return 1.0

        # 英文标点符号
        if char in ".,!?;:-":
            return 0.5

        # 中日韩字符通常是方块字符
        if ('\u4e00' <= char <= '\u9fff' or  # 中文
            '\u3040' <= char <= '\u309f' or  # 日文平假名
            '\u30a0' <= char <= '\u30ff' or  # 日文片假名
                '\uac00' <= char <= '\ud7af'):   # 韩文
            return 2.0

        # 拉丁文扩展字符
        if '\u0100' <= char <= '\u017f':  # 拉丁文扩展-A
            return 1.0

        # 其他Unicode字符默认宽度
        return 1.5

    def is_punctuation(self, char: str):
        """判断字符是否是可以换行的标点符号"""
        # 英文标点
        english_punctuation = ".,!?;:-"

        # 中文标点
        chinese_punctuation = "，。！？；：、"

        # 其他语言标点
        other_punctuation = "{}[]~'\"`#$%^&*|"

        all_punctuation = english_punctuation + chinese_punctuation + other_punctuation

        return char in all_punctuation

    def _is_breakable_punctuation(self, char: str) -> bool:
        """判断字符是否是可以换行的标点符号"""
        # 英文标点
        english_punctuation = ".,!?;:-"

        # 中文标点
        chinese_punctuation = "，。！？；：、"

        # 其他语言标点
        other_punctuation = ""

        all_punctuation = english_punctuation + chinese_punctuation + other_punctuation

        return char in all_punctuation

    def _update_styles(self, subs: pysubs2.SSAFile):
        """更新ASS样式以适应视频分辨率"""
        for style_name in subs.styles:
            style = subs.styles[style_name]
            # 更新字体大小
            style.fontsize = self.font_size
            # 根据视频分辨率调整边距
            style.marginl = max(20, self.video_width // 40)
            style.marginr = max(20, self.video_width // 40)
            style.marginv = max(10, self.video_height // 20)

    def _is_text_exceed_width(self, text: str) -> bool:
        """判断文本是否超出最大视觉宽度"""
        char_infos = self._analyze_text(text)
        total_width = sum(info.width for info in char_infos)
        return total_width > self.max_visual_width

    def _split_text_by_comma(self, text: str, words: List[List]) -> List[SegmentIndex]:
        """
        根据逗号或顿号分割文本

        Args:
            text: 要分割的文本

        Returns:
            分割后的文本片段列表
        """

        # print(f"len={len(text)}")

        # 使用正则表达式分割，保留分隔符
        parts = re.split(r'([，、,？])', text)

        # 合并分割后的部分，确保标点符号与前面的文本在一起
        segments = []
        current_segment = ""

        for part in parts:
            if part in ["，", "、", ",", "?", "？"]:
                current_segment += part
                segments.append(current_segment)
                current_segment = ""
            else:
                current_segment += part

        # 添加最后一段（如果没有以标点符号结尾）
        if current_segment:
            segments.append(current_segment)

        # 清理每段文本（去除首尾空格）会否丢失index索引？暂时不处理
        # segments = [seg.strip() for seg in segments if seg.strip()]

        result = []
        start_index = 0
        for (index, text) in enumerate(segments):
            _start, _end = self.findRangeFromWords(text, start=start_index, words=words)
            data = SegmentIndex(start=_start, end=_end, text=text)
            start_index = _end + 1
            result.append(data)

        return result

    def findRangeFromWords(self, text: str, start: int, words: list[list]):
        line = ""
        for i in range(start, len(words)):
            line = line + words[i][0]
            if text == line:
                return start, i

        return -1, -1

    def merge_seginfos(self, arr: list[SegmentIndex], words: list[list]) -> SubtitleSegment:
        txt = "".join([seg.text for seg in arr])
        start_index = arr[0].start
        end_index = arr[-1].end
        start_time = words[start_index][1]
        end_time = words[end_index][2]
        return SubtitleSegment(
            text=txt,
            start=start_time,
            end=end_time,
            # words=None
            words=words[start_index:end_index + 1]
        )

    def _auto_add_CRLF(self, segment: SubtitleSegment):
        text = str(segment.text)
        arr = []
        index = len(text)
        while index > 0 and len(text) > 1:
            if not self._is_text_exceed_width(text[:index]):
                sub_text = text[:index]
                text = text[index:]
                if (text in [',', '，', '!', '！', '、', '?', '？']):
                    sub_text = sub_text + text
                    arr.append(sub_text)
                    text = ""
                    break

                arr.append(sub_text)
                index = len(text)
            else:
                index -= 1

        if len(text) > 0:
            arr.append(text)

        segment.text = "\n".join(arr)

    def _cut_by_comma(self, segment: SubtitleSegment):
        result_segments = []
        text = segment.text
        start = segment.start
        end = segment.end
        words = segment.words

        left_exceed_count = 0

        # 判断是否超出屏幕宽度
        if not self._is_text_exceed_width(text):
            # 未超出宽度，直接添加
            # 保留原始的words字段
            result_segments.append(segment)
            return result_segments, 0

        # 以逗号分割成几组
        split_segments = self._split_text_by_comma(text, words=words)
        if len(split_segments) < 2:
            self._auto_add_CRLF(segment)
            result_segments.append(segment)
            return result_segments, 0

        segment_copy = split_segments.copy()
        sub_pool = []  # 砍掉的组放在这里,待处理

        while len(segment_copy) > 1:
            sub_pool.append(segment_copy.pop())  # 砍掉最后一组,放进待处理的组
            txt = "".join([item.text for item in segment_copy])  # 拼接字符串
            if not self._is_text_exceed_width(txt):
                new_seg = self.merge_seginfos(segment_copy, words)
                result_segments.append(new_seg)
                segment_copy.clear()
                break

        if len(segment_copy) > 0:
            new_seg = self.merge_seginfos(segment_copy, words)
            if self._is_text_exceed_width(new_seg.text):
                left_exceed_count += 1

            result_segments.append(new_seg)

        if len(sub_pool) > 0:
            sub_pool.reverse()
            new_seg = self.merge_seginfos(sub_pool, words)
            if self._is_text_exceed_width(new_seg.text):
                left_exceed_count += 1

            result_segments.append(new_seg)

        # 递归检查
        if left_exceed_count > 0:
            left_exceed_count = 0
            new_results = []
            for seg in result_segments:
                rs, c = self._cut_by_comma(seg)
                left_exceed_count += c
                new_results.extend(rs)

            result_segments = new_results

        return result_segments, left_exceed_count

    def split_subtitle(self, input_json_file: str, output_json_file: str):

        # 读取输入JSON文件
        with open(input_json_file, 'r', encoding='utf-8') as f:
            segments = json.load(f)

        # 处理后的结果
        result_segments = []

        # 遍历每一行字幕记录
        for segment in segments:
            sub = SubtitleSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"],
                words=segment["words"]
            )
            new_segmens, left_exceeds = self._cut_by_comma(sub)
            result_segments.extend(new_segmens)

        # s = dumps(result_segments, indent=2)
        # print(s)

        with open(output_json_file, "w", encoding="utf8") as f:
            arr = []
            for r in result_segments:
                _dict = r.__dict__
                del _dict["words"]
                arr.append(_dict)
            s = dumps(arr, indent=2)
            f.write(s)
        return result_segments


# 使用示例
if __name__ == "__main__":
    video_width = 358
    video_height = 512

    # if True:
    #    exit()

    # 处理ASS字幕文件
    processor = SubtitleProcessor(video_width=video_width, video_height=video_height, font_size=16)
    processor.split_subtitle(r"test\sentences_1214.json", "./1111111111.json")

    # 处理JSON字幕文件
    # split_subtitle_json_by_comma(
    #    'sentences_output.json',
    #    './sentences_output_split.json',
    #    video_width=video_width,
    #    video_height=video_height,
    #    font_size=16
    # )

    # 新增功能：处理JSON字幕文件，仅在有逗号或顿号且超出宽度时进行分割
    # json_file = r"test\sentences_1214.json"
    '''split_subtitle_with_width_control(
        json_file,
        './test/outputs/output.json',
        video_width=video_width,
        video_height=video_height,
        font_size=16
    )
    '''
