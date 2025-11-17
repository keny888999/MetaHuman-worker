import os
import sys

WORKERS_PATH = os.path.abspath(os.path.dirname(__file__))
WORK4X_PATH = os.path.abspath(os.path.join(WORKERS_PATH, ".."))
ROOT_PATH = os.path.abspath(os.path.join(WORK4X_PATH, ".."))

sys.path.insert(0, ROOT_PATH)
print(f"ROOT_PATH={ROOT_PATH}")

sys.path.insert(0, WORK4X_PATH)
print(f"WORK4X_PATH={WORK4X_PATH}")

print(f"WORKERS_PATH={WORKERS_PATH}")
sys.path.insert(0, WORKERS_PATH)
