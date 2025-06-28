import time
import datetime
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
from config import QUEUE_NAME
from config import GPU_SERVER_LIST
from config import SERVER_LOG_EVENT_LEN
from config import SERVER_LOG_

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

def get_time():
    # 假设有一个时间戳
    timestamp = time.time()  # 当前时间戳

    # 转换为UTC时间
    utc_time = datetime.datetime.utcfromtimestamp(timestamp)

    # 转换为北京时间 (UTC+8)
    beijing_time = utc_time + datetime.timedelta(hours=8)

    # 格式化输出
    formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

def server_log_event(name, action, data):
    server_log_str = redis_conn.get(name).decode("utf-8")
    server_log = json.loads(server_log_str)
    event = {}
    event['time'] = time.time()
    event['time_str'] = get_time(time.time())
    event['action'] = action
    event['data'] = data
    if(len(server_log['events']) > SERVER_LOG_EVENT_LEN):
        server_log['events'].pop(0)
    server_log['events'].append(event)
    server_log['last_event'] = event
    server_log_str = json.dumps(server_log)
    redis_conn.set(f"{SERVER_LOG_}{name}", server_log_str)

def registerGpuServer(name, url, can_use):
    try:
        server_list_str = redis_conn.get(GPU_SERVER_LIST).decode("utf-8")
        server_list = json.loads(server_list_str)
        if name not in server_list:
            server_list.append(name)
        server = {}
        server['name'] = name
        server['url'] = url
        server['can_use'] = can_use
        server_str = json.dumps(server)
        logger.info(f"registerGpuServer, {server_str}")
        redis_conn.set(name, server_str)

        server_log = {}
        server_log['name'] = name
        event = {}
        event['time'] = time.time()
        event['time_str'] = get_time(time.time())
        event['action'] = "register"
        event['data'] = "url"
        server_log['last_event'] = event
        server_log['events'] = []
        if(len(server_log['events']) > SERVER_LOG_EVENT_LEN):
            server_log['events'].pop(0)
        server_log['events'].append(event)
        server_log_str = json.dumps(server_log)
        redis_conn.set(f"{SERVER_LOG_}{name}", server_log_str)

        redis_conn.set(GPU_SERVER_LIST, json.dumps(server_list))
    except Exception as e:
        logger.error(f"registerGpuServer{e.message}")


def get_remote_gpu_server():
    logger.info(f"call get_remote_gpu_server")
    start_time = datetime.now()
    while (datetime.now() - start_time).seconds < 20:
        server_list_str = redis_conn.get(GPU_SERVER_LIST).decode("utf-8")
        server_list = json.loads(server_list_str)
        for name in server_list:
            server_str = redis_conn.get(name).decode("utf-8")
            server = json.loads(server_str)
            if server['can_use']:
                return server
        time.sleep(0.1)
    return None

def call_remote_gpu_server(task_data_str):
    task_data = json.loads(task_data_str)
    key = task_data['key']
    server = get_remote_gpu_server()
    result_str = ''
    if server:
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            "hair_id": task_data['request']['hair_id'],
            "task_id": task_data['request']["task_id"],
            "user_img_path": task_data['request']['user_img_path'],
            "is_hr": task_data['request']['is_hr']
        }
        name = server['name']

        # set server busy
        server['can_use'] = False
        server_str = json.dumps(server)
        redis_conn.set(name, server_str)

        server_log_event(server['name'], "call", data)
        url = server['url']
        response = requests.post(url, headers=headers, json=data)

        # release server
        server['can_use'] = True
        server_str = json.dumps(server)
        redis_conn.set(name, server_str)
        
        result = response.json()
        server_log_event(server['name'], "call result", result)
        result_str = json.dumps(result)
    else:
        result_str = json.dumps({
            "state":-1,
            "data":"",
            "task_id":task_data['request']["task_id"],
            'msg': f'Timeout after no gpu server'
        })
    logger.info(f"call_remote_gpu_server {result_str}")
    result_key = f"result_{key}"
    redis_conn.set(result_key, result_str, ex=60)

def main_worker():
    while True:
        try:
            # 使用阻塞式弹出
            _, task_data_str = redis_conn.brpop(QUEUE_NAME, timeout=30)
            if task_data_str:
                threading.Thread(target=call_remote_gpu_server, args=(task_data_str,)).start()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(0.1)

if __name__ == '__main__':
    import os
    print(f"[Worker] Starting with PID: {os.getpid()}")
    redis_conn.set(GPU_SERVER_LIST, "[]")
    registerGpuServer("old_server", "http://js1.blockelite.cn:28559/api/swapHair/v1", True)
    registerGpuServer("test_server", "http://43.143.205.217:5000/api/swapHair/v1", False)
    main_worker()