import time
import threading
import redis
import uuid
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from config import QUEUE_NAME

app = Flask(__name__)

# 配置
from config import REDIS_HOST
from config import REDIS_PORT
from config import REDIS_DB
from config import DEFAULT_TIMEOUT
from config import MAX_WAIT

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


@app.route('/api/swapHair/v1', methods=['POST'])
def api_swapHair_v1():
    # 获取请求参数
    data = request.get_json()
    if not data or 'hair_id' not in data:
        return jsonify({'error': 'Missing hair_id parameter'}), 400
    if not data or 'task_id' not in data:
        return jsonify({'error': 'Missing task_id parameter'}), 400
    if not data or 'user_img_path' not in data:
        return jsonify({'error': 'Missing user_img_path parameter'}), 400
    if not data or 'is_hr' not in data:
        return jsonify({'error': 'Missing is_hr parameter'}), 400

    key = str(uuid.uuid4())
    redis_conn = get_redis_conn()
    task_data = {}
    task_data['key'] = key
    task_data['request'] = data
    task_data_str = json.dumps(task_data)
    redis_conn.lpush(QUEUE_NAME, task_data_str)
    timeout = 60
    start_time = datetime.now()
    result_key = f"result_{key}"
    while (datetime.now() - start_time).seconds < timeout:
        if redis_conn.exists(result_key):
            result_str = redis_conn.get(result_key)
            return result_str
        time.sleep(0.1) 

    return jsonify({
            'status': 'timeout',
            'message': f'Timeout after {timeout} seconds, http time out'
        }), 408



@app.route('/wait_for_success', methods=['POST'])
def wait_for_success():
    # 获取请求参数
    data = request.get_json()
    if not data or 'key' not in data:
        return jsonify({'error': 'Missing key parameter'}), 400
    
    key = data['key']
    timeout = int(data.get('timeout', DEFAULT_TIMEOUT))
    timeout = min(timeout, MAX_WAIT)  # 限制最大等待时间
    
    redis_conn = get_redis_conn()
    start_time = datetime.now()
    
    # 检查 key 是否存在
    if not redis_conn.exists(key):
        return jsonify({'error': 'Key not found'}), 404
    
    # 初始检查
    current_value = redis_conn.get(key)
    if current_value and current_value.decode('utf-8') == 'success':
        return jsonify({
            'status': 'success',
            'key': key,
            'waited_seconds': 0
        })
    
    # 设置发布/订阅
    pubsub = redis_conn.pubsub()
    pubsub.subscribe(f'channel:{key}')
    
    try:
        # 等待通知或超时
        while (datetime.now() - start_time).seconds < timeout:
            # 非阻塞检查消息
            message = pubsub.get_message(timeout=(timeout - (datetime.now() - start_time).seconds))
            
            # 检查当前值（防止错过通知）
            current_value = redis_conn.get(key)
            if current_value and current_value.decode('utf-8') == 'success':
                return jsonify({
                    'status': 'success',
                    'key': key,
                    'waited_seconds': (datetime.now() - start_time).seconds
                })
            
            if message:
                if message['type'] == 'message' and message['data'].decode('utf-8') == 'success':
                    return jsonify({
                        'status': 'success',
                        'key': key,
                        'waited_seconds': (datetime.now() - start_time).seconds
                    })
            
            time.sleep(0.1)  # 短暂睡眠减少CPU使用
        
        # 超时处理
        return jsonify({
            'status': 'timeout',
            'key': key,
            'waited_seconds': (datetime.now() - start_time).seconds,
            'message': f'Timeout after {timeout} seconds'
        }), 408
        
    finally:
        pubsub.unsubscribe()
        pubsub.close()

@app.route('/set_redis_value', methods=['POST'])
def set_redis_value():
    data = request.get_json()
    if not data or 'key' not in data or 'value' not in data:
        return jsonify({'error': 'Missing key or value parameter'}), 400
    
    key = data['key']
    value = data['value']
    redis_conn = get_redis_conn()
    
    # 设置值并发布通知
    with redis_conn.pipeline() as pipe:
        pipe.set(key, value)
        if value == 'success':
            pipe.publish(f'channel:{key}', 'success')
        pipe.execute()
    
    return jsonify({
        'status': 'set',
        'key': key,
        'value': value,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # 启动Flask应用，启用多线程处理
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True,  # 启用多线程处理并发请求
        debug=False    # 生产环境应设置为False
    )