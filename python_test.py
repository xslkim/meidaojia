import threading
import requests
import json
import base64

url = 'http://mq.aidigifi.meidaojia.com/api/swapHair/v1'
# url = 'https://692139771842565-http-8801.northwest1.gpugeek.com:8443/api/swapHair/v1'
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

def image_to_base64(image_path):
    """读取图片文件并转换为Base64编码"""
    with open(image_path, "rb") as image_file:
        # 读取图片二进制数据
        image_data = image_file.read()
        # 转换为Base64编码的bytes
        base64_bytes = base64.b64encode(image_data)
        # 转换为字符串（如果需要）
        base64_string = base64_bytes.decode('utf-8')
        return base64_string

# img64_str = image_to_base64("test_image.jfif")
# data['user_img_path'] = img64_str

# 存储所有请求的响应
responses = []

# 线程锁，防止多线程写入冲突
lock = threading.Lock()


send_index = 0

def send_request():
    try:
        global send_index
        send_data = more_data[send_index]
        send_index = send_index + 1
        response = requests.post(url, headers=headers, json=send_data)
        with lock:  # 加锁，防止多线程同时修改 responses
            responses.append(response.json())
    except Exception as e:
        with lock:
            responses.append({"error": str(e)})

# 创建并启动多个线程
threads = []
num_requests = 7  # 并发请求数量

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