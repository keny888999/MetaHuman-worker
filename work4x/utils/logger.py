from loguru import logger
import sys
import os
from datetime import datetime

# 移除默认配置（如果有）
logger.remove()

# 自定义控制台输出格式
console_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<white>{message}</white>"
)

# 添加控制台处理器
logger.add(
    sys.stdout,
    format=console_format,
    level="INFO",
    colorize=True,  # 启用颜色
    backtrace=True,  # 显示异常堆栈
    diagnose=True   # 显示变量值
)
