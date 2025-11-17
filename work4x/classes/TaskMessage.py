from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus:
    """
    任务状态
    """
    READY = 0
    DISPATCHED = 1
    PROCESSING = 2
    SUCCESS = 3
    FAIL = -1


class TaskType(Enum):
    IMAGE_DESCRIBE = "ImageDesc"
    TEXT_TO_SPEECH = "TTS"
    SPEECH_TO_TEXT = "STT"
    VIDEO_CUT = "VideoCut"
    TEXT_GENERATION = "TextGen"
    IMAGE_GENERATION = "ImageGen"
    VIDEO_GENERATION = "VideoGen"
    IMAGE_THUMB = "ImageThumb"


class TaskBaseMessage(BaseModel):
    # 标识ID
    id: int = 0

    # 用户ID
    userId: int = None

    # 项目ID
    projectId: int = None

    # 任务类型
    type: str = None

    # 任务输出JSON
    outputs: Optional[str] = None

    # 任务状态
    status: Optional[int] = None

    # 任务状态描述
    statusText: Optional[str] = None


class TaskMessage(TaskBaseMessage):
    """
    任务消息类
    """
    # 任务内容JSON
    inputs: Optional[str] = None

    # 消耗积分数
    credits: Optional[int] = None


class TaskCallback(TaskBaseMessage):
    pass
