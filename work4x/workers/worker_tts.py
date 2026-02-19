#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny
"""
基于 ServerBase 和 LiteLLM 实现的文本生成服务
"""
import os
import sys
import math

import orjson
from typing import Dict, Any
import time
from pydantic import BaseModel
import subprocess
from celery.signals import worker_ready

# 这句于要提前
from work4x.workers.App import app, WorkerApp,  Work4xTask,WorkerMetrics,UsageItem
from work4x.config import WORKER_NUM_TTS, RUNNINGHUB_API_KEY_BASE

worker_name = os.path.basename(__file__).split('.')[0]

os.environ.pop('http_proxy', None)
# os.environ.pop('https_proxy', None)

from work4x.utils.file import upload_oss, upload_oss_url, FileType
from work4x.utils.logger import logger
from work4x.workers.sdk.tts_doubao import tts_http_stream
from work4x.workers.sdk.minmax import tts as minmax_tts
from work4x.workers.sdk.sta_doubao import audio_to_srt, speech_to_text
from work4x.workers.video_utils.words_to_sentences import convert_word_to_sentence_timestamps
from work4x.classes.TaskRequest import TaskRequest, TaskType
from work4x.workers.llm.text_generator import quick_generate_with_template
from work4x.workers.llm.templates import TemplateTranslate


class InputAudio(BaseModel):
    audioUrl: str


class InputTTS(BaseModel):
    text: str


def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


# 转换为句子级时间戳（使用默认的1.0秒逗号停顿阈值）
def convertSentences(word_timestamps):
    sentence_timestamps = convert_word_to_sentence_timestamps(word_timestamps)
    return sentence_timestamps


@worker_ready.connect
def at_start(sender, **k):
    logger.info("worker_ready...")
    # with sender.app.connection() as conn:
    #    sender.app.send_task('tasks.start_websocket_listener')



@app.task(bind=True, base=Work4xTask,name=TaskType.SPEECH_TO_TEXT.value)
def STT(self, task: dict[str, object]):
    """
    声音转文字
    """
    str_inputs = str(task.get("inputs"))
    inputs: InputAudio = InputAudio.model_validate_json(str_inputs)
    audio_url: str = inputs.audioUrl

    logger.info("语音提取字幕.." + audio_url)
    text, subtitle_url = speech_to_text(audio_url)

    return {"text": text, "subtitleUrl": subtitle_url}


@app.task(bind=True, base=Work4xTask,name=TaskType.TEXT_TO_SPEECH.value)
def TTS(self, task: dict[str, object]):
    from moviepy import AudioFileClip

    task_id = self.request.id
    inputs: dict[str, object] = task.get("inputs")
    text: str = str(inputs.get("text"))
    params = inputs
    print(params)

    this:Work4xTask=self

    if inputs.get("text", None) is None:
        raise Exception("input text empty")

    character = params.get('character', 'female-shaonv')
    speed = params.get('speed', 0)
    emotion = params.get('emotion', "happy")

    logger.info("正在生成..")

    language = params.get("language")
    if language and language!="" and language!='original':
        logger.info(f"正在翻译文本到{language}...")
        trans_text = quick_generate_with_template(TemplateTranslate, {"prompt": text, "language": language})
        print(trans_text)
    else:
        trans_text = text

    audio_save_path = os.path.join(os.path.dirname(__file__), '..', '..', 'temp', task_id + ".mp3")
    minmax_tts(trans_text, {"character": character, "speed": speed, "emotion": emotion}, audio_save_path)  # "emotion": emotion

    if False:
        audio_data, sentences = tts_http_stream(trans_text, {"character": character, "speed": speed})  # "emotion": emotion
        # ffmpeg -i 666_1766473642692.ogg -c copy -fflags +genpts output.ogg
        audio_fixed_path = os.path.join(os.path.dirname(__file__), '..', '..', 'temp', task_id + ".fixed.mp3")
        logger.info(f"正在修复音频长度...")
        fix_audio_length(audio_save_path, audio_fixed_path)
        try:
            os.unlink(audio_save_path)
        except:
            logger.warning("删除临时文件失败:" + audio_save_path)
        audio_save_path = audio_fixed_path

    audio_info=AudioFileClip(audio_save_path)
    duration=audio_info.duration

    logger.info("生成完毕,正在上传..")
    audio_url = upload_oss(audio_save_path, FileType.AUDIO)
    if not audio_url:
        raise Exception("上传音频失败")

    if False:
        for sentence in sentences:
            words = sentence.get("words")
            sentence["start"] = words[0].get("startTime")
            sentence["end"] = words[-1].get("endTime")
            sentence["words"] = [[x.get("word"), x.get("startTime"), x.get("endTime")] for x in words]

            # sentences = convertSentences(words)
            sentence_path = os.path.join(os.path.dirname(__file__), '..', '..', 'temp', 'sentences_' + task_id + ".json")

            # 保存并上传
            with open(sentence_path, "wb") as f:
                f.write(orjson.dumps(sentences))
            subtitle_url = upload_oss(sentence_path, FileType.JSON)
            if not subtitle_url:
                raise Exception("上传字幕文件失败")

    if False:
        try:
            os.unlink(audio_save_path)
        except:
            logger.warning("删除临时文件失败:" + audio_save_path)

    # try:
    #    os.unlink(sentence_path)
    # except:
    #    logger.warning("删除临时文件失败:" + sentence_path)


    if audio_url:
        logger.info("音频生成功:")
        logger.info(audio_url)
    else:
        raise Exception("生成失败")

    this.usage.duration=round(duration)
    this.usage.input=len(trans_text)
    return self.success({"audioUrl": audio_url,"duration":duration})


def fix_audio_length(file_path: str, output_path: str):
    try:
        # 构建FFmpeg命令
        # 使用字幕流覆盖在视频上

        # ffmpeg -i input.ogg -c copy -fflags +genpts output.ogg
        cmd = [
            'ffmpeg',
            '-i', file_path,           # 输入视频文件
            '-c:a', 'libmp3lame',             # 音频流直接复制
            '-y',
            output_path                 # 输出文件路径
        ]

        # 执行FFmpeg命令
        print(" ".join(cmd))
        result = subprocess.run(cmd)
        print(f"return code={result.returncode}")
        if result.returncode == 0:
            logger.info(f"修复成功")
            return True
        else:
            logger.error("修复失败")
            return False
    except Exception as e:
        logger.error(f"修复音频长度失败: {e.stderr}")
        return False


if __name__ == "__main__":
    worker = WorkerApp(app)
    worker.main(worker_name=worker_name,more_args=["-c",WORKER_NUM_TTS])
