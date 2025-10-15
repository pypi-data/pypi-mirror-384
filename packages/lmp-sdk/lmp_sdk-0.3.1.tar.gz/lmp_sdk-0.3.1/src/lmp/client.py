import time
import logging
import threading
from typing import Optional, Callable, List
from datetime import timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from .task_queue import TaskQueue

from .models import (
    PostAsyncInferRequest,
    PostAsyncInferResponse,
    PostAsyncInferParams,
    Message,
    TaskResponse,
    Content
)
from .constants import (
    DEFAULT_API_ENDPOINT,
    DEFAULT_MODEL,
    BASE_GET_URL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_MAX_WAIT_TIME,
    DEFAULT_MAX_QUEUE_SIZE
)
from .exceptions import APIError, TaskTimeoutError, TaskFailedError

logger = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        token: str,
        is_use_queue: bool = True,
        endpoint: str = DEFAULT_API_ENDPOINT,
        worker_num: int = 100,
        polling_interval: int = DEFAULT_POLLING_INTERVAL,
        max_wait_time: int = DEFAULT_MAX_WAIT_TIME,
        max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE,
        timeout: int = 3600
    ):
        self.endpoint = endpoint
        self.token = token
        self.polling_interval = polling_interval
        self.max_wait_time = max_wait_time

        # 创建 Session
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=worker_num,  # 每个主机的连接池连接数
            pool_maxsize=worker_num,
            max_retries=Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]),
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "content-type": "application/json",
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        })
        self.timeout = timeout

        if is_use_queue:
            # 1. 创建任务队列
            self.task_queue = TaskQueue(
                max_queue_size=max_queue_size
            )

        logger.info(f"Client initialized with endpoint: {endpoint}")

    def get_task_queue(self):
        return self.task_queue

    def post_async_infer(self, request: PostAsyncInferRequest) -> PostAsyncInferResponse:
        # 设置默认值
        if not request.model:
            request.model = DEFAULT_MODEL
        if request.temperature == 0:
            request.temperature = DEFAULT_TEMPERATURE
        if request.max_retries == 0:
            request.max_retries = DEFAULT_MAX_RETRIES

        if not request.contents:
            raise ValueError("No contents provided")

        # 构建参数
        params = PostAsyncInferParams(
            model=request.model,
            messages=[
                Message(role=request.role, content=request.contents)
            ],
            temperature=request.temperature,
            frequency_penalty=request.frequency_penalty,
            stream=request.stream,
            ipai_max_request_retries=request.max_retries
        )

        return self.async_infer_send(params)

    def async_infer_send(self, params: PostAsyncInferParams) -> PostAsyncInferResponse:

        try:
            response = self.session.post(
                self.endpoint,
                json=params.to_dict(),
                timeout=self.timeout
            )

            if response.status_code != 200:
                raise APIError(response.status_code, response.text)

            result = PostAsyncInferResponse.from_dict(response.json())

            # 添加到任务队列
            if self.task_queue and result.data:
                self.task_queue.add_task(result.data.task_id)
                logger.info(f"Task {result.data.task_id} added to queue")

            return result

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(0, str(e))

    def get_task_status(self, task_id: str) -> TaskResponse:

        url = f"{BASE_GET_URL}/async_infer/{task_id}"

        try:
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                raise APIError(response.status_code, response.text)

            return TaskResponse.from_dict(response.json())

        except requests.RequestException as e:
            logger.error(f"Get task status failed: {e}")
            raise APIError(0, str(e))

    def wait_for_task_completion(
        self,
        task_id: str,
        callback: Optional[Callable[[TaskResponse], None]] = None
    ) -> TaskResponse:
        start_time = time.time()
        deadline = start_time + self.max_wait_time

        logger.info(f"Start polling task: {task_id}")
        logger.info(f"Polling interval: {self.polling_interval}s, Max wait: {self.max_wait_time}s")

        request_count = 0

        while True:
            # 检查超时
            if time.time() > deadline:
                raise TaskTimeoutError(f"Task timeout after {time.time() - start_time:.1f}s")

            request_count += 1
            current_time = time.strftime("%H:%M:%S")
            logger.info(f"[{current_time}] Request #{request_count}")

            try:
                result = self.get_task_status(task_id)

                # 检查错误码
                if result.errno != 0:
                    logger.info(f"Task processing: {result.msg}")
                    if result.data and result.data.estimated_scheduled_time > 0:
                        logger.info(f"Estimated wait: {result.data.estimated_scheduled_time}s")
                    time.sleep(self.polling_interval)
                    continue

                # 检查任务状态
                if result.data:
                    status = result.data.status
                    print(f'get_task_status, task_id is: {task_id}, resp status is: {status}')
                    if status == "RUNNING":
                        logger.info("Task running...")
                    elif status == "SUCCEEDED":
                        logger.info("Task succeeded!")
                        self._update_task_status(task_id, callback, result)
                        return result
                    elif status in ["FAILED", "UNKNOWN"]:
                        logger.error(f"Task failed: {result.data.failed_reason}")
                        self._update_task_status(task_id, callback, result)
                        raise TaskFailedError(f"Task failed: {result.data.failed_reason}")
                    elif status == "PENDING":
                        logger.info("Task pending...")
                    else:
                        logger.warning(f"Unknown status: {status}")

            except (APIError, TaskFailedError):
                raise
            except Exception as e:
                logger.error(f"Request failed: {e}")

            time.sleep(self.polling_interval)

    def _update_task_status(
        self,
        task_id: str,
        callback: Optional[Callable[[TaskResponse], None]],
        response: TaskResponse
    ):
        """更新任务状态"""
        # 从队列删除
        if self.task_queue:
            self.task_queue.remove_task(task_id)

        # 执行回调
        if callback:
            threading.Thread(target=callback, args=(response,), daemon=True).start()

    def post_async_infer_batch(
        self,
        requests: List[PostAsyncInferRequest],
        max_workers: int = 10
    ) -> List[PostAsyncInferResponse]:

        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.post_async_infer, req): i
                for i, req in enumerate(requests)
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch request failed: {e}")
                    results.append(None)

        return results

    def close(self):
        """关闭客户端"""
        self.session.close()
        logger.info("Client closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()