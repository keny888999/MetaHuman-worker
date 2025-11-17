::uv run celery -A workers worker -P gevent -c 3 --loglevel=INFO  -E
uv run workers\worker_text_gen.py
