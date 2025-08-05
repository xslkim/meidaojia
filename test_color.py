import threading
import requests
import json
import base64
import time
import random


# url = 'http://172.17.110.92/hairColor/v2'
url = 'https://693565557084165-http-8801.northwest1.gpugeek.com:8443/hairColor/v2'



headers = {'Content-Type': 'application/json'}
data =  {
    "img": "data:image/jpeg;base64,/9j/4AAQSkZJ....Euy+sn/oZrKn8CPlK2qR/9k=",
    "userId": "18701620166",
    "rgb":[77,99,0],
    "ratio": 0.9,
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
data['img'] = img64_str

# 存储所有请求的响应
responses = []
responses_time = []

# 线程锁，防止多线程写入冲突
lock = threading.Lock()


def send_request():
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data)
        end_time = time.time()
        response_time = end_time - start_time
        print(f"相应时间:{response_time}")
        result = response.json()
        if 'state' in result:
            if result['state'] != 0:
                print(f"请求失败: {result}")
                time.sleep(5)
        with lock:  # 加锁，防止多线程同时修改 responses
            responses.append(response)
            responses_time.append(response_time)
    except Exception as e:
       with lock:
            error_msg = {"error": str(e)}
            responses.append(error_msg)
            print(f"请求失败: {error_msg}")  # 打印错误信息
            time.sleep(5)  # 延时5秒

# 创建并启动多个线程
threads = []
num_requests = 1  # 并发请求数量
test_rand_num = 1

time_start = time.time()

for _ in range(test_rand_num):
    for _ in range(num_requests):
        t = threading.Thread(target=send_request)
        t.start()
        threads.append(t)

    # 等待所有线程完成
    for t in threads:
        t.join()


end_time = time.time()

total_time = (end_time - time_start)
qps = (num_requests*test_rand_num)/total_time
print(f"num_requests:{num_requests} total_time:{total_time} qps:{qps}")

totalReqTime = 0
for t in responses_time:
    totalReqTime += t
avgTime = totalReqTime/len(responses_time)
print(f"平均相应时间:{avgTime}")



# 打印所有响应
for i, resp in enumerate(responses, 1):
    print(f"请求 {i} 结果:", {resp.status_code, resp.text[:128]})

print(f"num_requests:{num_requests} total_time:{total_time} qps:{qps}")
print(f"平均相应时间:{avgTime}")