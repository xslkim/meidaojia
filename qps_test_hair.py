import requests
import random
import time
import concurrent.futures
import base64
from collections import defaultdict

url = 'http://172.17.110.92/api/swapHair/v1'
# url = 'https://699520645652485-http-8801.northwest1.gpugeek.com:8443/api/swapHair/v1'

headers = {'Content-Type': 'application/json'}
data = {
    "hair_id": "1907651680352395265",
    "task_id": "1907651680352395265",
    "user_img_path": "https://cdn.meidaojia.com/ZoeFiles/user2_1_%E5%89%AF%E6%9C%AC.JPG",
    "is_hr": "false",
    "output_format": "base64"
}

def image_to_base64(file_path, mime_type=None):
    """
    将图片文件转换为带Base64前缀的Data URI字符串
    
    参数:
        file_path (str): 图片文件路径
        mime_type (str): 可选，指定MIME类型。如果为None，则根据文件扩展名自动判断
    
    返回:
        str: 带Base64前缀的Data URI字符串
    """
    # 如果没有指定MIME类型，根据文件扩展名推断
    if mime_type is None:
        extension = file_path.split('.')[-1].lower()
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp'
        }
        mime_type = mime_types.get(extension, 'application/octet-stream')
    
    # 读取文件内容并编码为Base64
    with open(file_path, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    # 组合成Data URI格式
    return f"data:{mime_type};base64,{encoded_string}"

img64_str = image_to_base64("aaa.jpg")
data['user_img_path'] = img64_str

class RequestStats:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.start_time = None
        self.end_time = None
        self.request_timestamps = defaultdict(int)
    
    def record_success(self, response_time):
        self.successful_requests += 1
        self.response_times.append(response_time)
        self.request_timestamps[int(time.time())] += 1
    
    def record_failure(self):
        self.failed_requests += 1
    
    def calculate_qps(self):
        if not self.request_timestamps:
            return 0
        timestamps = sorted(self.request_timestamps.keys())
        if len(timestamps) < 2:
            return self.successful_requests
        total_time = timestamps[-1] - timestamps[0] + 1
        return self.successful_requests / total_time

def send_request(stats):
    try:
        data['task_id'] = str(int(random.uniform(0, 10000000)))
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data)
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            stats.record_success(response_time)
            print(f"请求完成，响应时间: {response_time:.3f} 秒")
            return response_time
        else:
            print(f"请求失败，状态码: {response.status_code}")
            stats.record_failure()
            return None
    except Exception as e:
        print(f"请求发生错误: {e}")
        stats.record_failure()
        return None

def main():
    total_requests = 100  #请求总数
    concurrency = 25  # 并发数
    
    stats = RequestStats()
    stats.start_time = time.time()
    stats.total_requests = total_requests
    
    print(f"开始测试，总请求数: {total_requests}，并发数: {concurrency}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_request, stats) for _ in range(total_requests)]
        concurrent.futures.wait(futures)
    
    stats.end_time = time.time()
    
    print("\n统计结果:")
    print(f"总请求数: {stats.total_requests}")
    print(f"成功请求数: {stats.successful_requests}")
    print(f"失败请求数: {stats.failed_requests}")
    
    if stats.successful_requests > 0:
        total_time = stats.end_time - stats.start_time
        avg_response_time = sum(stats.response_times) / len(stats.response_times)
        qps = stats.calculate_qps()
        
        print(f"测试总时间: {total_time:.3f} 秒")
        print(f"平均响应时间: {avg_response_time:.3f} 秒")
        print(f"最大响应时间: {max(stats.response_times):.3f} 秒")
        print(f"最小响应时间: {min(stats.response_times):.3f} 秒")
        print(f"QPS (每秒查询率): {qps:.2f}")
    else:
        print("所有请求都失败了，无法计算统计信息")

if __name__ == "__main__":
    main()