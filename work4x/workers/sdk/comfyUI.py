import sys
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
from pprint import pprint
from typing import Optional, Protocol, Any
from pydantic import BaseModel, RootModel

CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)
sys.path.append(os.path.join(CURR_PATH, '..', '..'))
sys.path.append(os.path.join(CURR_PATH, '..', '..', '..'))

from work4x.config import RUNNINGHUB_BASE_URL, RUNNINGHUB_API_KEY_BASE, RUNNINGHUB_WSS_URL


class RHTaskResponse(BaseModel):
    code: int
    msg: str
    data: Any


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


RH_CODE_QUEUED = 813
RH_CODE_WAIT = 804
RH_CODE_CANCEL = 805


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
    def __call__(self, node_id: str | int, node_name: str, curr: int, total: int, node_count: int) -> None:
        ...


def to_float(v, default=0.0):
    try:
        return float(v)
    except ValueError:
        return default


class ComfyUIApi:
    workflow: dict

    def __init__(self, api_url=RUNNINGHUB_WSS_URL, api_key=None):
        self.api_url = api_url
        self.client_id = str(uuid.uuid4())
        self.ws = None
        self.workflow = None
        self.connected = False
        self.node_count = 0

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

    def disconnect(self):
        if self.connected:
            self.connected = False
            self.ws.close()

    def load(self, workflow_path):
        # 加载工作流配置
        logger.info(f"加载工作流 {workflow_path}")
        with open(workflow_path, 'r', encoding="utf8") as file:
            self.workflow = json.load(file)
            keys = self.workflow.keys()
            self.node_count = len(keys)

    def set_node(self, id: str, key: str, value):
        node = self.workflow[id]
        node["inputs"][key] = value

    def update_node(self, data: list[dict]):
        for d in data:
            id = d["nodeId"]
            key = d["fieldName"]
            val = d["fieldValue"]
            self.set_node(id, key, val)

    def getWebsocketOutputID(self):
        for key, node in self.workflow.items():
            if node["class_type"] == "SaveImageWebsocket":
                return key

        return None

    def query_RH_result(self, task_id) -> RHTaskResponse:
        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "apiKey": RUNNINGHUB_API_KEY_BASE,
            "taskId": task_id
        }

        res = requests.post(f"{RUNNINGHUB_BASE_URL}/task/openapi/outputs", headers=headers, json=params)
        # print(f"status_code: {res.status_code}", flush=True)
        print(f"\ncontent: {res.content.decode()}", flush=True)
        print("\n")

        rs = res.json()
        return RHTaskResponse.model_validate(rs)

    async def _wait_task(self, task_id, TEST_DEBUG=False):
        delay_seconds = 1

        while True:
            if TEST_DEBUG:
                # test_mp4 = "https://rh-images.xiaoyaoyou.com/5aee649f5080f8ea9820e0a225c6de55/output/WanVideo2_1_InfiniteTalk_00001_p83-audio_rimbq_1760890771.mp4"
                # test_mp4 = "http://192.168.2.67:9000/work4x/video/20251023/liuyifei.mp4"
                test_mp4 = "https://rh-images.xiaoyaoyou.com/5aee649f5080f8ea9820e0a225c6de55/output/WanVideo2_1_InfiniteTalk_00001_p83-audio_pzytj_1763387667.mp4"
                result = {
                    "code": 0,
                    "msg": "success",
                    "data": [{'fileUrl': test_mp4, 'fileType': 'mp4', 'taskCostTime': '279', 'nodeId': '34'}]
                }

                if delay_seconds > 0:
                    print(f"delay_seconds {delay_seconds}")
                    delay_seconds -= 1
                    result.code = RH_CODE_WAIT
            else:
                result = self.query_RH_result(task_id)

            if result.code == 0:
                return result
            else:
                if result.code != RH_CODE_WAIT and result.code != RH_CODE_QUEUED:
                    return result

            await asyncio.sleep(1)

    def wait_task_sync(self, task_id, TEST_DEBUG=False):
        return asyncio.run(self._wait_task(task_id, TEST_DEBUG))

    def run(self, is_runningHub=False, on_progress: OnProgress | None = None):
        try:

            # 临时保存工作流，用来观察
            '''
            workflow_path = 'workflow.json'
            texts = json.dumps(self.workflow)
            with open(workflow_path, 'w', encoding="utf8") as file:
                file.write(texts)
                file.close()
            '''

            """将提示发送到ComfyUI服务器"""
            logger.debug(f"正在提交工作流到ComfyUI服务器")
            p = {"prompt": self.workflow, "client_id": self.client_id, "instanceType": "plus"}
            url = f"{self.api_url}/prompt"
            response = requests.post(url, json=p)
            result = response.json()

            print("result", result)

            if "error" in result:
                raise Exception("错误:", result["error"])

            if "node_errors" in result and len(result["node_errors"]) > 0:
                for node_name in result["node_errors"]:
                    print(f"节点 {node_name} 发生错误:")
                    for error in result["node_errors"][node_name]["errors"]:
                        print(error["message"])
                        print("====================")

                raise Exception("节点发生错误,终止执行")

            prompt_id = result["prompt_id"]
            current_node = ""

            consume_money = 0.0
            consume_coins = 0
            out_files = []

            ws_try_count = 3
            # 等待执行完成
            while True:
                try:
                    if self.connected == False:
                        self.connect()

                    out = self.ws.recv()
                    if not out:
                        continue

                    if not isinstance(out, str):
                        logger.info(f"binary output:{current_node}")
                        '''
                        #Websocket二进制图像输出
                        if current_node ==self.getWebsocketOutputID():
                            output_images_bytes=out[8:]
                        else:                                 
                            if current_node =="42":
                                image = Image.open( io.BytesIO(out[8:]))
                                image.save(f"d:/ksampler_step{ksampler_step}.png")                                   
                        '''
                        continue

                    message = json.loads(out)
                    print(json.dumps(message))

                    data = message.get("data", None)

                    # 执行中
                    if message["type"] == "executing":
                        if data["prompt_id"] != prompt_id:
                            continue

                        if data["node"] is not None:
                            current_node = data['node']
                            _id = data['node']
                            display_name = self.workflow[_id]["_meta"]["title"]
                            logger.info(f"正在处理节点 {display_name}")
                            if on_progress is not None:
                                on_progress(_id, display_name, 0, 0, self.node_count)

                        # 整个流程结束 {"type": "executing", "data": {"node": null, "prompt_id": "4159d3c1-16d2-4705-b8d3-ac5ba85d0761"}}
                        if data["node"] is None and data["prompt_id"] == prompt_id:
                            break
                    # 进度条
                    elif message["type"] == "progress":
                        if data["prompt_id"] != prompt_id:
                            continue

                        step = data.get('value', 0)
                        total = data.get('max', 0)
                        if on_progress is not None:
                            display_name = self.workflow[_id]["_meta"]["title"]
                            on_progress(data['node'], display_name, step, total, self.node_count)

                    # 执行完成
                    elif message["type"] == "executed" and data["prompt_id"] == prompt_id:
                        # {"type": "executed", "data": {"node": "225", "display_node": "225","output": {"images": [{"filename": "ComfyUI_temp_vzpua_00091_.png", "subfolder": "", "type": "temp"}]}, "prompt_id": "f7c7d88b-99c6-4a58-b39e-6e8e744e091c"}}
                        if "output" in data and data["output"] is not None and ("images" in data["output"] or "videos" in data["output"] or "audios" in data["output"]):
                            for key in data["output"]:
                                arr = data["output"][key]
                                for i in arr:
                                    filename = f"{self.api_url}/view?filename={i['filename']}&subfolder={i['subfolder']}&type={i['type']}"
                                    out_files.append(filename)

                    # 执行成功
                    elif message["type"] == "execution_success" and data["prompt_id"] == prompt_id:
                        break

                    elif message["type"] == "execution_error" and data["prompt_id"] == prompt_id:
                        raise Exception(data['exception_message'])
                        break

                except json.JSONDecodeError as e:
                    logger.error(f"处理接收JSON数据时错误:{str(e)}")
                    self.disconnect()
                    break

                except websocket.WebSocketConnectionClosedException as e:
                    self.connected = False
                    logger.info("WebSocket连接意外关闭")
                    time.sleep(2)

                    # 意外断链需要检查任务是否完成，才决定是否重连，如果任务已经完成的情况下重连，则会卡死在上面的等待消息的环节上
                    if is_runningHub:
                        rs = self.query_RH_result(prompt_id)
                        code = rs.code
                        if code == 0:
                            break

                        if code != RH_CODE_WAIT and code != RH_CODE_QUEUED:
                            exception_message = rs.data.failedReason.exception_message
                            logger.error(f"query_RH_result error:{exception_message}")
                            break

                    if ws_try_count > 0:
                        ws_try_count -= 1
                    else:
                        logger.info("尝试连接超过3次，退出websocket")
                        break

                    # 重连
                    try:
                        self.connect()
                        ws_try_count = 3
                    except:
                        time.sleep(1)
                        continue

                except Exception as e:
                    logger.error(f"流程发生错误:" + str(e))
                    break

            self.disconnect()

            # 退出循环websocket之后，获取输出结果
            if is_runningHub:
                time.sleep(1)
                rs = self.wait_task_sync(prompt_id)
                if rs.code == 0:
                    output_list = RHTaskSuccessData(rs.data).root
                    out_files = []
                    for d in output_list:
                        out_files.append(d.fileUrl)
                        if d.consumeMoney is not None:
                            consume_money += to_float(d.consumeMoney)

                        if d.consumeCoins is not None:
                            consume_coins += to_float(d.consumeCoins)
                else:
                    if rs.code == RH_CODE_CANCEL:
                        exception_message = "user cancel"
                    else:
                        failData = RHTaskFailData.model_validate(rs.data)
                        if failData.failedReason:
                            exception_message = failData.failedReason.exception_message or "unknown"
                        else:
                            exception_message = rs.msg

                    raise Exception(f"query_RH_result error: {exception_message}")
            else:
                # TODO 本地comfyUI的查询结果和容错机制
                pass

            logger.info("成功处理流程")
            return out_files, consume_coins, consume_money
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


comfyApi = ComfyUIApi()

if __name__ == "__main__":
    # 初始化API客户端
    comfyApi = ComfyUIApi()
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
    result = comfyApi.run(is_runningHub=True)
    logger.info(f"输出：{result}")
    logger.info(f"总耗时{time.time() - t}")
