import os
import sys
import platform
import subprocess

CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)
sys.path.append(os.path.join(CURR_PATH, '..'))
sys.path.append(os.path.join(CURR_PATH, '..', '..'))

# 这句于要提前
from WorkerApp import App, WorkerHelper, ROOT_PATH


from work4x.utils.logger import logger
from work4x.utils.file import upload_oss, download_temp_file, FileType
from video_utils.json_to_ass_converter import json_to_ass
from work4x.workers.video_utils.subtitle import SubtitleProcessor
from work4x.config import FILE_TEMP_DIR


def merge_video_with_subtitles(video_path: str, subtitle_path: str, output_path: str) -> bool:
    """
    使用FFmpeg将MP4视频与字幕文件合并

    Args:
        video_path (str): 视频文件路径
        subtitle_path (str): 字幕文件路径
        output_path (str): 输出文件路径

    Returns:
        bool: 合并是否成功
    """
    try:
        # 构建FFmpeg命令
        # 使用字幕流覆盖在视频上
        cmd = [
            'ffmpeg',
            '-i', video_path,           # 输入视频文件
            '-vf', f'subtitles={subtitle_path}',  # 使用字幕滤镜
            '-c:a', 'copy',             # 音频流直接复制
            '-y',                       # 覆盖输出文件
            output_path                 # 输出文件路径
        ]

        # 执行FFmpeg命令
        print(" ".join(cmd))
        result = subprocess.run(cmd)
        print(f"return code={result.returncode}")

        # 检查输出文件是否存在
        if result.returncode == 0 and os.path.exists(output_path):
            logger.info(f"视频与字幕合并成功: {output_path}")
            return True
        else:
            logger.error("FFmpeg执行错误")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg执行失败: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"合并视频与字幕时发生错误: {str(e)}")
        return False


def merge_video_with_subtitles_soft(video_path: str, subtitle_path: str, output_path: str) -> bool:
    """
    使用FFmpeg将MP4视频与字幕文件合并（软字幕方式）
    将字幕作为单独的流添加到视频中，而不是直接渲染到画面上

    Args:
        video_path (str): 视频文件路径
        subtitle_path (str): 字幕文件路径
        output_path (str): 输出文件路径

    Returns:
        bool: 合并是否成功
    """
    try:
        # 构建FFmpeg命令
        # 添加字幕流到视频中
        cmd = [
            'ffmpeg',
            '-i', video_path,           # 输入视频文件
            '-i', subtitle_path,        # 输入字幕文件
            '-c', 'copy',               # 直接复制所有流
            '-c:s', 'mov_text',         # 字幕编码为mov_text (适用于MP4)
            '-y',                       # 覆盖输出文件
            output_path                 # 输出文件路径
        ]

        # 执行FFmpeg命令
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # 检查输出文件是否存在
        if os.path.exists(output_path):
            logger.info(f"视频与字幕软合并成功: {output_path}")
            return True
        else:
            logger.error("FFmpeg执行完成但输出文件不存在")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg执行失败: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"合并视频与字幕时发生错误: {str(e)}")
        return False


def merge_subtitle(subtitle_url: str, video_path, video_width, video_height, save_path):
    subtitle_path = download_temp_file(subtitle_url)
    font_size = 16
    processor = SubtitleProcessor(video_width=video_width, video_height=video_height, font_size=font_size)
    processor.split_subtitle(subtitle_path, subtitle_path)

    subtitle_ass = os.path.join(FILE_TEMP_DIR, os.path.basename(subtitle_path).replace(".json", ".ass"))
    json_to_ass(
        subtitle_path,
        subtitle_ass,
        font_name="Microsoft YaHei",
        font_size=font_size,
        outline=1,
    )

    if platform.system() == 'Windows':
        subtitle_ass = subtitle_ass.replace("\\", "/")
        arr = subtitle_ass.split(":")
        subtitle_ass = f"{arr[0]}\\\:{arr[1]}"

    success = merge_video_with_subtitles(video_path, subtitle_ass, save_path)
    if (not success):
        raise Exception("merge failed")
    return success


if __name__ == "__main__":
    cn = "http://dev.oss.work4x.com/work4x/json/20251220/sentences_1766196352862365_1766196352881.json"
    en = "http://dev.oss.work4x.com/work4x/json/20251221/sentences_644_1766283613559.json"
    subtitle_path = download_temp_file(en)
    font_size = 16
    processor = SubtitleProcessor(video_width=960, video_height=1920, font_size=font_size)
    processor.split_subtitle(subtitle_path, "./112233.json")
