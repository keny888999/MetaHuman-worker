::uv run celery -A workers worker -P gevent -c 3 --loglevel=INFO  -E
uv run work4x\workers\worker_comfyui.py
