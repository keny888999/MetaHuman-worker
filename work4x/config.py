#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
FILE_TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'temp')
OSS_UPLOAD_URL = "http://127.0.0.1:48080/app-api/infra/file/upload?directory="


WORKER_NUM_TTS = 5
WORKER_NUM_TEXT_GEN = 5
WORKER_NUM_VIDEO_GEN = 3
WORKER_NUM_THUMB = 5

WORKER_REDIS_URL = "redis://192.168.2.6:6379"
WORKER_REDIS_DB = 1

TASK_REQUEST_KEY_PREFIX = "work4x:task:request:"
TASK_RESPONSE_KEY = "work4x:task:response"
TASK_DEFAULT_GROUP = "default"
TASK_STREAM_KEY = "work4x:task:stream"

TASK_CACHE_KEY = "Tasks"

RUNNINGHUB_API_KEY_BASE = "7e280a5e033d4809a944cb82f8f3c597"  # 基础API
# RUNNINGHUB_API_KEY_BASE = "3a386039183548409b741f4a45ee6c18"  # 基础API李鹏
RUNNINGHUB_API_KEY_ENT = "62ecd374ff7645f39c96acdec857c804"  # 企业API扣钱
RUNNINGHUB_API_KEY_ENT2 = "76a6ce629ff34fbdab48a6d20eed558c"  # 另外一个账户的企业API

RUNNINGHUB_API_KEY_VIDEO_GEN=RUNNINGHUB_API_KEY_ENT

RUNNINGHUB_BASE_URL = "https://www.runninghub.cn"
RUNNINGHUB_WSS_URL = f"{RUNNINGHUB_BASE_URL}/proxy/{RUNNINGHUB_API_KEY_BASE}"

RUNNINGHUB_DEV = True


MINMAX_API_KEY = "sk-api-ibJIFzC-tcU2vgDoaY8Xc1uxQRw34vihx7VCDu7fLwe-3cwFBxxBxI9SuthESeaGDtCaRGFQElhfL9YYj2TImSCTz87PXEVdIPjgoY05z6pSpCZysmR49bE"
