import requests
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from threading import Lock

# 全局计数器
class RequestCounter:
    def __init__(self):
        self.sent = 0
        self.in_progress = 0
        self.completed = 0
        self.success = 0
        self.failed = 0
        self.lock = Lock()
    
    def increment_sent(self):
        with self.lock:
            self.sent += 1
    
    def increment_in_progress(self):
        with self.lock:
            self.in_progress += 1
    
    def decrement_in_progress(self):
        with self.lock:
            self.in_progress -= 1
    
    def increment_completed(self):
        with self.lock:
            self.completed += 1
    
    def increment_success(self):
        with self.lock:
            self.success += 1
    
    def increment_failed(self):
        with self.lock:
            self.failed += 1
    
    def get_stats(self):
        with self.lock:
            return {
                'sent': self.sent,
                'in_progress': self.in_progress,
                'completed': self.completed,
                'success': self.success,
                'failed': self.failed
            }

counter = RequestCounter()


def send_request(url, headers, data):
    """发送单个请求"""
    try:
        # 更新计数器
        counter.increment_sent()
        counter.increment_in_progress()
        
        response = requests.post(url, headers=headers, json=data)
        
        # 根据响应状态更新计数器
        if response.status_code == 200:
            counter.increment_success()
        else:
            counter.increment_failed()
            
        return response.status_code, response.text
    except Exception as e:
        counter.increment_failed()
        return None, str(e)
    finally:
        counter.decrement_in_progress()
        counter.increment_completed()

def print_stats():
    """打印实时统计信息"""
    while True:
        stats = counter.get_stats()
        print(f"\rStats - Sent: {stats['sent']}, In Progress: {stats['in_progress']}, "
              f"Completed: {stats['completed']} (Success: {stats['success']}, Failed: {stats['failed']})", 
              end="", flush=True)
        time.sleep(10)

def worker(url, headers, data, qps, duration):
    """工作线程函数，控制QPS"""
    requests_count = 0
    start_time = time.time()
    end_time = start_time + duration
    
    while time.time() < end_time:
        request_start = time.time()
        status_code, response_text = send_request(url, headers, data)
        requests_count += 1
        
        # 控制QPS
        elapsed = time.time() - request_start
        sleep_time = max(0, (1.0 / qps) - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    return requests_count

def run_test(url, headers, data, qps, duration, concurrency):
    """运行测试"""
    total_requests = 0
    start_time = time.time()
    
    # 启动统计信息打印线程
    import threading
    stats_thread = threading.Thread(target=print_stats, daemon=True)
    stats_thread.start()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker, url, headers, data, qps, duration) 
                  for _ in range(concurrency)]
        
        for future in as_completed(futures):
            total_requests += future.result()
    
    end_time = time.time()
    actual_duration = end_time - start_time
    actual_qps = total_requests / actual_duration
    
    # 获取最终统计
    stats = counter.get_stats()
    
    print("\n\nTest Summary:")
    print(f"Total requests: {total_requests}")
    print(f"  Success: {stats['success']}")
    print(f"  Failed: {stats['failed']}")
    print(f"Success rate: {(stats['success']/total_requests)*100:.2f}%")
    print(f"Test duration: {actual_duration:.2f} seconds")
    print(f"Actual QPS: {actual_qps:.2f}")
    print(f"Target QPS: {qps}")
    print(f"Concurrency: {concurrency}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='API Load Test Tool')
    parser.add_argument('--qps', type=float, default=1, help='Requests per second (per thread)')
    parser.add_argument('--duration', type=float, default=10, help='Test duration in seconds')
    parser.add_argument('--concurrency', type=int, default=2, help='Number of concurrent threads')
    
    args = parser.parse_args()
    
    # 配置请求参数
    url = 'http://mq.aidigifi.meidaojia.com/hairColor/v2'
    # url = 'https://692139771842565-http-8801.northwest1.gpugeek.com:8443/hairColor/v2'
    headers = {'Content-Type': 'application/json'}
    data =  {
        "img": "data:image/jpeg;base64,/9j/4AAQSkZJ....Euy+sn/oZrKn8CPlK2qR/9k=",
        "userId": "18701620166",
        "rgb":[77,99,0],
        "ratio": 0.9,
        "output_format": "base64"
    }
    
    print(f"Starting test with QPS={args.qps}, duration={args.duration}s, concurrency={args.concurrency}")
    run_test(url, headers, data, args.qps, args.duration, args.concurrency)