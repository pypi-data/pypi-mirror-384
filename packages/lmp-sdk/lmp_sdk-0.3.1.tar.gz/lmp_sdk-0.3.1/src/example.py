import logging
import threading
import time
from lmp import (
    Client,
    TaskQueue,
    TaskProcessor,
    QueueConfig,
    Content,
    ContentType,
    PostAsyncInferRequest
)

# 配置日志
logging.basicConfig(level=logging.INFO)


def main():
    # 1. 创建任务队列
    config = QueueConfig(
        on_task_completed_success=lambda response: print(f"Task completed: {response.data.task_id if response.data else 'Unknown'}"),
        on_task_completed_failed=lambda response: print(f"Task completed: {response.data.task_id if response.data else 'Unknown'}")
    )
    task_queue = TaskQueue(
        on_task_completed_success=lambda response: print(f"Task completed: {response.data.task_id if response.data else 'Unknown'}"),
        on_task_completed_failed=lambda response: print(f"Task completed: {response.data.task_id if response.data else 'Unknown'}")
    )

    # 2. 创建客户端
    client = Client(
        token="ak-infer-bHBhaS1sbXA6bnhtamZoOm54bWpmaC1kZWZhdWx0OnpoYW5neGlucmFuM0BsaXhpYW5nLmNvbTppbmZlcg_NzMzNTcxNTktNmVlMC00MjU1LThjYzAtZmFmMDllZTRlNGM1",
        task_queue=task_queue
    )

    # 3. 创建任务处理器
    processor = TaskProcessor(
        queue=task_queue,
        client=client,
        worker_num=5,
    )


    # 4. 启动处理器
    processor.start()
    threads = []

    # 创建并启动5个线程
    for worker_id in range(5):
        thread = threading.Thread(
            target=processor._worker,
            args=(worker_id,),
            name=f"Worker-{worker_id}",
            daemon=True
        )
        thread.start()
        threads.append(thread)
        print(f"Started Worker-{worker_id}")

    time.sleep(10)
"""
  try:
      # 5. 发送请求
      request = PostAsyncInferRequest(
          contents=[
              Content(type=ContentType.TEXT, text="Hello, World!"),
              Content(
                  type=ContentType.IMAGE_URL,
                  image_url={"url": "datasets/ad-vlm/versions/0.1.1/data/front.jpg"}
              )
          ],
          model="qwen__qwen2_5-vl-72b-instruct"
      )

      response = client.post_async_infer(request)
      print(f"Task submitted: {response.data.task_id if response.data else 'Unknown'}")

      # 6. 批量请求
      batch_requests = [
          PostAsyncInferRequest(
              contents=[Content(type=ContentType.TEXT, text=f"Test {i}")]
          )
          for i in range(5)
      ]

      batch_responses = client.post_async_infer_batch(batch_requests)
      print(f"Batch submitted: {len(batch_responses)} tasks")

      # 让程序运行一段时间
      import time
      time.sleep(60)

  finally:
      # 7. 清理
      processor.stop()
      # task_queue.shutdown()
      client.close()
"""

if __name__ == "__main__":
    main()