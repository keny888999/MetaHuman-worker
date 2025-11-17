#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
FILE_TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'temp')
OSS_UPLOAD_URL = "http://127.0.0.1:48080/app-api/infra/file/upload?directory="

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_DB = 0

CELERY_REDIS_HOST = "127.0.0.1"
CELERY_REDIS_PORT = 6379
CELERY_REDIS_DB = 1

WORKER_NUM_TTS = 5
WORKER_NUM_TEXT_GEN = 5
WORKER_NUM_VIDEO_GEN = 5
WORKER_NUM_THUMB = 5


STREAM_CALLBACK_KEY = "TaskCallback"
TASK_HASH_KEY = "Tasks"
