from ast import Dict
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus:
    """
    任务状态
    """
    PENDING = 0
    DISPATCHED = 1
    PROCESSING = 2
    SUCCESS = 3
    FAIL = -1


class TaskType(Enum):
    IMAGE_DESCRIBE = "ImageDesc"
    TEXT_TO_SPEECH = "TTS"
    SPEECH_TO_TEXT = "STT"
    CLONE_VOICE = "CloneVoice"
    VIDEO_CUT = "VideoCut"
    TEXT_GENERATION = "TextGen"
    IMAGE_GENERATION = "ImageGen"
    VIDEO_GENERATION = "VideoGen"
    IMAGE_THUMB = "ImageThumb"


class TaskBaseMessage(BaseModel):
    # 标识ID
    taskId: int = 0
    type: Optional[str] = ""
    headers: Optional[dict] = Field(default_factory=dict)


class TaskRequest(TaskBaseMessage):
    inputs: Optional[dict] = None


class TaskCallback(TaskBaseMessage):
    # 任务状态
    status: Optional[int] = None
    # 任务状态描述
    statusText: Optional[str] = None

    # 任务输出JSON
    outputs: Optional[str] = None

    metrics: Optional[dict] = None
    pass
