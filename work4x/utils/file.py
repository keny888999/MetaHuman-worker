from venv import logger
import requests
import pyvips
import os
import sys
from urllib.parse import urlparse
import math
import random
import mimetypes
import re
import time

from enum import Enum
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from work4x.config import OSS_UPLOAD_URL, FILE_TEMP_DIR


class FileType(Enum):
    PICS = "pics"
    AUDIO = "audio"
    VIDEO = "video"
    JSON = "json"


def upload_oss(file_path: str, type: FileType):
    headers = {"Tenant-Id": "1"}
    filename = os.path.basename(file_path)
    mime, enc = mimetypes.guess_type(file_path)

    files = {"file": (filename, open(file_path, 'rb'), mime)}
    logger.info(f"正在上传..{filename}")
    rs = requests.post(OSS_UPLOAD_URL + type.value, headers=headers, files=files)  # type: ignore
    rs.raise_for_status()  # 检查请求是否成功
    js = rs.json()
    logger.info(f"{js}")
    return js["data"]


def upload_oss_url(url: str, type: FileType):
    file_path = download_temp_file(url)
    return upload_oss(file_path, type)


def download_file(url: str, save_path, retry_count=3):

    try_count = 0
    while try_count < retry_count:
        time.sleep(1)
        try:
            logger.info("正在下载: " + url)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, stream=True, timeout=10, headers=headers)
            response.raise_for_status()  # 检查请求是否成功
            break
        except Exception as e:
            logger.error("download_file failed")
            if try_count < retry_count:
                logger.info("retry..." + str(try_count))
                try_count += 1
                time.sleep(1)
                continue
            else:
                raise e

    with open(save_path, "wb") as f:
        f.write(response.content)

    return response.headers


def remove_file(file_path: str):
    try:
        os.unlink(file_path)
        return True
    except Exception as e:
        logger.error("remove_file failed:" + str(e))
        return False


