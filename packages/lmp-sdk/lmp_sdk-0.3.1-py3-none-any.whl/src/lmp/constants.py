# API 端点
DEFAULT_API_ENDPOINT = "https://lpai.lixiang.com/lpai/api/lpai-service-lmp/async_infer"
BASE_GET_URL = "https://lpai.lixiang.com/lpai/api/lpai-service-lmp"

# 默认模型
DEFAULT_MODEL = "qwen__qwen2_5-vl-72b-instruct"

# 默认参数
DEFAULT_TEMPERATURE = 0.000001
DEFAULT_FREQUENCY_PENALTY = 1.05
DEFAULT_MAX_RETRIES = 5
DEFAULT_POLLING_INTERVAL = 10  # 秒
DEFAULT_MAX_WAIT_TIME = 86400  # 24小时（秒）
DEFAULT_MAX_QUEUE_SIZE = 100000
DEFAULT_WORKER_NUM = 5