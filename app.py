import time
import logging
import redis
import uuid
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from config import QUEUE_NAME, DEFAULT_TIMEOUT, release_lock, acquire_lock

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

app = Flask(__name__)

# 配置
from config import REDIS_HOST
from config import REDIS_PORT
from config import REDIS_DB


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

get_redis_conn().set(QUEUE_NAME, "[]")

def pushStr2Queue(str):
    redis_conn = get_redis_conn()
    acquire_lock(redis_conn)
    task_queue_str = redis_conn.get(QUEUE_NAME).decode("utf-8")
    task_queue = json.loads(task_queue_str)
    task_queue.append(str)
    task_queue_str = json.dumps(task_queue)
    redis_conn.set(QUEUE_NAME, task_queue_str)
    release_lock(redis_conn)
    

@app.route('/api/uploadHair/v1', methods=['POST'])
def api_uploadHair_v1():
    # 获取请求参数
    data = request.get_json()
    if not data or 'img_lists' not in data:
        return jsonify({'msg': 'Missing img_lists parameter', "state":-1, "data":"" }), 400
    if not data or '"hair_id": ' not in data:
        return jsonify({'msg': 'Missing "hair_id":  parameter', "state":-1, "data":""}), 400
    
    if not data or 'output_format' not in data:
        logger.warning(f"api_swapHair_v1 no output_format task_id:{data['task_id']}")
    

    key = str(uuid.uuid4())
    redis_conn = get_redis_conn()
    task_data = {}
    task_data['key'] = key
    task_data['api'] = "/api/uploadHair/v1"
    task_data['request'] = data
    logger.info(f"request api_uploadHair_v1 task_data: {json.dumps(task_data)}")
    task_data_str = json.dumps(task_data)
    pushStr2Queue(task_data_str)
    timeout = DEFAULT_TIMEOUT
    start_time = datetime.now()
    result_key = f"result_{key}"
    while (datetime.now() - start_time).seconds < timeout:
        if redis_conn.exists(result_key):
            result_str = redis_conn.get(result_key)
            result = json.loads(result_str)
            if result['state'] == 0:
                return jsonify(result), 200
            else:
                return jsonify(result), 500
        time.sleep(0.1) 

    logger.error(f"request api_uploadHair_v1 time out")
    return jsonify({
            'msg': f'Timeout after {timeout} seconds, http time out'
            , "state":-1, "data":""
        }), 408


@app.route('/api/swapHair/v1', methods=['POST'])
def api_swapHair_v1():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    # 获取请求参数
    data = request.get_json()
    if not data or 'hair_id' not in data:
        return jsonify({'msg': 'Missing hair_id parameter', "state":-1, "data":"" }), 400
    if not data or 'task_id' not in data:
        return jsonify({'msg': 'Missing task_id parameter', "state":-1, "data":""}), 400
    if not data or 'user_img_path' not in data:
        return jsonify({'msg': 'Missing user_img_path parameter', "state":-1, "data":""}), 400
    if not data or 'is_hr' not in data:
        return jsonify({'msg': 'Missing is_hr parameter', "state":-1, "data":""}), 400
    
    if not data or 'output_format' not in data:
        logger.warning(f"api_swapHair_v1 no output_format task_id:{data['task_id']}")
    
    redis_conn = get_redis_conn()
    key = str(uuid.uuid4())
    if len(data['user_img_path']) > 256:
        redis_conn.set(f"img_{key}", data['user_img_path'], ex=60)
        data['user_img_path'] = "base64"

    task_data = {}
    task_data['key'] = key
    task_data['api'] = "/api/swapHair/v1"
    task_data['request'] = data
    logger.info(f"request api_swapHair_v1 task_data: {json.dumps(task_data)}")
    task_data_str = json.dumps(task_data)
    pushStr2Queue(task_data_str)
    timeout = DEFAULT_TIMEOUT
    start_time = datetime.now()
    result_key = f"result_{key}"
    while (datetime.now() - start_time).seconds < timeout:
        if redis_conn.exists(result_key):
            result_str = redis_conn.get(result_key)
            return result_str, 200, {'Content-Type': 'application/json'}
        time.sleep(0.1) 

    logger.error(f"request api_swapHair_v1 time out {data['task_id']}")
    return jsonify({
            'msg': f'Timeout after {timeout} seconds, http time out'
            , "state":-1, "data":""
        }), 408


if __name__ == '__main__':
    # 启动Flask应用，启用多线程处理
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True,  # 启用多线程处理并发请求
        debug=False    # 生产环境应设置为False
    )