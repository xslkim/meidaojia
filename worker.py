import time
import random
import sys
import redis
import logging
import requests
import threading
import json
from datetime import datetime

from config import REDIS_HOST
from config import REDIS_PORT
from config import REDIS_DB
from config import DEFAULT_TIMEOUT
from config import MAX_WAIT
from config import QUEUE_NAME
from config import GPU_SERVER_LIST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 Redis 连接池
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    db=REDIS_DB,
    max_connections=2000  # 根据实际情况调整
)

def get_redis_conn():
    """获取 Redis 连接"""
    return redis.Redis(connection_pool=redis_pool)

redis_conn = get_redis_conn()


def registerGpuServer(name, url):
    
    if not redis_conn.exists(GPU_SERVER_LIST):
        redis_conn.set(GPU_SERVER_LIST, "[]")
    server_list = json.decoder(redis_conn.get(GPU_SERVER_LIST))
    if name not in server_list:
        server_list.add(name)
    server = {}
    server['name'] = name
    server['url'] = url
    server['is_idle'] = True
    server_str = json.encoder(server)
    logger.info(f"registerGpuServer, {server_str}")
    redis_conn.set(name, server_str)

def registerGpuServer():
    registerGpuServer("old_server", "http://js1.blockelite.cn:28559/api/swapHair/v1")

def get_remote_gpu_server():
    logger.info(f"call get_remote_gpu_server")
    start_time = datetime.now()
    server_url = None
    while (datetime.now() - start_time).seconds < 20:
        server_list = json.decoder(redis_conn.get(GPU_SERVER_LIST))
        for name in server_list:
            server = json.decoder(redis_conn.get(name))
            if server['is_idel']:
                return server['url']
        time.sleep(0.1)
    return server_url

def call_remote_gpu_server(task_data_str):
    task = json.loads(task_data_str)
    key = task['key']
    url = get_remote_gpu_server()
    result_str = ''
    if url:
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            "hair_id": task['hair_id'],
            "task_id": task["task_id"],
            "user_img_path": task['user_img_path'],
            "is_hr": task['is_hr']
        }

        response = requests.post(url, headers=headers, json=data)
        result_str = response.json()
    else:
        result_str = json.encoder({
            'status': 'timeout',
            'message': f'Timeout after no gpu server'
        })
    result_key = f"result_{key}"
    redis_conn.set(result_key, result_str)

def main_worker():
    while True:
        try:
            # 使用阻塞式弹出
            _, task_data_str = redis_conn.brpop(QUEUE_NAME, timeout=30)
            if task_data_str:
                threading.Thread(target=call_remote_gpu_server, args=(task_data_str,)).start()
        except redis.exceptions.TimeoutError:
            logger.info("No messages for 30 seconds, still alive...")
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error: {e}")
            time.sleep(5)  # 等待后重试
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    import os
    print(f"[Worker] Starting with PID: {os.getpid()}")
    registerGpuServer()
    main_worker()