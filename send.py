import json
import requests
import os
import time
import io
from PyPDF2 import PdfReader, PdfWriter

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

global WX_ACCESS_TOKEN
global DD_ACCESS_TOKEN

wx_touser = '@all' # 发送给所有人
wx_agentId = 'XXXX'
wx_secret = 'XXXX'
wx_companyId = 'XXXX'

dd_appKey = 'XXXX'
dd_appSecret = 'XXXX'
dd_robotCode = 'XXXX'
dd_openConversationId = 'XXXX'

def get_wx_token():
    global WX_ACCESS_TOKEN
    WX_ACCESS_TOKEN = None
    if os.path.exists('WX_ACCESS_TOKEN.txt'):
        txt_last_edit_time = os.stat('WX_ACCESS_TOKEN.txt').st_mtime
        now_time = time.time()
        if now_time - txt_last_edit_time < 7000:  # 2小时刷新
            with open('WX_ACCESS_TOKEN.txt', 'r') as f:
                WX_ACCESS_TOKEN = f.read()
    if not WX_ACCESS_TOKEN:
        try:
            r = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wx_companyId}&corpsecret={wx_secret}', timeout=15).json()
        except Exception as e:
            print(f"获取通行密钥时发生错误: {e}")
            return
        WX_ACCESS_TOKEN = r["access_token"]
        with open('WX_ACCESS_TOKEN.txt', 'w', encoding='utf-8') as f:
            f.write(WX_ACCESS_TOKEN)

def get_dd_token():
    global DD_ACCESS_TOKEN
    DD_ACCESS_TOKEN = None
    if os.path.exists('DD_ACCESS_TOKEN.txt'):
        txt_last_edit_time = os.stat('DD_ACCESS_TOKEN.txt').st_mtime
        now_time = time.time()
        if now_time - txt_last_edit_time < 7000:  # 2小时刷新
            with open('DD_ACCESS_TOKEN.txt', 'r') as f:
                DD_ACCESS_TOKEN = f.read()
    if not DD_ACCESS_TOKEN:
        try:
            r = requests.post(
                f'https://api.dingtalk.com/v1.0/oauth2/accessToken', json={'appKey': dd_appKey, 'appSecret': dd_appSecret}, timeout=15).json()
        except Exception as e:
            print(f"获取通行密钥时发生错误: {e}")
            return
        DD_ACCESS_TOKEN = r["accessToken"]
        with open('DD_ACCESS_TOKEN.txt', 'w', encoding='utf-8') as f:
            f.write(DD_ACCESS_TOKEN)

class SendManager:
    def __init__(self,wx=False,dd=False) -> None:
        self.wx=wx
        self.dd=dd

    def sendMsg(self,msg):
        print(msg)
        if self.wx:
            get_wx_token()
            send_wx_msg(msg_part(msg, 500))
        if self.dd:
            get_dd_token()
            send_dd_msg(msg_part(msg, 3000))
    
    def sendImage(self,path):
        if self.wx:
            get_wx_token()
            send_wx_image(upload_wx_file(path))
        if self.dd:
            get_dd_token()
            send_dd_image(upload_dd_file(path))

    def sendFile(self,path):
        if self.wx:
            get_wx_token()
            send_wx_file(upload_wx_file(path))
        if self.dd:
            get_dd_token()
            send_dd_file(upload_dd_file(path))

def get_pdf_size(pdf_writer):
    temp_io = io.BytesIO()
    pdf_writer.write(temp_io)
    return temp_io.getbuffer().nbytes

def split_pdf(filepath, max_size):
    if os.path.getsize(filepath) < max_size:
        return [filepath]
    pdf = PdfReader(filepath)
    pdf_writer = PdfWriter()
    filepaths = []
    output_filename = f'{filepath[:-4]}_'
    start_page = 0
    for page in range(len(pdf.pages)):
        pdf_writer.add_page(pdf.pages[page])
        if get_pdf_size(pdf_writer) >= max_size:
            if start_page != page:
                if start_page == page - 1:
                    temp_filename = f'{output_filename}{start_page + 1}.pdf'
                    temp_pdf_writer=PdfWriter()
                    temp_pdf_writer.add_page(pdf.pages[start_page])
                else:
                    temp_filename = f'{output_filename}{start_page + 1}-{page}.pdf'
                    temp_pdf_writer = PdfWriter()
                    for i in range(start_page, page):
                        temp_pdf_writer.add_page(pdf.pages[i])
                with open(temp_filename, 'wb') as out:
                    temp_pdf_writer.write(out)
                filepaths.append(temp_filename)
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf.pages[page])
                start_page = page
                if get_pdf_size(pdf_writer) >= max_size:
                    pdf_writer = PdfWriter()
                    start_page = page + 1
            else:
                pdf_writer = PdfWriter()
                start_page = page + 1
    if start_page != len(pdf.pages):
        if start_page == len(pdf.pages) - 1:
            temp_filename = f'{output_filename}{start_page + 1}.pdf'
            temp_pdf_writer = PdfWriter()
            temp_pdf_writer.add_page(pdf.pages[start_page])
        else:
            temp_filename = f'{output_filename}{start_page + 1}-{len(pdf.pages)}.pdf'
            temp_pdf_writer = PdfWriter()
            for i in range(start_page, len(pdf.pages)):
                temp_pdf_writer.add_page(pdf.pages[i])
        with open(temp_filename, 'wb') as out:
            temp_pdf_writer.write(out)
        filepaths.append(temp_filename)
    return filepaths

