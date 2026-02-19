import os
import sys

pwd = os.path.dirname(__file__)
dir_name = os.path.basename(pwd)
WORKERS_PATH = os.path.abspath(pwd)
WORK4X_PATH = os.path.abspath(os.path.join(WORKERS_PATH, ".."))
ROOT_PATH = os.path.abspath(os.path.join(WORK4X_PATH, ".."))

from work4x import config

# ============ 基础配置 ============
backend_url = f"{config.WORKER_REDIS_URL}/{config.WORKER_REDIS_DB}"
broker_url = backend_url  # Broker URL
result_backend_url = backend_url
# result_backend = backend_url  # 结果后端
result_backend = 'work4x.workers.backend.work4x_backend.EventAwareStreamBackend'

# ============ 任务配置 ============
# imports = ('tasks',)                          # 任务模块
task_serializer = 'json'  # 序列化方式
result_serializer = 'json'
accept_content = ['json']

# ============ 时区配置 ============
timezone = 'Asia/Shanghai'
enable_utc = True

# ============ Worker 配置 ============
worker_prefetch_multiplier = 1  # 预取任务数量倍数
worker_max_tasks_per_child = 1000  # 每个子进程最大任务数
worker_max_memory_per_child = 120000  # 内存限制 (KB)

# ============ 任务执行配置 ============
task_track_started = True  # 跟踪任务开始
task_time_limit = 60 * 60  # 任务超时时间 (秒)
task_annotations = {'*': {'rate_limit': '120/s'}}
task_soft_time_limit = 60 * 60  # 软超时时间 (秒)
task_acks_late = True  # 任务完成后确认
# task_reject_on_worker_lost = True  # Worker 丢失时拒绝任务
task_send_sent_event = True
worker_send_task_events = True
worker_enable_remote_control = True

resultrepr_maxsize = 100 * 1024

# ============ 结果配置 ============
result_expires = 3600 * 24  # 结果过期时间 (秒)
result_cache_max = 10000  # 最大结果缓存数

# ============ 路由配置 ============
task_routes = {
    'TextGen': {'queue': 'worker_text_gen'},
    'CloneVoice': {'queue': 'worker_comfyui'},
    'VideoGen': {'queue': 'worker_comfyui'},
    'ImageGen': {'queue': 'worker_comfyui'},
    'ImageThumb': {'queue': 'worker_thumb'},
    'TTS': {'queue': 'worker_tts'},
    'STT': {'queue': 'worker_tts'},
}

result_backend_transport_options = {
    # 'global_keyprefix': 'results:',  # 全局前缀
    'visibility_timeout': 3600,
}

broker_transport_options = {
    'fanout_patterns': True,  # 使用Redis Streams进行事件广播
    'fanout_prefix': True,  # 为事件键添加前缀
    "max_retries": 3,
    "interval_start": 0,
    "interval_step": 0.2,
    "interval_max": 0.5
}
