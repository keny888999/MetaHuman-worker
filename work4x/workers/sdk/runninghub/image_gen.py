import traceback
import time

import requests
from work4x.config import RUNNINGHUB_BASE_URL,RUNNINGHUB_API_KEY_ENT, RUNNINGHUB_API_KEY_ENT2
from work4x.utils.logger import logger

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Usage(BaseModel):
    """使用情况明细"""
    consumeMoney: Optional[float] = None        # 消耗金额，可能为 null
    consumeCoins: Optional[float] = None        # 消耗积分，可能为 null
    taskCostTime: str                            # 任务耗时（字符串形式）
    thirdPartyConsumeMoney: Optional[float] = None  # 第三方消耗金额，可能为 null

class ResultItem(BaseModel):
    """结果项"""
    url: str                                      # 结果文件的 URL
    outputType: str                               # 输出类型，如 "png"
    text: Optional[str] = None                    # 可能的文本输出，可能为 null

class TaskResponse(BaseModel):
    """任务响应主模型"""
    taskId: str                                    # 任务 ID
    status: str                                    # 任务状态，如 "SUCCESS"
    errorCode: str = ""                            # 错误码，默认为空字符串
    errorMessage: str = ""                         # 错误信息，默认为空字符串
    failedReason: Optional[Dict[str, Any]] = None  # 失败原因，可能为 null 或空对象
    usage: Optional[Usage]                                    # 使用情况
    results: Optional[List[ResultItem]]                       # 结果列表
    clientId: str = ""                              # 客户端 ID，默认为空
    promptTips: str = ""                            # 提示信息，默认为空


headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {RUNNINGHUB_API_KEY_ENT}"
}

class ImageGen:
    @staticmethod
    def wait_result(task_id:str,timeout:int=120)->TaskResponse:
        params={
            "taskId": task_id,
        }

        t_begin = time.time()
        try_count=0
        while time.time()-t_begin < timeout:
            try:
                logger.info(f"wait_result...[{task_id}]")
                res = requests.post(f"{RUNNINGHUB_BASE_URL}/openapi/v2/query", headers=headers, json=params, timeout=5)
                logger.info(f"content: {res.content.decode()}")
                rs = res.json()
                try_count = 0

                response=TaskResponse.model_validate(rs)
                if  response.status in ["QUEUED","RUNNING"]:
                    time.sleep(1)
                    continue
                else:
                    return response
            except Exception as e:
                traceback.print_exc()
                try_count+=1
                if try_count>2:
                    raise e

            time.sleep(1)

        raise Exception("Timeout")

    @staticmethod
    def text_to_image(prompt:str,aspectRatio:str,resolution:str="1k",**args)->(str|None,Usage):
        params = {
            "prompt": prompt,
            "aspectRatio":aspectRatio,
            "resolution": resolution,
        }

        res = requests.post(f"{RUNNINGHUB_BASE_URL}/openapi/v2/rhart-image-n-pro/text-to-image", headers=headers, json=params, timeout=5)
        logger.info(f"content: {res.content.decode()}")
        rs = res.json()
        response = TaskResponse.model_validate(rs)
        if response.errorCode:
            raise Exception(response.errorMessage)

        response=ImageGen.wait_result(response.taskId,timeout=120)
        if response.status=="SUCCESS":
            return response.results[0].url,response.usage
        else:
            raise Exception(response.errorMessage)


    @staticmethod
    def image_to_image(prompt:str,imageUrls:list[str],aspectRatio:str,resolution:str="1k",**args)->(str|None,Usage):
        params = {
            "prompt": prompt,
            "aspectRatio":aspectRatio,
            "imageUrls": imageUrls,
            "resolution": resolution,
        }

        res = requests.post(f"{RUNNINGHUB_BASE_URL}/openapi/v2/rhart-image-n-pro/edit", headers=headers, json=params, timeout=5)
        logger.info(f"content: {res.content.decode()}")
        rs = res.json()
        response = TaskResponse.model_validate(rs)
        if response.errorCode:
            raise Exception(response.errorMessage)

        response=ImageGen.wait_result(response.taskId,timeout=120)
        if response.status=="SUCCESS":
            return response.results[0].url,response.usage
        else:
            raise Exception(response.errorMessage)

