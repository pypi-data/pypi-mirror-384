import time
from .task_queue import TaskQueue

class QueueMonitor:
    def __init__(self, task_queue: TaskQueue, max_duration: int = 3600, check_interval: int = 30):
        self.task_queue = task_queue
        self.max_duration = max_duration
        self.check_interval = check_interval
        self.start_time = None

    def monitor(self) -> str:
        self.start_time = time.time()

        while True:
            # 检查是否超时
            if time.time() - self.start_time >= self.max_duration:
                print(f"已运行满{self.max_duration}秒，退出...")
                return "timeout"

            queue_size = len(self.task_queue.queue)
            if queue_size == 0:
                print("队列为空，等待5秒确认...")
                time.sleep(5)
                # 再次检查
                if len(self.task_queue.queue) == 0:
                    print("队列确认为空，退出...")
                    return "empty"
            else:
                elapsed = time.time() - self.start_time
                remaining = self.max_duration - elapsed
                print(f"队列还有 {queue_size} 个任务，已运行 {elapsed:.0f}秒，剩余 {remaining:.0f}秒...")
                time.sleep(self.check_interval)

    def get_elapsed_time(self) -> float:
        """获取已运行时间（秒）"""
        if self.start_time:
            return time.time() - self.start_time
        return 0

    def get_queue_size(self) -> int:
        """获取当前队列大小"""
        return len(self.task_queue.queue)