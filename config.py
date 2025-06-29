import time

QUEUE_NAME = 'task_queue'
# 配置
REDIS_HOST = '172.21.0.15'
REDIS_PORT = 6379
REDIS_DB = 0
DEFAULT_TIMEOUT = 60  # 默认超时时间30秒
GPU_SERVER_LIST = 'gpu_server_list_key'
SERVER_LOG_ = "server_log"
SERVER_LOG_EVENT_LEN = 100
TASK_REDIS_LOCK = 'TASK_REDIS_LOCK'

def acquire_lock(r, acquire_timeout=10):
    """获取分布式锁"""
    # end = time.time() + acquire_timeout
    # while time.time() < end:
    #     # 使用 SETNX 尝试获取锁
    #     if r.setnx(TASK_REDIS_LOCK, 1):
    #         # 设置过期时间，防止死锁
    #         r.expire(TASK_REDIS_LOCK, 10)
    #         return True
    #     time.sleep(0.1)
    # return False
    return True

def release_lock(r):
    """释放分布式锁"""
    # r.delete(TASK_REDIS_LOCK)
