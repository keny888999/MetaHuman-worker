import sys
import orjson
import requests
import json
import websocket
import uuid
import base64
from PIL import Image
import time
import asyncio
import os
from loguru import logger
from typing import Optional, Protocol, Any
from pydantic import BaseModel, RootModel

CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)
sys.path.append(os.path.join(CURR_PATH, '../..', '..'))
sys.path.append(os.path.join(CURR_PATH, '../..', '..', '..'))

from work4x.config import RUNNINGHUB_DEV, RUNNINGHUB_BASE_URL, RUNNINGHUB_WSS_URL, RUNNINGHUB_API_KEY_BASE, RUNNINGHUB_API_KEY_ENT, RUNNINGHUB_API_KEY_ENT2

if RUNNINGHUB_DEV:
    API_KEY = RUNNINGHUB_API_KEY_BASE
else:
    API_KEY = RUNNINGHUB_API_KEY_ENT


class RHTaskResponse(BaseModel):
    code: int
    msg: str
    data: Any


class RHTaskCreateData(BaseModel):
    netWssUrl: str
    taskId: int
    clientId: str
    taskStatus: str
    promptTips: str


class RHTaskOutputData(BaseModel):
    fileUrl: str = ""
    fileType: str = ""  # "png",
    taskCostTime: str = ""  # "0",
    consumeMoney: Optional[float] = 0.0
    consumeCoins: Optional[int] = 0
    nodeId: str = ""  # "9"


class RHTaskSuccessData(RootModel):
    root: list[RHTaskOutputData]


class RHTaskFailData(BaseModel):
    class FailedReason(BaseModel):
        node_name: Optional[str]
        traceback: Optional[str]
        node_id: Optional[int]
        exception_message: str

    failedReason: FailedReason


class RHInput(BaseModel):
    apiKey: str
    workflowId: Optional[str] = None
    webhookUrl: Optional[str] = None
    instanceType: Optional[str] = None
    workflow: Optional[Any] = None
    nodeInfoList: Optional[list[dict]] = None


RH_CODE_QUEUED = 813
RH_CODE_WAIT = 804
RH_CODE_CANCEL = 805
RH_CODE_NOT_FOUND = 807


logger.remove()
console_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<white>{message}</white>"
)
logger.add(
    sys.stdout,
    format=console_format,
    level="INFO",
    colorize=True,  # 启用颜色
    backtrace=True,  # 显示异常堆栈
    diagnose=True   # 显示变量值
)


POLLING = 0.5


class OnProgress(Protocol):
    def __call__(self, node_id: str | int, node_name: str, curr: int, total: int, node_executed: int, node_count: int) -> None:
        ...


def to_float(v, default=0.0):
    try:
        return float(v)
    except ValueError:
        return default


