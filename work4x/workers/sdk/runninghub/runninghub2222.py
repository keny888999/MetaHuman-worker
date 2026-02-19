#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny

import platform
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

from pprint import pprint

os.environ.pop('http_proxy', None)
# os.environ.pop('https_proxy', None) # 一定要保留 https_proxy ，否则请求会很慢!!!

# uv run -m 模式需要这2行代码
CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)
sys.path.append(os.path.join(CURR_PATH, '../..', '..'))

from work4x.utils.logger import logger
from work4x.utils.file import download_temp_file

# running_hub
# RH_api_key = "7e280a5e033d4809a944cb82f8f3c597"
RH_api_key = "62ecd374ff7645f39c96acdec857c804"
RH_api_url = "https://www.runninghub.cn"
webhook_url = "http://test.fang3d.com/comfyui_callback"


workflow_video_test = "1977210045475758081"
workflow_video = "1977587456478453761"
checker_running = False

QUEUED_CODE = 813
WAIT_CODE = 804


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
    data: Optional[list[TaskResultData] | dict | str]


class TaskCreateResultData(BaseModel):
    netWssUrl: Optional[str]  # null,
    taskId: str     # "1910246754753896450",
    clientId: str   # "e825290b08ca2015b8f62f0bbdb5f5f6",
    taskStatus: str  # "QUEUED",
    promptTips: Optional[str]  # "{\"result\": true, \"error\": null, \"outputs_to_execute\": [\"9\"], \"node_errors\": {}}"


class TaskCreateResponse(RHResponse):
    data: Optional[TaskCreateResultData] = None


def is_windows():
    return platform.system() == 'Windows'


def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


def onWebhookMessage():
    logger.info("onWebhookMessage")
    pass


def query_task(task_id: str):

    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "apiKey": RH_api_key,
        "taskId": task_id
    }

    res = requests.post(RH_api_url + "/task/openapi/outputs", headers=headers, json=params)
    print(f"status_code: {res.status_code}", flush=True)
    print(f"content: {res.content.decode()}", flush=True)

    rs = res.json()
    if rs["code"] == 0:
        print(rs["data"])
    else:
        print(f'code={rs["code"]},wait...')

    return rs


async def _wait_task(task_id, TEST_DEBUG=False):
    delay_seconds = 1

    while True:
        if TEST_DEBUG:
            # test_mp4 = "https://rh-images.xiaoyaoyou.com/5aee649f5080f8ea9820e0a225c6de55/output/WanVideo2_1_InfiniteTalk_00001_p83-audio_rimbq_1760890771.mp4"
            # test_mp4 = "http://192.168.2.67:9000/work4x/video/20251023/liuyifei.mp4"
            test_mp4 = "https://rh-images.xiaoyaoyou.com/5aee649f5080f8ea9820e0a225c6de55/output/WanVideo2_1_InfiniteTalk_00001_p83-audio_pzytj_1763387667.mp4"
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
            rs = query_task(task_id)
            result = TaskCheckResponse.model_validate(rs)

        if result.code == 0:
            print("task success")
            # 保存临时文件
            r = result.data[0]  # type: ignore
            if TEST_DEBUG:
                file_path = "/work2/worker/temp/20251202093733_307_4625.mp4"
            else:
                file_path = download_temp_file(r.fileUrl)

            print("文件已保存到: " + file_path)
            return file_path
        else:
            if result.code != WAIT_CODE and result.code != QUEUED_CODE:
                raise Exception(f"code:{result.code},msg={result.msg}")

        await asyncio.sleep(1)


def wait_task_sync(task_id, TEST_DEBUG=False):
    return asyncio.run(_wait_task(task_id, TEST_DEBUG))


def post_task(workflow_id: str, params: list):
    headers = {
        "Host": "www.runninghub.cn",
        "Content-Type": "application/json"
    }
    data = {
        "apiKey": RH_api_key,
        "workflowId": workflow_id,
        # "webhookUrl": webhook_url,
        "nodeInfoList": params,
        "instanceType": "plus"
    }
    print("#" * 50)
    pprint(orjson.dumps(data).decode())
    print("#" * 50)

    res = requests.post(RH_api_url + "/task/openapi/create", headers=headers, json=data)

    try:
        result = TaskCreateResponse.model_validate(res.json(), strict=True)
    except Exception as e:
        raise Exception(f"create task error [model_validate failed]: content= {res.content}")

    return result


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
