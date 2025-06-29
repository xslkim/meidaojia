import time
import datetime
import uuid
import redis
import logging
import requests
import threading
import json
from datetime import datetime, timedelta

from config import REDIS_HOST
from config import REDIS_PORT
from config import REDIS_DB
from config import QUEUE_NAME
from config import GPU_SERVER_LIST
from config import SERVER_LOG_EVENT_LEN
from config import SERVER_LOG_

import logging

# 创建 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置 logger 的级别

# 创建文件 handler
file_handler = logging.FileHandler('/var/log/meidaojia/worker.log')
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

def get_time(timestamp):
    # 转换为UTC时间
    utc_time = datetime.utcfromtimestamp(timestamp)  

    # 转换为北京时间 (UTC+8)
    beijing_time = utc_time + timedelta(hours=8)  # 正确

    # 格式化输出
    formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

def server_log_event(name, action, log_data):
    server_log_name = f"{SERVER_LOG_}{name}"
    server_log_str = redis_conn.get(server_log_name).decode("utf-8")
    server_log = json.loads(server_log_str)
    event = {}
    t = time.time()
    event['time'] = t
    event['time_str'] = get_time(t)
    event['action'] = action
    if 'data' in log_data:
        if len(log_data['data']) > 256:
            log_data['data'] = log_data['result'][:32]
    server_log['last_call'] = "success"
    if 'state' in log_data:
        if log_data['state'] != 0:
            server_log['last_call'] = "failure"
    event['data'] = log_data
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
        t = time.time()
        event['time'] = t 
        event['time_str'] = get_time(t)
        event['action'] = "register"
        event['data'] = f"url {url}"
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

def call_remote_gpu_server(task_data_str, server=None):
    task_data = json.loads(task_data_str)
    key = task_data['key']
    if server == None:
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
            "is_hr": task_data['request']['is_hr'],
            "output_format":task_data['request']['output_format']
        }
        name = server['name']

        # set server busy
        server['can_use'] = False
        server_str = json.dumps(server)
        redis_conn.set(name, server_str)

        server_log_event(server['name'], "call", data)
        url = server['url'] + task_data['api']
        response = requests.post(url, headers=headers, json=data, timeout=30)

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
    logger.info(f"call_remote_gpu_server task:{task_data_str}  result:{result_str}")
    result_key = f"result_{key}"
    redis_conn.set(result_key, result_str, ex=60)

def check_server_work_call(server):
    task_data = {}
    request = {}
    request['hair_id'] = "1907651680352395265"
    request['task_id'] = "1907651680352395265"
    request['user_img_path'] = "https://cdn.meidaojia.com/ZoeFiles/user2_1_%E5%89%AF%E6%9C%AC.JPG"
    request['output_format'] = "url"
    request['is_hr'] = "false"
    task_data['request'] = request
    key = str(uuid.uuid4())
    task_data['key'] = key
    task_data['api'] = "/api/uploadHair/v1"
    task_data_str = json.dumps(task_data)
    call_remote_gpu_server(task_data_str, server)

def check_server_work():
    server_list_str = redis_conn.get(GPU_SERVER_LIST).decode("utf-8")
    server_list = json.loads(server_list_str)
    for name in server_list:
        server_str = redis_conn.get(name).decode("utf-8")
        server = json.loads(server_str)
        if not server['can_use']:
            continue

        server_log_name = f"{SERVER_LOG_}{name}"
        server_log_str = redis_conn.get(server_log_name).decode("utf-8")
        server_log = json.loads(server_log_str)
        if time.time() - server_log['last_event']['time'] > (1*60):
            logger.info("check_server_work and call name")
            check_server_work_call(server)


def main_worker():
    while True:
        try:
            # _, task_data_str = redis_conn.brpop(QUEUE_NAME, timeout=30)
            task_data_str = redis_conn.rpop(QUEUE_NAME)
            if task_data_str:
                threading.Thread(target=call_remote_gpu_server, args=(task_data_str,)).start()
                continue
        except Exception as e:
            logger.info(f"main_worker redis_conn.rpop(QUEUE_NAME): {e}")
        check_server_work()
        time.sleep(0.1)

if __name__ == '__main__':
    import os
    print(f"[Worker] Starting with PID: {os.getpid()}")
    redis_conn.set(GPU_SERVER_LIST, "[]")
    registerGpuServer("old_server", "http://js1.blockelite.cn:28559", True)
    registerGpuServer("test_server", "http://43.143.205.217:5000", False)
    registerGpuServer("new_server", "https://692139771842565-http-8801.northwest1.gpugeek.com:8443", False)
    main_worker()