#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny

import os
import sys
import traceback

CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)
sys.path.append(os.path.join(CURR_PATH, '..'))
sys.path.append(os.path.join(CURR_PATH, '..', '..'))

from pydantic import BaseModel
from moviepy import VideoFileClip, AudioFileClip
from typing import Optional

# os.environ.pop('http_proxy', None)
# os.environ.pop('https_proxy', None) # 一定要保留 https_proxy ，否则请求会很慢!!!

# 这句于要提前
from App import app, WorkerApp, Work4xTask, WORK4X_PATH
from work4x.config import WORKER_NUM_VIDEO_GEN, RUNNINGHUB_DEV, RUNNINGHUB_API_KEY_ENT2,RUNNINGHUB_API_KEY_VIDEO_GEN

from work4x.utils.logger import logger
from work4x.utils.file import upload_oss, download_temp_file, FileType
from work4x.config import FILE_TEMP_DIR
from workers.sdk.runninghub.runninghub import RunningHub
from workers.video_utils.merge_subtitle import merge_subtitle
from classes.TaskRequest import TaskRequest, TaskType
from work4x.workers.sdk.runninghub.image_gen import ImageGen

class InputVideoGen(BaseModel):
    imageUrl: str
    audioUrl: str
    subtitleUrl: Optional[str]=None
    prompt: str
    loraStrength:Optional[float]=0.80


class InputVoiceClone(BaseModel):
    audioUrl: str
    text: str


class InputImageGen(BaseModel):
    imageUrls:Optional[list[str]]=None
    prompt: Optional[str]=None
    aspectRatio:str
    resolution:str=None

TEST_DEBUG = False
workflow_clone = "1982831757290536961"
workflow_video_gen = "2000507554289549314"
workflow_video_gen_plus2 = "1977587456478453761"
# WORKFLOW_CLONE_ID_PLUS2 = "1996528995673972737"  # 只要ID存在就行
WORKFLOW_CLONE_ID = "1982831757290536961"  # 只要ID存在就行


if not RUNNINGHUB_DEV:
    workflow_video_gen = workflow_video_gen_plus2

worker_name = os.path.basename(__file__).split('.')[0]
worker = WorkerApp(app)

@app.task(bind=True, base=Work4xTask,name=TaskType.VIDEO_GENERATION.value)
def generate_video(self:Work4xTask, task_data: dict[str, object]):
    task = TaskRequest.model_validate(task_data)

    try:
        inputs = InputVideoGen.model_validate(task.inputs)
        logger.info(inputs)

    except Exception as e:
        logger.error(str(e))
        raise e

    if TEST_DEBUG:
        files, coins, money,cost_time = ["http://dev.oss.work4x.com/work4x/video/20251221/_20251221010225_272_2385_1766250149747.mp4"], 0, 0,0
    else:
        comfyUI = RunningHub(api_key=RUNNINGHUB_API_KEY_VIDEO_GEN)
        flow_file = os.path.join(WORK4X_PATH, "comfyui_workflows", "Digital-human_api.json")
        comfyUI.load(flow_file)
        loraStrength:float=inputs.loraStrength or 0.70
        if inputs.loraStrength<0.70:
            loraStrength=0.70

        if inputs.loraStrength>1.0:
            loraStrength=1.0

        params = [
            {
                "nodeId": "71",
                "fieldName": "url",
                "fieldValue": inputs.imageUrl  # "http://oss.fang3d.com/work4x/pics/20251011/3_1760196325595.png"
            },
            {
                "nodeId": "72",
                "fieldName": "audio",
                "fieldValue": inputs.audioUrl
            },
            {
                "nodeId": "57",
                "fieldName": "prompt",
                "fieldValue": inputs.prompt
            },
            {
                "nodeId": "43",
                "fieldName": "strength",
                "fieldValue": loraStrength
            }
        ]

        task_id = task.taskId

        def on_progress(node_id: str | int, node_name: str, curr: int, total: int, node_executed: int, node_count: int):
            if node_name == "__taskId__":
                self.on_comfyui_started(node_id,comfyUI.api_key)
                return

            data = dict(
                node_id=node_id,
                node_name=node_name,
                curr=curr,
                total=total,
                node_executed=node_executed,
                node_count=node_count
            )
            self.send_progress_event(task_id, data)

        task_data = comfyUI.post_task(workflow_video_gen, params)
        #self.on_comfyui_started(task_data.taskId, comfyUI.api_key)
        files, coins, money,cost_time = comfyUI.wait(task_data, on_progress=on_progress)

        logger.info(f"outputs:{files}")
        logger.info(f"coins:{coins}")
        logger.info(f"money:{money}")

    files.reverse()  # 取最后一个结果
    video_url = files[0]
    video_path = download_temp_file(video_url)

    clip = VideoFileClip(video_path)
    width, height = clip.size
    fps = clip.fps
    duration = clip.duration
    file_size = os.path.getsize(video_path)

    logger.info(f"尺寸: {width}x{height}")
    logger.info(f"帧率: {fps}")
    logger.info(f"时长: {duration} 秒")

    upload_file_path=""
    if inputs.subtitleUrl:
        try:
            logger.info("合并字幕文件: "+inputs.subtitleUrl)
            upload_file_path = os.path.join(FILE_TEMP_DIR, "_" + os.path.basename(video_path))
            merge_subtitle(inputs.subtitleUrl, video_path, width, height, upload_file_path)
        except Exception as e:
            upload_file_path = video_path
            logger.error("合并字幕处理失败:"+str(e))
    else:
        upload_file_path=video_path

    url=upload_oss(upload_file_path, FileType.VIDEO)

    result_data = {
        "url": url,
        "width": width,
        "height": height,
        "duration": duration,
        "fileSize": file_size
    }

    self.usage.duration=round(duration)
    self.usage.costTime=round(cost_time)
    return  self.success(result_data)


