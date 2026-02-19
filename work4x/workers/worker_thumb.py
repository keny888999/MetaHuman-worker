#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny
"""
缩略图制作 Worker
"""
import platform


import argparse
import orjson
import time
import os
import sys
import random
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.pop('http_proxy', None)
# os.environ.pop('https_proxy', None)
#
from work4x.config import WORKER_NUM_THUMB
from work4x.workers.App import app, WorkerApp, Work4xTask
from work4x.classes.TaskRequest import TaskType

tmp_file_count = 0
tmp_file_max = 20
default_pixels = 320 * 240

worker_name = os.path.basename(__file__).split('.')[0]

from work4x.utils.logger import logger
from work4x.utils.file import upload_oss, download_resize_save, FileType
from work4x.config import FILE_TEMP_DIR


class InputThumb(BaseModel):
    imageUrl: str
    pixels: int = default_pixels


async def delay(v):
    time.sleep(v)


async def wait(v):
    await delay(v)


def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


@app.task(bind=True,base=Work4xTask,name=TaskType.IMAGE_THUMB.value)
def thumb(self,task: dict[str, object]):
    inputs = InputThumb.model_validate(task.get('inputs'))

    img_url = inputs.imageUrl
    max_pixels = inputs.pixels

    now = datetime.now()
    t = now.strftime("%Y%m%d%H%M%S") + "_{:03d}_{:04d}".format(now.microsecond // 1000, random.randrange(100, 10000))
    filename = f"thumb_{t}.jpg"
    save_path = os.path.join(FILE_TEMP_DIR, filename)
    download_resize_save(img_url, save_path, max_pixels)
    url = upload_oss(save_path, FileType.PICS)
    logger.info(f"uploaded to {url}")

    return self.success({"imageUrl": url})


if __name__ == "__main__":
    worker = WorkerApp(app)
    worker.main(worker_name=worker_name,more_args=["-c",WORKER_NUM_THUMB])