def msg_part(message, max_length):
    lines = message.split('\n')
    parts = []
    part = lines[0]
    part_length = len(part)
    for line in lines[1:]:
        new_length = part_length + 1 + len(line)
        if new_length <= max_length:
            part += '\n' + line
            part_length = new_length
        else:
            parts.append(part)
            part = line
            part_length = len(line)
    parts.append(part)
    return parts

def upload_wx_file(filepath):
    _, ext = os.path.splitext(filepath)
    if ext.lower() == '.pdf':
        filepaths = split_pdf(filepath, 20971520) # 20MB
    else:
        filepaths = [filepath]
    media_ids = []
    for path in filepaths:
        files={
            'file': open(path, 'rb')
        }
        try:
            r=requests.post(f'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={WX_ACCESS_TOKEN}&type=file', files=files, timeout=15)
        except Exception as e:
            print(f"上传文件时发生错误: {e}")
            return
        media_ids.append(r.json()['media_id'])
    return media_ids

def send_wx_msg(parts):
    for part in parts:
        data = {
            "touser": wx_touser,
            "msgtype": "text",
            "agentid": wx_agentId,
            "text": {"content": f"{part}"}
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={WX_ACCESS_TOKEN}', data=data, timeout=15)
        except Exception as e:
            print(f"发送消息时发生错误: {e}")
            return
        time.sleep(1)

def send_wx_image(media_ids):
    for id in media_ids:
        data = {
            "touser": wx_touser,
            "msgtype": "image",
            "agentid": wx_agentId,
            "image":  {'media_id':id}
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={WX_ACCESS_TOKEN}', data=data, timeout=15)
        except Exception as e:
            print(f"发送图片时发生错误: {e}")
            return
        time.sleep(1)

def send_wx_file(media_ids):
    for id in media_ids:
        data = {
            "touser": wx_touser,
            "msgtype": "file",
            "agentid": wx_agentId,
            "file":  {'media_id':id}
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={WX_ACCESS_TOKEN}', data=data, timeout=15)
        except Exception as e:
            print(f"发送文件时发生错误: {e}")
            return
        time.sleep(1)

def upload_dd_file(filepath):
    _, ext = os.path.splitext(filepath)
    if ext.lower() == '.pdf':
        filepaths = split_pdf(filepath, 20971520) # 20MB
    else:
        filepaths = [filepath]
    media_ids = {}
    for path in filepaths:
        files={
            'media': open(path, 'rb')
        }
        try:
            r=requests.post(f'https://oapi.dingtalk.com/media/upload?access_token={DD_ACCESS_TOKEN}&type=file', files=files, timeout=15)
        except Exception as e:
            print(f"上传文件时发生错误: {e}")
            return
        media_ids[r.json()['media_id']] = os.path.basename(path)
    return media_ids

def send_dd_msg(parts):
    for part in parts:
        headers = {
            'x-acs-dingtalk-access-token': DD_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        data = {
            "msgParam" : f'{{"content":"{part}"}}',
            "msgKey" : "sampleText",
            "robotCode" : dd_robotCode,
            "openConversationId" : dd_openConversationId
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://api.dingtalk.com/v1.0/robot/groupMessages/send', headers=headers, data=data, timeout=15)
        except Exception as e:
            print(f"发送消息时发生错误: {e}")
            return
        time.sleep(1)

def send_dd_image(media_ids):
    for id in media_ids:
        headers = {
            'x-acs-dingtalk-access-token': DD_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        data = {
            "msgParam" : f'{{"photoURL":"{id}"}}',
            "msgKey" : "sampleImageMsg",
            "robotCode" : dd_robotCode,
            "openConversationId" : dd_openConversationId
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://api.dingtalk.com/v1.0/robot/groupMessages/send', headers=headers, data=data, timeout=15)
        except Exception as e:
            print(f"发送图片时发生错误: {e}")
            return
        time.sleep(1)

def send_dd_file(media_ids):
    for id in media_ids:
        _, ext = os.path.splitext(media_ids[id])
        fileType = ext[1:]
        headers = {
            'x-acs-dingtalk-access-token': DD_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        data = {
            "msgParam" : f'{{"mediaId":"{id}", "fileName":"{media_ids[id]}", "fileType":"{fileType}"}}',
            "msgKey" : "sampleFile",
            "robotCode" : dd_robotCode,
            "openConversationId" : dd_openConversationId
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://api.dingtalk.com/v1.0/robot/groupMessages/send', headers=headers, data=data, timeout=15)
        except Exception as e:
            print(f"发送文件时发生错误: {e}")
            return
        time.sleep(1)
