QUEUE_NAME = 'task_queue'
# 配置
REDIS_HOST = '172.21.0.10'
REDIS_PORT = 6379
REDIS_DB = 0
DEFAULT_TIMEOUT = 60  # 默认超时时间30秒
MAX_WAIT = 300        # 最大等待时间300秒（5分钟）
GPU_SERVER_LIST = 'gpu_server_list_key'