def download_temp_file(url: str):
    now = datetime.now()
    t = now.strftime("%Y%m%d%H%M%S") + "_{:03d}_{:04d}".format(now.microsecond // 1000, random.randrange(100, 10000))
    filename = f"{t}.tmp"
    save_path = os.path.join(FILE_TEMP_DIR, filename)
    headers = download_file(url, save_path=save_path)

    # 获取 Content-Type 确立扩展名
    content_type = headers.get('Content-Type', '').split(';')[0]

    # ('application/json', none)
    if content_type.find(r"('") == 0:
        m = re.findall(r"\('(.*?)'", content_type)
        content_type = m[0]

    # 使用 mimetypes 猜测扩展名
    extension = mimetypes.guess_extension(content_type) or ""
    new_path = save_path.replace(".tmp", extension)
    os.rename(save_path, new_path)

    return new_path


def download_resize_save(image_url, output_path, max_pixels=None, width=None, height=None, quality=85):
    """
    下载图像、进行缩放并保存到本地

    Args:
        image_url: 图像URL地址
        output_path: 输出文件路径
        max_pixels: 最大像素限制（可选）
        width: 目标宽度（可选）
        height: 目标高度（可选）
        quality: 输出图像质量（1-100）
    """
    try:

        # 1. 下载图像
        logger.info(f"正在下载图像: {image_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(image_url, stream=True, timeout=10, headers=headers)
        response.raise_for_status()  # 检查请求是否成功

        # 2. 将图像数据加载到pyvips
        image_data = response.content
        image = pyvips.Image.new_from_buffer(image_data, "")

        logger.info(f"原始尺寸: {image.width} x {image.height} ({image.width * image.height:,} 像素)")

        # 3. 根据参数进行缩放
        if max_pixels:
            # 基于总像素限制缩放
            current_pixels = image.width * image.height
            if current_pixels > max_pixels:
                scale_factor = math.sqrt(max_pixels / current_pixels)
                image = image.resize(scale_factor, kernel="cubic")
                logger.info(f"按像素限制缩放至: {image.width} x {image.height}")

        elif width and height:
            # 精确尺寸缩放（可能改变宽高比）
            scale_x = width / image.width
            scale_y = height / image.height
            image = image.resize(scale_x, vscale=scale_y, kernel="cubic")
            logger.info(f"缩放至精确尺寸: {width} x {height}")

        elif width:
            # 按宽度等比缩放
            scale_factor = width / image.width
            image = image.resize(scale_factor, kernel="cubic")
            logger.info(f"按宽度缩放至: {width} x {int(image.height * scale_factor)}")

        elif height:
            # 按高度等比缩放
            scale_factor = height / image.height
            image = image.resize(scale_factor, kernel="cubic")
            logger.info(f"按高度缩放至: {int(image.width * scale_factor)} x {height}")

        # 4. 保存图像
        # 根据输出文件扩展名选择保存格式
        file_ext = os.path.splitext(output_path)[1].lower()

        save_options = {}
        if file_ext in ['.jpg', '.jpeg']:
            save_options = {'Q': quality, 'optimize_coding': True, 'strip': True}
        elif file_ext == '.png':
            save_options = {'compression': 9, 'strip': True}

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        image.write_to_file(output_path, **save_options)
        logger.info(f"图像已保存至: {output_path}")
        logger.info(f"最终尺寸: {image.width} x {image.height} ({image.width * image.height:,} 像素)")

        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"下载失败: {e}")
        return False

    except Exception as e:
        logger.error(f"处理图像时出错: {e}")
        return False

# 高级版本：支持更多选项


def download_and_process_image(image_url, output_path,
                               max_pixels=None,
                               width=None,
                               height=None,
                               keep_aspect_ratio=True,
                               kernel="cubic",
                               quality=85,
                               timeout=30,
                               headers=None):
    """
    高级图像下载和处理函数

    Args:
        keep_aspect_ratio: 是否保持宽高比
        kernel: 缩放算法 ("nearest", "linear", "cubic", "lanczos2", "lanczos3")
        timeout: 下载超时时间（秒）
        headers: 自定义请求头
    """
    try:
        # 设置默认请求头（模拟浏览器）
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

        logger.info(f"下载: {image_url}")
        response = requests.get(image_url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        # 从内存加载图像
        image = pyvips.Image.new_from_buffer(response.content, "")
        original_size = f"{image.width}x{image.height}"
        logger.info(f"原始尺寸: {original_size}")

        # 计算目标尺寸
        target_width, target_height = image.width, image.height

        if max_pixels:
            current_pixels = image.width * image.height
            if current_pixels > max_pixels:
                scale = math.sqrt(max_pixels / current_pixels)
                target_width = int(image.width * scale)
                target_height = int(image.height * scale)

        elif width and height:
            if keep_aspect_ratio:
                # 保持宽高比，选择较小的缩放比例
                scale_x = width / image.width
                scale_y = height / image.height
                scale = min(scale_x, scale_y)
                target_width = int(image.width * scale)
                target_height = int(image.height * scale)
            else:
                target_width, target_height = width, height

        elif width:
            scale = width / image.width
            target_height = int(image.height * scale)
            target_width = width

        elif height:
            scale = height / image.height
            target_width = int(image.width * scale)
            target_height = height

        # 执行缩放（如果尺寸有变化）
        if target_width != image.width or target_height != image.height:
            scale_x = target_width / image.width
            scale_y = target_height / image.height

            if keep_aspect_ratio and scale_x != scale_y:
                # 使用缩略图方法保持宽高比
                image = image.thumbnail_image(target_width, height=target_height, crop=False)
            else:
                # 使用resize方法
                image = image.resize(scale_x, vscale=scale_y, kernel=kernel)

            logger.info(f"缩放至: {image.width}x{image.height}")

        # 保存图像
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 根据文件类型设置保存选项
        ext = os.path.splitext(output_path)[1].lower()
        options = {}

        if ext in ['.jpg', '.jpeg']:
            options = {
                'Q': quality,
                'optimize_coding': True,
                'interlace': True
            }
        elif ext == '.png':
            options = {'compression': 9}
        elif ext == '.webp':
            options = {'Q': quality}

        image.write_to_file(output_path, **options)
        logger.info(f"已保存: {output_path}")

        return True

    except Exception as e:
        logger.error(f"错误: {e}")
        return False


# tests
if __name__ == "__main__":
    url = "https://www.tesehebei.com/UploadImages/FckeditorImage/20140806/20140806110941_5196.jpg"
    download_resize_save(url, "./test.jpg", 320 * 240, quality=85)
