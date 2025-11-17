#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny
"""
基于 ServerBase 和 LiteLLM 实现的文本生成服务
"""
import platform
if platform.system() == 'Windows':
    from eventlet import monkey_patch
    monkey_patch(thread=True, select=True)

import orjson
from typing import Dict, Any, cast
import time
import os
import sys

# uv run -m 模式需要这2行代码
CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)
sys.path.append(os.path.join(CURR_PATH, '..', '..'))


# 这句于要提前
from WorkerApp import App

from work4x.config import WORKER_NUM_TTS

module = os.path.basename(__file__).replace('.py', '')
app = App(module, worker_concurrency=WORKER_NUM_TTS)

os.environ.pop('http_proxy', None)
# os.environ.pop('https_proxy', None)

from utils.file import upload_oss, FileType
from utils.logger import logger
from sdk.tts_doubao import tts_http_stream
from workers.video_utils.words_to_sentences import convert_word_to_sentence_timestamps


def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


# 转换为句子级时间戳（使用默认的1.0秒逗号停顿阈值）
def convertSentences(word_timestamps):
    sentence_timestamps = convert_word_to_sentence_timestamps(word_timestamps)
    return sentence_timestamps


@app.task(bind=True)
def text_to_speech(self, task: dict[str, object]):
    task_id = self.request.id
    inputs: dict[str, object] = orjson.loads(str(task.get("inputs")))
    text: str = str(inputs.get("text"))
    params = cast(Dict[str, object], inputs.get('settings'))
    print(params)
    character = params.get('character', '')
    speed = params.get('speed', 1.0)
    emotion = params.get('emotion', "surprised")

    logger.info("正在生成..")
    audio_save_path = os.path.join(os.path.dirname(__file__), '..', '..', 'temp', task_id + ".mp3")
    audio_data, sentence = tts_http_stream(text, {"character": character, "speed": speed, "emotion": emotion})
    # 保存音频文件
    with open(audio_save_path, "wb") as f:
        f.write(audio_data)

    logger.info("生成完毕,正在上传..")
    audio_url = upload_oss(audio_save_path, FileType.AUDIO)

    # 把字词级转换成句子级
    words = [[x.get("word"), x.get("startTime"), x.get("endTime")] for x in sentence.get("words")]
    sentences = convertSentences(words)
    sentence_path = os.path.join(os.path.dirname(__file__), '..', '..', 'temp', 'sentences_' + task_id + ".json")

    # 保存并上传
    with open(sentence_path, "wb") as f:
        f.write(orjson.dumps(sentences))
    subtitle_url = upload_oss(sentence_path, FileType.JSON)

    if False:
        try:
            os.unlink(audio_save_path)
        except:
            logger.warning("删除临时文件失败:" + audio_save_path)

    # try:
    #    os.unlink(sentence_path)
    # except:
    #    logger.warning("删除临时文件失败:" + sentence_path)

    logger.info("成功上传:")
    logger.info(audio_url)
    logger.info(subtitle_url)
    return orjson.dumps({"audio_url": audio_url, "subtitle_url": subtitle_url}).decode()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='')
    # parser.add_argument('worker', type=str, default='', help='batch size')
    # parser.add_argument('-P', type=str, default='gevent', help='batch size')
    worker = app.Worker()
    worker.start()
