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
from typing import Dict, Any
import time
import os
import sys
import math
import random
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from WorkerApp import App

os.environ.pop('http_proxy', None)
# os.environ.pop('https_proxy', None)
#
from work4x.config import WORKER_NUM_THUMB

tmp_file_count = 0
tmp_file_max = 20
default_pixels = 320 * 240


# from celery.events.dispatcher import EventDispatcher
from work4x.utils.logger import logger
from work4x.utils.file import upload_oss, download_resize_save, FileType
from work4x.config import FILE_TEMP_DIR


class TaskInputs(BaseModel):
    image_url: str
    pixels: int = default_pixels


app = App('worker_thumb', worker_concurrency=WORKER_NUM_THUMB)


def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


@app.task
def thumb(task: dict[str, object]):
    inputs = TaskInputs.model_validate(orjson.loads(str(task.get('inputs'))))

    img_url = inputs.image_url
    max_pixels = inputs.pixels

    now = datetime.now()
    t = now.strftime("%Y%m%d%H%M%S") + "_{:03d}_{:04d}".format(now.microsecond // 1000, random.randrange(100, 10000))
    filename = f"thumb_{t}.jpg"
    save_path = os.path.join(FILE_TEMP_DIR, filename)
    download_resize_save(img_url, save_path, max_pixels)
    url = upload_oss(save_path, FileType.PICS)
    print(f"uploaded to {url}")
    return url


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='')
    # parser.add_argument('worker', type=str, default='', help='batch size')
    # parser.add_argument('-P', type=str, default='gevent', help='batch size')

    worker = app.Worker()
    worker.start()

    # url = "https://www.tesehebei.com/UploadImages/FckeditorImage/20140806/20140806110941_5196.jpg"
    # thumb(url)
