import pysubs2
import re
from math import ceil
from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def smart_wrap_by_resolution(input_file, output_file, video_width, video_height, font_size=None):
    """
    根据视频分辨率智能换行

    Args:
        input_file: 输入ASS文件路径
        output_file: 输出ASS文件路径
        video_width: 视频宽度
        video_height: 视频高度
        font_size: 字体大小(可选，自动计算如果未提供)
    """
    # 根据分辨率自动计算合适的参数

    processor = AdvancedMultilingualSubtitleProcessor(video_width=video_width, video_height=video_height, font_size=16)

    return processor.process_subtitle_file(input_file, "./output.ass")  # smart_wrap_text(clean_text, chars_per_line)

    if font_size is None:
        # 基于视频高度自动计算字体大小
        font_size = max(12, video_width // 40)

    ref_width = 358
    ref_height = 512
    ref_font_size = 16
    ref_chars_per_line = 14

    # 计算每行最大字符数（经验公式）
    font_size = 16

    subs = pysubs2.load(input_file)

    for line in subs:
        if not line.text.strip():
            continue

        # 移除现有的\N（避免重复）
        clean_text = line.text.replace('\\N', ' ')

        # 提取文本内容（去除ASS标签）
        text_content = re.sub(r'\{[^}]*\}', '', clean_text)

        wrapped_text = processor.process_line(text_content)  # smart_wrap_text(clean_text, chars_per_line)
        line.text = wrapped_text

    # 更新样式中的字体大小
    update_styles(subs, font_size, video_width, video_height)

    subs.save(output_file)
    print(f"处理完成: 视频分辨率{video_width}x{video_height}, 字体大小{font_size}px")


def calculate_chars_per_line(video_width, font_size):
    """根据视频宽度和字体大小计算每行字符数"""
    # 经验公式：每行字符数 ≈ (视频宽度 * 0.8) / (字体大小 * 0.6)
    # 假设中文字符近似正方形，0.6是宽度系数，0.8是边距系数
    return max(8, min(40, int((video_width * 0.8) / (font_size * 0.6))))


def smart_wrap_text(text, max_chars):
    """智能文本换行"""
    # 如果已经有ASS标签，需要特殊处理
    if '{' in text:
        return wrap_text_with_tags(text, max_chars)
    else:
        return wrap_plain_text(text, max_chars)


def wrap_plain_text(text, max_chars):
    """普通文本换行"""
    if len(text) <= max_chars:
        return text

    # 优先在标点符号处分行
    punctuation = '，。！？；,.;!? '
    lines = []
    current_line = ""

    for char in text:
        current_line += char
        if len(current_line) >= max_chars and char in punctuation:
            lines.append(current_line.strip())
            current_line = ""

    if current_line:
        lines.append(current_line.strip())

    if len(lines) == 1:
        # 如果没有自然断点，强制在最大字符数处分行
        return force_wrap_text(text, max_chars)

    return '\\N'.join(lines)


def force_wrap_text(text, max_chars):
    """强制换行（无合适标点时使用）"""
    lines = []
    for i in range(0, len(text), max_chars):
        lines.append(text[i:i + max_chars])
    return '\\N'.join(lines)


def wrap_text_with_tags(text, max_chars):
    """处理带ASS标签的文本换行"""
    # 简单的标签处理：在标签外换行
    lines = []
    current_line = ""
    in_tag = False
    tag_content = ""

    for char in text:
        if char == '{':
            in_tag = True
            tag_content = char
        elif char == '}' and in_tag:
            tag_content += char
            current_line += tag_content
            in_tag = False
            tag_content = ""
        elif in_tag:
            tag_content += char
        else:
            current_line += char
            # 检查是否需要换行
            clean_current = re.sub(r'\{[^}]*\}', '', current_line)
            if len(clean_current) >= max_chars and char in '，。！？；,.;!? ':
                lines.append(current_line.strip())
                current_line = ""

    if current_line:
        lines.append(current_line.strip())

    if len(lines) == 1 and len(re.sub(r'\{[^}]*\}', '', text)) > max_chars:
        # 需要强制换行但保持标签
        return force_wrap_with_tags(text, max_chars)

    return '\\N'.join(lines)


def force_wrap_with_tags(text, max_chars):
    """带ASS标签的强制换行"""
    # 简化处理：在标签外寻找合适位置换行
    clean_text = re.sub(r'\{[^}]*\}', '', text)
    if len(clean_text) <= max_chars:
        return text

    # 找到合适的换行位置
    split_pos = find_best_split_position(clean_text, max_chars)

    # 重建带标签的文本
    before_split = text[:split_pos]
    after_split = text[split_pos:]

    return before_split + '\\N' + after_split


def find_best_split_position(text, max_chars):
    """找到最佳的分割位置"""
    # 优先在标点后分割
    for i in range(min(max_chars + 10, len(text) - 1), max_chars - 10, -1):
        if i < len(text) and text[i] in '，。！？；,.;!? ':
            # 检查是否在标签内
            if not is_inside_tag(text, i):
                return i + 1  # 在标点后分割

    # 其次在字符边界分割
    for i in range(min(max_chars + 5, len(text)), max_chars - 5, -1):
        if not is_inside_tag(text, i):
            return i

    return max_chars


def is_inside_tag(text, position):
    """检查指定位置是否在ASS标签内"""
    open_braces = text.count('{', 0, position)
    close_braces = text.count('}', 0, position)
    return open_braces > close_braces


def update_styles(subs, font_size, video_width, video_height):
    """更新ASS样式以适应视频分辨率"""
    for style_name in subs.styles:
        style = subs.styles[style_name]
        # 更新字体大小
        style.fontsize = font_size
        # 根据视频分辨率调整边距
        style.marginl = max(20, video_width // 40)
        style.marginr = max(20, video_width // 40)
        style.marginv = max(10, video_height // 20)


# 使用示例
if __name__ == "__main__":
    # 示例1: 1080p视频

    if True:
        smart_wrap_by_resolution(
            "subtitle.ass",
            "output_1080p.ass",
            video_width=352,
            video_height=512,
            font_size=20  # 可选，不指定则自动计算
        )

    # 示例2: 720p视频
    if False:
        smart_wrap_by_resolution(
            "subtitle.ass",
            "output_720p.ass",
            video_width=384,
            video_height=512
            # 不指定font_size，自动计算
        )