class RunningHub:
    workflow: dict

    def __init__(self, api_url=RUNNINGHUB_WSS_URL, api_key=API_KEY):
        self.api_url = api_url
        self.client_id = str(uuid.uuid4())
        self.ws = None
        self.workflow = None
        self.connected = False
        self.node_count = 0
        self.params = []
        self.api_key = api_key

    def connect(self, ws_url: str = ""):
        # 创建WebSocket连接
        self.ws = websocket.WebSocket()
        if not ws_url:
            ws_url = self.api_url.replace("http://", "ws://").replace("https://", "wss://")
            ws_url = f"{ws_url}/ws?clientId={self.client_id}"

        logger.info(f"正在连接ComfyUI服务器:{ws_url}")
        self.ws.connect(ws_url)
        self.connected = True
        logger.info("websocket连接成功")

    def cancel(self, task_id: str):
        headers = {
            "Host": "www.runninghub.cn",
            "Content-Type": "application/json"
        }
        data = dict(
            apiKey=self.api_key,
            taskId=task_id,
        )

        res = requests.post(RUNNINGHUB_BASE_URL + "/task/openapi/cancel", headers=headers, json=data)
        result = RHTaskResponse.model_validate(res.json(), strict=True)
        if res.status_code == 200 and result.code == 0:
            logger.info("取消任务成功")
        else:
            logger.error(f"取消任务失败:{res.status_code} {res.text}")

    def disconnect(self):
        self.connected = False
        try:
            self.ws.close()
        except:
            pass

    def load(self, workflow_path):
        # 加载工作流配置
        logger.info(f"加载工作流 {workflow_path}")
        with open(workflow_path, 'r', encoding="utf8") as file:
            self.workflow = json.load(file)
            keys = self.workflow.keys()
            self.node_count = len(keys)

    def set_params(self, data: list[dict]):
        self.params = data
        if self.workflow is not None:
            self.update_node(data)

    def update_node(self, data: list[dict]):
        for d in data:
            id = d["nodeId"]
            key = d["fieldName"]
            val = d["fieldValue"]
            self.set_input(id, key, val)

    def set_input(self, id: str, key: str, value):
        node = self.workflow[id]
        node["inputs"][key] = value

    def getWebsocketOutputID(self):
        for key, node in self.workflow.items():
            if node["class_type"] == "SaveImageWebsocket":
                return key

        return None

    def is_bad_code(self, code):
        return code != 0 and code != RH_CODE_WAIT and code != RH_CODE_QUEUED

    def RH_get_result(self, task_id) -> RHTaskResponse:
        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "apiKey": self.api_key,
            "taskId": task_id
        }

        res = requests.post(f"{RUNNINGHUB_BASE_URL}/task/openapi/outputs", headers=headers, json=params)
        # print(f"status_code: {res.status_code}", flush=True)
        logger.info(f"content: {res.content.decode()}")

        rs = res.json()
        return RHTaskResponse.model_validate(rs)

    def RH_get_status(self, task_id) -> RHTaskResponse:
        logger.info("RH_get_status...")

        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "apiKey": self.api_key,
            "taskId": task_id
        }

        res = requests.post(f"{RUNNINGHUB_BASE_URL}/task/openapi/status", headers=headers, json=params, timeout=5)
        logger.info(f"content: {res.content.decode()}")

        rs = res.json()
        return RHTaskResponse.model_validate(rs)

    async def _wait_task(self, task_id, TEST_DEBUG=False) -> RHTaskResponse:
        delay_seconds = 1

        try_count = 1
        while True:
            try:
                if TEST_DEBUG:
                    test_mp4 = "https://rh-images.xiaoyaoyou.com/5aee649f5080f8ea9820e0a225c6de55/output/WanVideo2_1_InfiniteTalk_00001_p83-audio_pzytj_1763387667.mp4"
                    result: RHTaskResponse = RHTaskResponse(
                        code=0,
                        msg="success",
                        data=[{'fileUrl': test_mp4, 'fileType': 'mp4', 'taskCostTime': '279', 'nodeId': '34'}]
                    )

                    if delay_seconds > 0:
                        print(f"delay_seconds {delay_seconds}")
                        delay_seconds -= 1
                        result.code = RH_CODE_WAIT
                else:
                    result = self.RH_get_status(task_id)

                if result.code == 0:
                    if str(result.data) in ["FAILED", "SUCCESS"]:
                        return self.RH_get_result(task_id)
                elif result.code == RH_CODE_NOT_FOUND:
                    return result
                else:
                    raise Exception(result.msg)

                try_count = 1  # 正常情况复位

            except Exception as e:
                logger.error(str(e))
                if try_count >= 5:
                    raise e

                logger.info(f"retry ...{try_count}")
                try_count += 1

            await asyncio.sleep(1)

    def wait_task_sync(self, task_id, TEST_DEBUG=False):
        return asyncio.run(self._wait_task(task_id, TEST_DEBUG))

    def get_node_name(self, node_id: str) -> str:
        if self.workflow and node_id in self.workflow:
            return self.workflow[node_id]["_meta"]["title"]
        return node_id

    def post_task(self, workflow_id: str, params: list):
        logger.info(f"正在提交工作流到ComfyUI服务器")

        headers = {
            "Host": "www.runninghub.cn",
            "Content-Type": "application/json"
        }
        data = RHInput(
            apiKey=self.api_key,
            workflowId=workflow_id,
            # "webhookUrl": webhook_url,
            nodeInfoList=params,
            instanceType="plus"
        )

        print("#" * 50)
        print(data)
        print("#" * 50)

        if self.workflow:
            self.set_params(params)
            data.workflow = orjson.dumps(self.workflow).decode()
        else:
            data.nodeInfoList = params

        res = requests.post(RUNNINGHUB_BASE_URL + "/task/openapi/create", headers=headers, json=data.model_dump())
        res_json = res.json()
        print("\n\n")
        print(">" * 50)
        print(res_json)
        print(">" * 50)
        print("\n\n")
        code = res_json.get("code")
        if code != 0 and code != RH_CODE_WAIT and code != RH_CODE_QUEUED:
            raise Exception("错误:"+ str(res_json.get("msg")))

        result = RHTaskResponse.model_validate(res.json(), strict=False)
        result_data = RHTaskCreateData.model_validate(result.data)
        return result_data

    def wait(self, create_result: RHTaskCreateData, on_progress: OnProgress | None = None):
        try:
            is_cancel=False

            prompt_id = str(create_result.taskId)
            consume_money = 0.0
            consume_coins = 0
            taskCostTime=0
            out_files = []

            current_node_id = None
            node_executed = 0

            # 首次执行时，报告所有节点进度为0
            if on_progress is not None:
                on_progress(prompt_id, "__taskId__", 0, 0, 0, 0)

            # 等待执行完成
            while True:
                try:
                    if not self.connected:
                        self.connect(create_result.netWssUrl)

                    out = self.ws.recv()
                    if not out:
                        continue

                    if not isinstance(out, str):
                        logger.info(f"binary data")
                        continue

                    message = json.loads(out)
                    logger.info(json.dumps(message))

                    data = message.get("data", None)

                    if message["type"] == "executing":
                        if not data.get("node", None):
                            break

                        if data['node'] != current_node_id:
                            current_node_id = data['node']
                            node_executed += 1

                        _id = data['node']
                        display_name = self.get_node_name(_id)
                        logger.info(f"正在处理节点 {display_name}")
                        if on_progress is not None:
                            on_progress(_id, display_name, 0, 0, node_executed, self.node_count)
                    # 进度条
                    elif message["type"] == "progress":
                        if data.get("prompt_id") != prompt_id:
                            continue

                        step = data.get('value', 0)
                        total = data.get('max', 0)
                        if on_progress is not None:
                            _id = data['node']
                            display_name = self.get_node_name(_id)
                            on_progress(_id, display_name, step, total, node_executed, self.node_count)

                    # 执行成功
                    elif message["type"] == "execution_success":
                        break

                    elif message["type"] == "execution_cached":
                        nodes = data.get('nodes', [])
                        node_executed += len(nodes)
                        if len(nodes) > 0:
                            _id = nodes[-1]
                            display_name = self.get_node_name(_id)
                            on_progress(_id, display_name, 0, 0, node_executed, self.node_count)

                    elif message["type"] == "execution_interrupted":
                        is_cancel = True
                        self.disconnect()
                        raise Exception("user cancel")
                        break

                    elif message["type"] == "execution_error":
                        raise Exception(data['exception_message'])

                except json.JSONDecodeError as e:
                    logger.error(f"处理接收JSON数据时错误:{str(e)}")
                    self.disconnect()
                    break

                except websocket.WebSocketConnectionClosedException as e:
                    self.connected = False
                    logger.info("WebSocket连接意外关闭")
                    break

                except Exception as e:
                    self.disconnect()
                    raise e

            self.disconnect()
            if is_cancel:
                return None,0, 0,0

            # 退出循环websocket之后，获取输出结果
            time.sleep(0.5)
            rs = self.wait_task_sync(prompt_id)
            if rs.code == 0:
                output_list = RHTaskSuccessData(rs.data).root
                out_files = []
                for d in output_list:
                    out_files.append(d.fileUrl)
                    if d.consumeMoney is not None:
                        consume_money += to_float(d.consumeMoney)

                    if d.consumeCoins is not None:
                        consume_coins += int(d.consumeCoins)

                    if d.taskCostTime is not None:
                        taskCostTime += int(d.taskCostTime)
            else:
                if rs.code == RH_CODE_CANCEL:
                    exception_message = "user cancel"
                else:
                    if 'data' in rs and 'failedReason' in rs.data:
                        failData = RHTaskFailData.model_validate(rs.data)
                        exception_message = failData.failedReason.exception_message or "unknown"
                    else:
                        exception_message = rs.msg

                raise Exception(exception_message)

            logger.info("成功处理流程")
            return out_files, consume_coins, consume_money,taskCostTime
        except Exception as e:
            self.disconnect()
            raise e

    def upload_image(self, image_path, image_name):
        """上传图片到ComfyUI服务器"""
        url = f"{self.api_url}/upload/image"
        files = {
            'image': (image_name, open(image_path, 'rb'), 'image/png')
        }
        response = requests.post(url, files=files)
        return response.json()



comfyApi = RunningHub()

if __name__ == "__main__":
    # 初始化API客户端
    comfyApi = RunningHub()
    comfyApi.connect()
    pwd = os.path.dirname(__file__)
    flow_file = os.path.join(pwd, "workflows/test.json")
    comfyApi.load(flow_file)
    comfyApi.update_node([{
        "nodeId": "6",
        "fieldName": "text",
        "fieldValue": "A realistic orange is placed on the table."
    }])

    # 执行工作流
    t = time.time()
    # result = comfyApi.run(is_runningHub=True)
    # logger.info(f"输出：{result}")
    # logger.info(f"总耗时{time.time() - t}")
