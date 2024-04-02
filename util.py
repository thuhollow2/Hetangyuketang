import requests
import json
import os
import re
import shutil
from PIL import Image
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

def download_qrcode(url):
    try:
        res=requests.get(url, timeout=15)
    except Exception as e:
        print(f"下载登录二维码时发生错误: {e}")
        return
    print("登录二维码已保存为qrcode.jpg")
    with open("qrcode.jpg","wb")as f:
        f.write(res.content)

def cookie_date(response):
    set_cookie_str = response.headers.get('Set-Cookie', '')
    expires_regex = re.compile(r'expires=([^;]+)')
    expires_matches = expires_regex.findall(set_cookie_str)
    expires_datetimes = [datetime.strptime(date_str, '%a, %d-%b-%Y %H:%M:%S GMT') for date_str in expires_matches]
    nearest_expires = min(expires_datetimes, default=None)
    if nearest_expires:
        nearest_expires_str = nearest_expires.strftime('%Y年%m月%d日%H时%M分%S秒')
    else:
        nearest_expires_str = None
    return nearest_expires_str

def clear_folder(folder_path):
    try:
        if os.path.isfile(folder_path) or os.path.islink(folder_path):
            os.unlink(folder_path)
        elif os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
    except Exception as e:
        print(f'删除 {folder_path} 时发生错误。原因: {e}')
    os.makedirs(folder_path)

def download_images_to_folder(slides, folder):
    for item in slides:
        if not item.get('cover'):
            continue
        try:
            response = requests.get(item['cover'], timeout=15)
        except Exception as e:
            print(f"下载图片 {item['index']} 时发生错误: {e}")
            continue
        if response.status_code == 200:
            file_path = os.path.join(folder, f"{item['index']}.jpg")
            with open(file_path, 'wb') as f:
                f.write(response.content)

def images_to_pdf(folder, output_path):
    if not os.path.exists(folder):
        print(f'文件夹 {folder} 不存在')
        return
    image_files = [f for f in os.listdir(folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print(f'文件夹 {folder} 中没有任何图片文件')
        return
    image_files.sort(key=lambda x: int(x.split('.')[0]))
    images = [Image.open(os.path.join(folder, f)).convert('RGB') for f in image_files]
    if images:
        images[0].save(output_path, save_all=True, append_images=images[1:])
        print(f'PDF文件已生成: {output_path}')
    else:
        print("没有找到任何图片文件")
    images[0].save(output_path, save_all=True, append_images=images[1:])

def convert_date(timestamp_ms):
    timestamp_s = timestamp_ms / 1000
    dt = datetime.fromtimestamp(timestamp_s)
    formatted_date = dt.strftime('%Y年%m月%d日%H时%M分%S秒')
    return formatted_date

def format_json_to_text(json_data, list_data):
    index_data = []
    text_result = "问题列表：\n"
    for index, problem_info in json_data.items():
        if index in list_data:
            index_data.append(problem_info['index'])
        text_result += "-"*20 + "\n"
        body = problem_info.get('body', '未知问题')
        answers = problem_info.get('answers', [])
        text_result += f"PPT: 第{problem_info['index']}页\n问题: {body}\n"
        for option in problem_info.get('options', []):
            text_result += f"- {option['key']}: {option['value']}\n"
        if answers:
            answer_text = ', '.join(answers)
            text_result += f"答案: {answer_text}\n"
        else:
            text_result += "答案: 暂无\n"
    text_result += "已解锁问题：\n"
    if not index_data:
        text_result += "无\n"
    else:
        for item in index_data:
            text_result += f"- PPT: 第{item}页\n"
    return text_result

async def recv_json(websocket):
    server_response = await websocket.recv()
    # print(f"Received from server: {server_response}")
    info=json.loads(server_response)
    return info
