import time
import logging
import redis
import uuid
import json
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timedelta
from config import QUEUE_NAME, DEFAULT_TIMEOUT
from flask_cors import CORS
GPU_SERVER_LIST = 'gpu_server_list_key'

# 创建 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置 logger 的级别

# 创建文件 handler
file_handler = logging.FileHandler('/var/log/meidaojia/app.log')
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

monitor = Flask(__name__)
CORS(monitor)  

# 配置
from config import REDIS_HOST
from config import REDIS_PORT
from config import REDIS_DB
from config import SERVER_LOG_

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

@monitor.route('/get_server_state', methods=['GET', 'POST'])
def get_server_state():
    monitor_data = []
    redis_conn = get_redis_conn()
    server_list_str = redis_conn.get(GPU_SERVER_LIST).decode("utf-8")
    server_list = json.loads(server_list_str)
    for name in server_list:
        server_str = redis_conn.get(name).decode("utf-8")
        server = json.loads(server_str)

        server_log_name = f"{SERVER_LOG_}{name}"
        server_log_str = redis_conn.get(server_log_name).decode("utf-8")
        server_log = json.loads(server_log_str)
        server_log['busy'] = not server['can_use']
        monitor_data.append(server_log)
    json_str = json.dumps(monitor_data)
    print(len(json_str))
    return json_str, 200


@monitor.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    # 启动Flask应用，启用多线程处理
    monitor.run(
        host='0.0.0.0',
        port=5001,
        threaded=True,  # 启用多线程处理并发请求
        debug=False    # 生产环境应设置为False
    )