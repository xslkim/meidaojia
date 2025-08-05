import requests
import random
import time
import base64

# url = 'https://693565319933957-http-8801.northwest1.gpugeek.com:8443/api/swapHair/v1'
url = 'http://172.17.110.92/api/swapHair/v1'

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

# img64_str = image_to_base64("aaa.jpg")
# data['user_img_path'] = img64_str

def send_request():
    try:
        data['task_id'] = str(int(random.uniform(0, 10000000)))
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data)
        end_time = time.time()
        response_time = end_time - start_time
        return response_time
    except Exception as e:
        print(f"请求发生错误: {e}")
        return None

def main():
    total_requests = 30
    response_times = []
    
    for i in range(total_requests):
        print(f"正在发送第 {i+1} 个请求...")
        rt = send_request()
        if rt is not None:
            response_times.append(rt)
            print(f"第 {i+1} 个请求完成，响应时间: {rt:.3f} 秒")
        else:
            print(f"第 {i+1} 个请求失败")
        
        # 单路串行，不需要延迟，但如果需要可以添加
        # time.sleep(1)
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        print("\n统计结果:")
        print(f"总请求数: {total_requests}")
        print(f"成功请求数: {len(response_times)}")
        print(f"失败请求数: {total_requests - len(response_times)}")
        print(f"平均响应时间: {avg_response_time:.3f} 秒")
        print(f"最大响应时间: {max(response_times):.3f} 秒")
        print(f"最小响应时间: {min(response_times):.3f} 秒")
    else:
        print("所有请求都失败了，无法计算统计信息")

if __name__ == "__main__":
    main()