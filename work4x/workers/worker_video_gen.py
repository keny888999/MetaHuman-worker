#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny
"""
缩略图制作 Worker
"""
import platform
if platform.system() == 'Windows':
    from eventlet import monkey_patch
    monkey_patch(thread=True, select=True)

import orjson
import time
import os
import sys
import math
import random

from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import requests
from moviepy import VideoFileClip
import subprocess
import asyncio

os.environ.pop('http_proxy', None)
# os.environ.pop('https_proxy', None)

# uv run -m 模式需要这2行代码
CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)
sys.path.append(os.path.join(CURR_PATH, '..', '..'))

# 这句于要提前
from WorkerApp import App, ROOT_PATH
from work4x.config import WORKER_NUM_VIDEO_GEN
from RedisPublisher import RedisPublisher

#

tmp_file_count = 0
tmp_file_max = 20
thumb_max_pixels = 320 * 240

# from celery.events.dispatcher import EventDispatcher
from work4x.utils.logger import logger
from work4x.utils.file import upload_oss, download_temp_file, FileType, remove_file
from work4x.config import FILE_TEMP_DIR
from video_utils.json_to_ass_converter import json_to_ass
from work4x.workers.video_utils.subtitle import SubtitleProcessor

# running_hub
RH_api_key = "7e280a5e033d4809a944cb82f8f3c597"
RH_api_url = "https://www.runninghub.cn"
webhook_url = "http://test.fang3d.com/comfyui_callback"


workflow_video_test = "1977210045475758081"
workflow_video = "1977587456478453761"
checker_running = False

app = App("worker_video_gen", worker_concurrency=WORKER_NUM_VIDEO_GEN)

WAIT_CODE = 804


class TaskInputs(BaseModel):
    image_url: str
    audio_url: str
    subtitle_url: str
    prompt: str


class NodeInfo(BaseModel):
    nodeId: str = ""
    fieldName: str = ""
    fieldValue: str = ""


class TaskResultData(BaseModel):
    fileUrl: str = ""
    fileType: str = ""  # "png",
    taskCostTime: str = ""  # "0",
    nodeId: str = ""  # "9"


class WebHookData(BaseModel):
    event: str = ""
    taskId: str = ""
    eventData: str = ""


class RHResponse(BaseModel):
    code: int = 0
    msg: str = ""
    data: dict | str

    class Config:
        arbitrary_types_allowed = True


class TaskCheckResponse(RHResponse):
    data: list[TaskResultData] | dict | str


class TaskCreateResultData(BaseModel):
    netWssUrl: str  # null,
    taskId: str     # "1910246754753896450",
    clientId: str   # "e825290b08ca2015b8f62f0bbdb5f5f6",
    taskStatus: str  # "QUEUED",
    promptTips: str  # "{\"result\": true, \"error\": null, \"outputs_to_execute\": [\"9\"], \"node_errors\": {}}"


class TaskCreateResponse(RHResponse):
    data: Optional[TaskCreateResultData] = None


def is_windows():
    return platform.system() == 'Windows'


def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


def onWebhookMessage():
    logger.info("onWebhookMessage")
    pass


def init_redis():
    global redis
    redis = RedisPublisher()


def check_task(task_id: str):

    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "apiKey": RH_api_key,
        "taskId": task_id
    }

    res = requests.post(RH_api_url + "/task/openapi/outputs", headers=headers, json=params)
    rs = res.json()
    if rs["code"] == 0:
        print(rs["data"])
    else:
        print(f'code={rs["code"]},wait...')

    return rs


def request_runningHub(workflow_id: str, params: list) -> TaskCreateResponse:

    headers = {
        "Host": "www.runninghub.cn",
        "Content-Type": "application/json"
    }
    data = {
        "apiKey": RH_api_key,
        "workflowId": workflow_id,
        "webhookUrl": webhook_url,
        "nodeInfoList": params,
        "instanceType": "plus"
    }
    res = requests.post(RH_api_url + "/task/openapi/create", headers=headers, json=data)
    try:
        result = TaskCreateResponse.model_validate(res.json(), strict=True)
    except Exception as e:
        raise Exception(f"create task error [model_validate failed]: content= {res.content}")

    return result


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

    if is_windows():
        subtitle_ass = subtitle_ass.replace("\\", "/")
        arr = subtitle_ass.split(":")
        subtitle_ass = f"{arr[0]}\\\:{arr[1]}"

    success = merge_video_with_subtitles(video_path, subtitle_ass, save_path)
    if (not success):
        raise Exception("merge failed")
    return success


