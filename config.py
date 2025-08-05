import time
from redis.lock import Lock
import logging

QUEUE_NAME = 'task_queue'
# 配置
REDIS_HOST = 'r-2zevknj33pkqrrbzjp.redis.rds.aliyuncs.com'
REDIS_PORT = 6379
REDIS_DB = 0
DEFAULT_TIMEOUT = (60+10)
GPU_SERVER_TIME_OUT = 60
GPU_SERVER_LIST = 'gpu_server_list_key'
SERVER_LOG_ = "server_log"
SERVER_LOG_EVENT_LEN = 20
KEY_QUEUE_LOCK_NAME = 'KEY_QUEUE_LOCK_NAME'
SERVER_LIST_LOCK_NAME = 'SERVER_LIST_LOCK_NAME'
SERVER_LIST_LOG_LOCK_NAME = 'SERVER_LIST_LOG_LOCK_NAME'

# 创建 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置 logger 的级别

# 创建文件 handler
file_handler = logging.FileHandler('/var/log/meidaojia/config.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 创建控制台 handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# 添加 handlers 到 logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def acquire_lock(redis_client, lock_name):
    lock = Lock(
        redis_client,
        name=lock_name,
        timeout=30,
        blocking_timeout=10
    )
    acquired = lock.acquire()
    if acquired:
        return lock
    return None



# def acquire_lock(r, acquire_timeout=10):
#     """获取分布式锁"""
#     end = time.time() + acquire_timeout
#     while time.time() < end:
#         # 使用 SETNX 尝试获取锁
#         if r.setnx(TASK_REDIS_LOCK_NAME, 1):
#             # 设置过期时间，防止死锁
#             r.expire(TASK_REDIS_LOCK_NAME, 10)
#             return True
#         time.sleep(0.1)
#     return False
#     # return True

# def release_lock(r):
#     """释放分布式锁"""
#     r.delete(TASK_REDIS_LOCK_NAME)
