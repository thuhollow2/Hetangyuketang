import json
import requests
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

global ACCESS_TOKEN

Touser = '@all'
AgentId = 'xxxx'
Secret = 'xxxx'
CompanyId = 'xxxx'

def get_token():
    global ACCESS_TOKEN
    # 通行密钥
    ACCESS_TOKEN = None
    # 如果本地保存的有通行密钥且时间不超过两小时，就用本地的通行密钥
    if os.path.exists('ACCESS_TOKEN.txt'):
        txt_last_edit_time = os.stat('ACCESS_TOKEN.txt').st_mtime
        now_time = time.time()
        if now_time - txt_last_edit_time < 7000:  # 官方说通行密钥2小时刷新
            with open('ACCESS_TOKEN.txt', 'r') as f:
                ACCESS_TOKEN = f.read()
                # print(ACCESS_TOKEN)
    # 如果不存在本地通行密钥，通过企业ID和应用Secret获取
    if not ACCESS_TOKEN:
        try:
            r = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CompanyId}&corpsecret={Secret}', timeout=15).json()
        except Exception as e:
            print(f"获取通行密钥时发生错误: {e}")
            return
        ACCESS_TOKEN = r["access_token"]
        # print(ACCESS_TOKEN)
        # 保存通行密钥到本地ACCESS_TOKEN.txt
        with open('ACCESS_TOKEN.txt', 'w', encoding='utf-8') as f:
            f.write(ACCESS_TOKEN)

class MsgManager:
    def __init__(self,debug=False,wx=True) -> None:
        self.debug=debug
        self.wx=wx

    def sendMsg(self,msg="this is a test msg"):
        get_token()
        if self.debug:
            print(f"发送给{Touser}的消息: {msg}")
        if self.wx:
            send2wechat(msg)


def upload_file(filepath):
    get_token()
    TYPE="file"
    files={
        'file':open(filepath,'rb')
    }
    try:
        r=requests.post(f'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={ACCESS_TOKEN}&type={TYPE}', files=files, timeout=15)
    except Exception as e:
        print(f"上传文件时发生错误: {e}")
        return
    return r.json()['media_id']

def send_file(id):
    get_token()
    data = {
        "touser": f"{Touser}",
        "msgtype": "file",
        "agentid": f"{AgentId}",
        "file":  {'media_id':id}
    }
    # 字典转成json，不然会报错
    data = json.dumps(data)
    # 发送消息
    try:
        r = requests.post(
            f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={ACCESS_TOKEN}', data=data, timeout=15)
    except Exception as e:
        print(f"发送文件时发生错误: {e}")
        return

def send2wechat(message):
    # 要发送的信息格式
    get_token()
    data = {
        "touser": f"{Touser}",
        "msgtype": "text",
        "agentid": f"{AgentId}",
        "text": {"content": f"{message}"}
    }
    # 字典转成json，不然会报错
    data = json.dumps(data)
    # 发送消息
    try:
        r = requests.post(
            f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={ACCESS_TOKEN}', data=data, timeout=15)
    except Exception as e:
        print(f"发送消息时发生错误: {e}")
        return

def send_image(id):
    # 要发送的信息格式
    get_token()
    data = {
        "touser": f"{Touser}",
        "msgtype": "image",
        "agentid": f"{AgentId}",
        "image":  {'media_id':id}
    }
    # 字典转成json，不然会报错
    data = json.dumps(data)
    # 发送消息
    try:
        r = requests.post(
            f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={ACCESS_TOKEN}', data=data, timeout=15)
    except Exception as e:
        print(f"发送图片时发生错误: {e}")
        return
    #print(r.json())

def get_useridlist():
    get_token()
    print(ACCESS_TOKEN)
    url="https://qyapi.weixin.qq.com/cgi-bin/user/list_id?access_token={ACCESS_TOKEN}"
    try:
        r=requests.post(url, timeout=15)
    except Exception as e:
        print(f"获取用户列表时发生错误: {e}")
        return
    print(r.json())