@app.task(bind=True, base=Work4xTask,name=TaskType.CLONE_VOICE.value)
def clone_voice(self:Work4xTask, task_data: dict[str, object]):
    task: TaskRequest = TaskRequest.model_validate(task_data)
    inputs = InputVoiceClone.model_validate(task.inputs)

    logger.info("=" * 20)
    logger.info("开始克隆..")
    logger.info(inputs)
    logger.info("=" * 20)

    # logger.info("sleep infinity")
    # time.sleep(3600 * 10)

    #rh = RunningHub(api_key=RUNNINGHUB_API_KEY_BASE)
    rh = RunningHub(api_key=RUNNINGHUB_API_KEY_ENT2)
    flow_file = os.path.join(WORK4X_PATH, "comfyui_workflows", "indexTTS2.json")
    rh.load(flow_file)
    params = [
        {
            "nodeId": "20",
            "fieldName": "audio",
            "fieldValue": inputs.audioUrl
        },
        {
            "nodeId": "6",
            "fieldName": "text",
            "fieldValue": inputs.text
        }
    ]

    task_id = task.taskId

    def on_progress(node_id: str | int, node_name: str, curr: int, total: int, node_executed: int, node_count: int):
        if node_name == "__taskId__":
            self.on_comfyui_started(node_id,rh.api_key)
            return

        data = dict(
            node_id=node_id,
            node_name=node_name,
            curr=curr,
            total=total,
            node_executed=node_executed,
            node_count=node_count
        )
        self.send_progress_event(task_id, data)

    try:
        create_result = rh.post_task(WORKFLOW_CLONE_ID, params)

        files, consume_coins, consume_money,taskCostTime = rh.wait(create_result, on_progress=on_progress)
        files.reverse()

        audio_save_path=download_temp_file(files[0])
        audio_url = upload_oss(audio_save_path, FileType.AUDIO)
        audio_info = AudioFileClip(audio_save_path)
        duration = audio_info.duration

        #text, subtitle_url = speech_to_text(audio_url)

        print(f"consume_coins={consume_coins}, consume_money={consume_money}")
        usage=self.usage
        usage.coins = consume_coins
        usage.money =consume_money
        usage.duration=round(duration)
        usage.costTime=round(taskCostTime)
        return self.success({"audioUrl": audio_url})
    except Exception as e:
        logger.error(f"克隆语音失败:{traceback.format_exc()}")
        raise e


@app.task(bind=True, base=Work4xTask,name=TaskType.IMAGE_GENERATION.value)
def image_gen(self:Work4xTask, task_data: dict[str, object]):
    task: TaskRequest = TaskRequest.model_validate(task_data)
    inputs = InputImageGen.model_validate(task.inputs)
    url=""
    if inputs.imageUrls and len(inputs.imageUrls)>0:
        url, usage = ImageGen.image_to_image(prompt=inputs.prompt, imageUrls=inputs.imageUrls, resolution=inputs.resolution,aspectRatio=inputs.aspectRatio)
    else:
        url,usage=ImageGen.text_to_image(prompt=inputs.prompt,resolution=inputs.resolution,aspectRatio=inputs.aspectRatio)

    img_path = download_temp_file(url)
    image_url = upload_oss(img_path, FileType.PICS)
    self.usage.money= usage.consumeMoney or usage.thirdPartyConsumeMoney
    return self.success({"imageUrl": image_url})

if __name__ == "__main__":
    worker.main(worker_name=worker_name,more_args=["-c",50])