TEST_DEBUG = False


async def wait_task(task_id):
    delay_seconds = 4

    while True:
        if TEST_DEBUG:
            # test_mp4 = "https://rh-images.xiaoyaoyou.com/5aee649f5080f8ea9820e0a225c6de55/output/WanVideo2_1_InfiniteTalk_00001_p83-audio_rimbq_1760890771.mp4"
            test_mp4 = "http://192.168.2.67:9000/work4x/video/20251023/liuyifei.mp4"
            result = TaskCheckResponse.model_validate({
                "code": 0,
                "msg": "success",
                "data": [{'fileUrl': test_mp4, 'fileType': 'mp4', 'taskCostTime': '279', 'nodeId': '34'}]
            })

            if delay_seconds > 0:
                print(f"delay_seconds {delay_seconds}")
                delay_seconds -= 1
                result.code = WAIT_CODE
        else:
            rs = check_task(task_id)
            result = TaskCheckResponse.model_validate(rs)

        if result.code == 0:
            print("task success")
            # 保存临时文件
            r = result.data[0]
            video_path = download_temp_file(r.fileUrl)
            print("文件已保存到: " + video_path)
            return video_path
        else:
            if result.code != WAIT_CODE:
                raise Exception(f"code:{result.code},msg={result.msg}")

        await asyncio.sleep(2)


@app.task(bind=True)
def generate_video(self, task: dict[str, object]):

    try:
        inputs = TaskInputs.model_validate(orjson.loads(str(task.get('inputs'))))
        print(inputs)

    except Exception as e:
        logger.error(str(e))
        raise e

    if not TEST_DEBUG:
        res = request_runningHub(workflow_video, [
            {
                "nodeId": "71",
                "fieldName": "url",
                "fieldValue": inputs.image_url  # "http://oss.fang3d.com/work4x/pics/20251011/3_1760196325595.png"
            },
            {
                "nodeId": "72",
                "fieldName": "audio",
                "fieldValue": inputs.audio_url
            },
            {
                "nodeId": "57",
                "fieldName": "prompt",
                "fieldValue": inputs.prompt
            }
        ])

        print(res)
        print("\n")

    print("check_task")
    if TEST_DEBUG:
        video_path = asyncio.run(wait_task(0))
    else:
        video_path = asyncio.run(wait_task(res.data.taskId))

    clip = VideoFileClip(video_path)
    width, height = clip.size
    fps = clip.fps
    duration = clip.duration
    file_size = os.path.getsize(video_path)

    print(f"尺寸: {width}x{height}")
    print(f"帧率: {fps}")
    print(f"时长: {duration} 秒")

    video_path_tmp = os.path.join(FILE_TEMP_DIR, "_" + os.path.basename(video_path))
    merge_subtitle(inputs.subtitle_url, video_path, width, height, video_path_tmp)

    url = upload_oss(video_path_tmp, FileType.VIDEO)
    print("文件已上传到oos: " + url)

    result_data = {
        "url": url,
        "width": width,
        "height": height,
        "duration": duration,
        "file_size": file_size,
        "duration": duration
    }
    return orjson.dumps(result_data).decode()


if __name__ == "__main__":
    worker = app.Worker()
    worker.start()
    # download_temp_file("http://oss.fang3d.com/work4x/video/SampleVideo_1280x720_1mb.mp4")


def download_video_file(url: str, save_path: str = "") -> str:
    """
    下载视频文件到本地

    Args:
        url (str): 视频文件的URL
        save_path (str, optional): 保存路径，如果未提供则自动生成临时路径

    Returns:
        str: 下载后的文件路径

    Raises:
        Exception: 下载失败时抛出异常
    """
    try:
        if save_path == "":
            # 如果没有提供保存路径，使用download_temp_file生成临时文件
            return download_temp_file(url)

        logger.info(f"开始下载视频: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()  # 检查请求是否成功

        # 确保保存目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"视频下载完成: {save_path}")
        return save_path

    except Exception as e:
        logger.error(f"下载视频失败: {str(e)}")
        raise Exception(f"下载视频失败: {str(e)}")


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
        print(f"returncode={result.returncode}")

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
