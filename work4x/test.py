import threading
import time
from concurrent.futures import ThreadPoolExecutor


class AsyncResultHandler:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)

    def wait_test(self, x):
        time.sleep(1)
        print(x, flush=True)

    def wait_and_send(self, id):
        # async_result = AsyncResult(str(id), app=current_app)
        # self.executor.submit(self.wait_result, async_result)
        self.executor.submit(self.wait_test, id)


asyncResultHandler = AsyncResultHandler()

for x in range(10):
    print(x, flush=True)
    asyncResultHandler.wait_and_send("ok")
