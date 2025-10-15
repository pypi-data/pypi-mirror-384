import logging
from lmp import (
    Client,
    TaskResponse,
    TaskProcessor,
    Content,
    ContentType,
    PostAsyncInferRequest,
    QueueMonitor
)

# 配置日志
logging.basicConfig(level=logging.INFO)


def main():

    # 1. 创建客户端
    worker_num = 100
    client = Client(
        token="ak-infer-bHBhaS1sbXA6bnhtamZoOm54bWpmaC1kZWZhdWx0OnpoYW5neGlucmFuM0BsaXhpYW5nLmNvbTppbmZlcg_NzMzNTcxNTktNmVlMC00MjU1LThjYzAtZmFmMDllZTRlNGM1",
        worker_num=worker_num,
        timeout=3600
    )

    # 结果列表
    results = []
    def callback_fn(resp: TaskResponse):
        print("Callback: get prediction result ", resp)
        results.append(resp)

    # 2. 创建任务处理器
    processor = TaskProcessor(
        client=client,
        worker_num=worker_num,
        callback=callback_fn
        #lambda response: print(f"Task completed success: {response.data.task_id if response.data else 'Unknown'}")
    )
    processor.start()

    try:
        # 3. 单个请求
        request = PostAsyncInferRequest(
            contents=[
                Content(type=ContentType.TEXT, text="Hello, World!"),
                Content(
                    type=ContentType.IMAGE_URL,
                    image_url={"url": "datasets/ai-pictures/versions/0.1.0/0701-0707/1751332643437.png"}
                )
            ],
            model="qwen__qwen2_5-vl-72b-instruct" # 模型
        )

        response = client.post_async_infer(request)
        print(f"Task submitted: {response.data.task_id if response.data else 'Unknown'}")

        # 4. 批量请求
        batch_requests = [
            PostAsyncInferRequest(
                contents=[Content(type=ContentType.TEXT, text=f"Test {i}")],
                model="qwen__qwen2_5-vl-72b-instruct" # 模型
            )
            for i in range(10)
        ]

        batch_responses = client.post_async_infer_batch(batch_requests)
        queue_size = len(client.get_task_queue().queue)
        print(f"Batch submitted: {len(batch_responses)} tasks")
        print(f"Queue has {queue_size} tasks, waiting...")

        # 5. 创建监控器并运行
        monitor = QueueMonitor(client.get_task_queue(), max_duration=3600)  # 3600秒超时
        exit_reason = monitor.monitor()

        print(f"监控结束，退出原因: {exit_reason}")
        print(f"总运行时间: {monitor.get_elapsed_time():.1f}秒")
        print(f"执行结果:{results}，总数: {len(results)}")

    finally:
        # 6. 清理
        processor.stop()
        #task_queue.shutdown()
        client.close()


if __name__ == "__main__":
    main()
