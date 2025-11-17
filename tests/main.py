from fastapi import FastAPI, File, UploadFile, Form
import uvicorn
import shutil
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, Any, Dict, List
from utils.logger import logger

app = FastAPI()

UPLOAD_DIR = Path("uploads")

# 成功响应工具函数


def success(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
    return {
        "errno": 0,
        "message": message,
        "data": data,
    }

# 错误响应工具函数


def error(message: str, error_code: int = 400) -> Dict[str, Any]:
    return {
        "errno": 0,
        "message": message,
        "data": None,
    }


@app.post("/upload")
async def upload_and_save_file(project_id: str = Form(...), file: UploadFile = File(...)):
    """上传文件并保存到服务器指定目录"""

    logger.info("media_type:{}", file.content_type)

    # 构建保存路径
    save_path = UPLOAD_DIR / project_id
    file_type = file.content_type
    if file_type.startswith("video"):
        save_path = save_path / "video"
    elif file_type.startswith("image"):
        save_path = save_path / "image"
    else:
        save_path = save_path / "other"

    save_path.mkdir(parents=True, exist_ok=True)
    save_path = save_path / file.filename

    # 保存文件
    with open(save_path, "wb") as buffer:
        # 使用 shutil 复制文件对象内容到新文件
        shutil.copyfileobj(file.file, buffer)

    return success({
        "saved_path": str(save_path).replace("\\", "/")
    })

uvicorn.run(app, port=8765)
