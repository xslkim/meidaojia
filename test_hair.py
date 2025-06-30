import threading
import requests
import json
import base64
import time
import random

url = 'http://mq.aidigifi.meidaojia.com/api/swapHair/v1'
# url = 'https://692524911165445-http-8801.northwest1.gpugeek.com:8443/api/swapHair/v1'
# url = 'https://692502023221253-http-8801.northwest1.gpugeek.com:8443/api/swapHair/v1'
# url = 'https://692493464571909-http-8801.northwest1.gpugeek.com:8443/api/swapHair/v1'
headers = {'Content-Type': 'application/json'}
data = {
    "hair_id": "1907651680352395265",
    "task_id": "1907651680352395265",
    "user_img_path": "https://cdn.meidaojia.com/ZoeFiles/user2_1_%E5%89%AF%E6%9C%AC.JPG",
    # "user_img_path": "https://cdn.meidaojia.com/ZoeFiles/testuser_8.JPG",
    "is_hr": "false",
    "output_format": "base64"
}

more_data = []
more_data.append(data)

data1 = {
    "hair_id": "1907651680352395265",
    "task_id": "2345623451234",
    "user_img_path": "https://cdn.meidaojia.com/ZoeFiles/testuser_8.JPG",
    "is_hr": "false",
    "output_format": "base64"
}
more_data.append(data1)

data2 = {
    "hair_id": "1907651680352395265",
    "task_id": "3145645324",
    "user_img_path": "https://cdn.meidaojia.com/ZoeFiles/testuser_7.JPG",
    "is_hr": "false",
    "output_format": "base64"
}
more_data.append(data2)

data3 = {
    "hair_id": "1907651680352395265",
    "task_id": "456412345",
    "user_img_path": "https://cdn.meidaojia.com/ZoeFiles/testuser_6.JPG",
    "is_hr": "false",
    "output_format": "base64"
}
more_data.append(data3)

data4 = {
    "hair_id": "1907651680352395265",
    "task_id": "45623445",
    "user_img_path": "https://cdn.meidaojia.com/ZoeFiles/testuser_5.JPG",
    "is_hr": "false",
    "output_format": "base64"
}
more_data.append(data4)

data5 = {
    "hair_id": "1907651680352395265",
    "task_id": "2345867435",
    "user_img_path": "https://cdn.meidaojia.com/ZoeFiles/testuser_4.JPG",
    "is_hr": "false",
    "output_format": "base64"
}
more_data.append(data5)


data6 = {
    "hair_id": "1907651680352395265",
    "task_id": "86747535",
    "user_img_path": "https://cdn.meidaojia.com/ZoeFiles/testuser_3.JPG",
    "is_hr": "false",
    "output_format": "base64"
}
more_data.append(data6)

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

# 存储所有请求的响应
responses = []

# 线程锁，防止多线程写入冲突
lock = threading.Lock()


send_index = 0

def send_request(start_time):
    try:
        sleep_time = start_time #random.uniform(0, 2)  # 生成 [0, 2) 之间的随机浮点数
        time.sleep(sleep_time)
        global send_index
        send_data = more_data[send_index]
        # send_index = send_index + 1
        send_data['task_id'] = str(int(random.uniform(0, 10000000)))
        response = requests.post(url, headers=headers, json=send_data)
        with lock:  # 加锁，防止多线程同时修改 responses
            responses.append(response)
    except Exception as e:
        with lock:
            responses.append({"error": str(e)})

# 创建并启动多个线程
threads = []
num_requests = 80  # 并发请求数量

time_start = time.time()

start_time = 0
for _ in range(num_requests):
    # start_time = start_time + 1
    start_time = 0 # random.uniform(0, 1)
    t = threading.Thread(target=send_request, args=(start_time,))
    t.start()
    threads.append(t)

# 等待所有线程完成
for t in threads:
    t.join()

end_time = time.time()

total_time = (end_time - time_start)
qps = num_requests/total_time
print(qps)

# 打印所有响应
for i, resp in enumerate(responses, 1):
    print(f"请求 {i} 结果: {resp.status_code, resp.text[:128]}")