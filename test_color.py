import threading
import requests
import json
import base64


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

# 线程锁，防止多线程写入冲突
lock = threading.Lock()


def send_request():
    try:
        response = requests.post(url, headers=headers, json=data)
        with lock:  # 加锁，防止多线程同时修改 responses
            responses.append(response.json())
    except Exception as e:
        with lock:
            responses.append({"error": str(e)})

# 创建并启动多个线程
threads = []
num_requests = 1  # 并发请求数量

for _ in range(num_requests):
    t = threading.Thread(target=send_request)
    t.start()
    threads.append(t)

# 等待所有线程完成
for t in threads:
    t.join()

# 打印所有响应
for i, resp in enumerate(responses, 1):
    print(f"请求 {i} 结果:", resp)