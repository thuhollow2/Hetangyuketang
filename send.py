import json
import requests
import os
import time
import io
from PyPDF2 import PdfReader, PdfWriter
from concurrent.futures import ThreadPoolExecutor, as_completed

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

timeout = config['send']['timeout']
threads = config['send']['threads']
services = config['send']['services']

class SendManager:
    def _send_wx_msg(self, msg, service):
        access_token = get_wx_token(service)
        if access_token:
            send_wx_msg(msg_part(msg, service['msgLimit']), service, access_token)

    def _send_dd_msg(self, msg, service):
        access_token = get_dd_token(service)
        if access_token:
            send_dd_msg(msg_part(msg, service['msgLimit']), service, access_token)

    def _send_fs_msg(self, msg, service):
        access_token = get_fs_token(service)
        if access_token:
            send_fs_msg(msg_part(msg, service['msgLimit']), service, access_token)

    def _send_wx_image(self, path, service):
        access_token = get_wx_token(service)
        if access_token:
            send_wx_image(upload_wx_file(path, access_token), service, access_token)

    def _send_dd_image(self, path, service):
        access_token = get_dd_token(service)
        if access_token:
            send_dd_image(upload_dd_file(path, access_token), service, access_token)

    def _send_fs_image(self, path, service):
        access_token = get_fs_token(service)
        if access_token:
            send_fs_image(upload_fs_image(path, access_token), service, access_token)

    def _send_wx_file(self, path, service):
        access_token = get_wx_token(service)
        if access_token:
            send_wx_file(upload_wx_file(path, access_token, service['dataLimit']), service, access_token)

    def _send_dd_file(self, path, service):
        access_token = get_dd_token(service)
        if access_token:
            send_dd_file(upload_dd_file(path, access_token, service['dataLimit']), service, access_token)

    def _send_fs_file(self, path, service):
        access_token = get_fs_token(service)
        if access_token:
            send_fs_file(upload_fs_file(path, access_token, service['dataLimit']), service, access_token)

    def sendMsg(self, msg):
        print(msg)
        tasks = []
        with ThreadPoolExecutor(max_workers=threads) as pool:
            for s in [s for s in services if s['enabled']]:
                tp = s['type']
                if tp == 'wechat':
                    tasks.append(pool.submit(self._send_wx_msg, msg, s))
                elif tp == 'dingtalk':
                    tasks.append(pool.submit(self._send_dd_msg, msg, s))
                elif tp == 'feishu':
                    tasks.append(pool.submit(self._send_fs_msg, msg, s))
                else:
                    continue

            for future in as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    print(f"发送失败: {e}")

    def sendImage(self, path):
        tasks = []
        with ThreadPoolExecutor(max_workers=threads) as pool:
            for s in [s for s in services if s['enabled']]:
                tp = s['type']
                if tp == 'wechat':
                    tasks.append(pool.submit(self._send_wx_image, path, s))
                elif tp == 'dingtalk':
                    tasks.append(pool.submit(self._send_dd_image, path, s))
                elif tp == 'feishu':
                    tasks.append(pool.submit(self._send_fs_image, path, s))
                else:
                    continue

            for future in as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    print(f"发送失败: {e}")

    def sendFile(self, path):
        tasks = []
        with ThreadPoolExecutor(max_workers=threads) as pool:
            for s in [s for s in services if s['enabled']]:
                tp = s['type']
                if tp == 'wechat':
                    tasks.append(pool.submit(self._send_wx_file, path, s))
                elif tp == 'dingtalk':
                    tasks.append(pool.submit(self._send_dd_file, path, s))
                elif tp == 'feishu':
                    tasks.append(pool.submit(self._send_fs_file, path, s))
                else:
                    continue

            for future in as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    print(f"发送失败: {e}")

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
    lines = [line for line in str(message).split('\n') if line.strip() != '']
    parts = []
    part = ''
    for line in lines:
        if len(line) < max_length:
            if part:
                new_length = len(part) + 1 + len(line)
            else:
                new_length = len(line)
            if new_length <= max_length:
                if part:
                    part += '\n' + line
                else:
                    part = line
            else:
                parts.append(part)
                part = line
        else:
            if part:
                parts.append(part)
                part = ''
            for i in range(0, len(line), max_length):
                parts.append(line[i:i+max_length])
    parts.append(part)
    return parts

def get_wx_token(service):
    access_token = None
    if os.path.exists(f'access_token_wx_{service["name"]}.txt'):
        txt_last_edit_time = os.stat(f'access_token_wx_{service["name"]}.txt').st_mtime
        now_time = time.time()
        if now_time - txt_last_edit_time < 7000:
            with open(f'access_token_wx_{service["name"]}.txt', 'r') as f:
                access_token = f.read()
    if not access_token:
        try:
            r = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={service["companyId"]}&corpsecret={service["secret"]}', timeout=timeout)
            access_token = r.json()["access_token"]
            with open(f'access_token_wx_{service["name"]}.txt', 'w', encoding='utf-8') as f:
                f.write(access_token)
        except Exception as e:
            print(f"企业微信获取通行密钥时发生错误: {e}")
    return access_token

def get_dd_token(service):
    access_token = None
    if os.path.exists(f'access_token_dd_{service["name"]}.txt'):
        txt_last_edit_time = os.stat(f'access_token_dd_{service["name"]}.txt').st_mtime
        now_time = time.time()
        if now_time - txt_last_edit_time < 7000:
            with open(f'access_token_dd_{service["name"]}.txt', 'r') as f:
                access_token = f.read()
    if not access_token:
        try:
            r = requests.post(
                f'https://api.dingtalk.com/v1.0/oauth2/accessToken', json={"appKey": service["appKey"], "appSecret": service["appSecret"]}, timeout=timeout)
            access_token = r.json()["accessToken"]
            with open(f'access_token_dd_{service["name"]}.txt', 'w', encoding='utf-8') as f:
                f.write(access_token)
        except Exception as e:
            print(f"钉钉获取通行密钥时发生错误: {e}")
    return access_token

def get_fs_token(service):
    access_token = None
    if os.path.exists(f'access_token_fs_{service["name"]}.txt'):
        txt_last_edit_time = os.stat(f'access_token_fs_{service["name"]}.txt').st_mtime
        now_time = time.time()
        if now_time - txt_last_edit_time < 1740:
            with open(f'access_token_fs_{service["name"]}.txt', 'r') as f:
                access_token = f.read()
    if not access_token:
        try:
            r = requests.post(
                f'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', json={"app_id": service["appId"], "app_secret": service["appSecret"]}, timeout=timeout)
            access_token = r.json()["tenant_access_token"]
            with open(f'access_token_fs_{service["name"]}.txt', 'w', encoding='utf-8') as f:
                f.write(access_token)
        except Exception as e:
            print(f"飞书获取通行密钥时发生错误: {e}")
    return access_token

def upload_wx_file(filepath, access_token, max_data=20971520):
    _, ext = os.path.splitext(filepath)
    if ext.lower() == '.pdf':
        filepaths = split_pdf(filepath, max_data)
    else:
        filepaths = [filepath]
    media_ids = []
    for path in filepaths:
        files={
            'file': open(path, 'rb')
        }
        try:
            r=requests.post(f'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=file', files=files, timeout=timeout)
            if r.json()['errcode'] == 60020:
                print('企业微信文件上传失败: 未配置可信IP')
                return []
        except Exception as e:
            print(f"企业微信文件上传发生错误: {e}")
            return []
        media_ids.append(r.json()['media_id'])
    return media_ids

def send_wx_msg(parts, service, access_token):
    for part in parts:
        data = {
            "touser": service['touser'],
            "msgtype": "text",
            "agentid": service['agentId'],
            "text": {"content": f"{part}"}
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}', data=data, timeout=timeout)
            if r.json()['errcode'] == 60020:
                print('企业微信消息发送失败: 未配置可信IP')
                return
        except Exception as e:
            print(f"企业微信消息发送发生错误: {e}")
            return
        time.sleep(1)

def send_wx_image(media_ids, service, access_token):
    for id in media_ids:
        data = {
            "touser": service['touser'],
            "msgtype": "image",
            "agentid": service['agentId'],
            "image":  {'media_id':id}
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}', data=data, timeout=timeout)
            if r.json()['errcode'] == 60020:
                print('企业微信图片发送失败: 未配置可信IP')
                return
        except Exception as e:
            print(f"企业微信图片发送发生错误: {e}")
            return
        time.sleep(1)

def send_wx_file(media_ids, service, access_token):
    for id in media_ids:
        data = {
            "touser": service['touser'],
            "msgtype": "file",
            "agentid": service['agentId'],
            "file":  {'media_id':id}
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}', data=data, timeout=timeout)
            if r.json()['errcode'] == 60020:
                print('企业微信文件发送失败: 未配置可信IP')
                return
        except Exception as e:
            print(f"企业微信文件发送发生错误: {e}")
            return
        time.sleep(1)

def upload_dd_file(filepath, access_token, max_data=20971520):
    _, ext = os.path.splitext(filepath)
    if ext.lower() == '.pdf':
        filepaths = split_pdf(filepath, max_data)
    else:
        filepaths = [filepath]
    media_ids = {}
    for path in filepaths:
        files={
            'media': open(path, 'rb')
        }
        try:
            r=requests.post(f'https://oapi.dingtalk.com/media/upload?access_token={access_token}&type=file', files=files, timeout=timeout)
        except Exception as e:
            print(f"钉钉文件上传发生错误: {e}")
            return {}
        media_ids[r.json()['media_id']] = os.path.basename(path)
    return media_ids

def send_dd_msg(parts, service, access_token):
    for part in parts:
        headers = {
            'x-acs-dingtalk-access-token': access_token,
            'Content-Type': 'application/json'
        }
        data = {
            "msgParam" : f'{{"content":"{part}"}}',
            "msgKey" : "sampleText",
            "robotCode" : service['robotCode'],
            "openConversationId" : service['openConversationId']
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://api.dingtalk.com/v1.0/robot/groupMessages/send', headers=headers, data=data, timeout=timeout)
        except Exception as e:
            print(f"钉钉消息发送发生错误: {e}")
            return
        time.sleep(1)

def send_dd_image(media_ids, service, access_token):
    for id in media_ids:
        headers = {
            'x-acs-dingtalk-access-token': access_token,
            'Content-Type': 'application/json'
        }
        data = {
            "msgParam" : f'{{"photoURL":"{id}"}}',
            "msgKey" : "sampleImageMsg",
            "robotCode" : service['robotCode'],
            "openConversationId" : service['openConversationId']
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://api.dingtalk.com/v1.0/robot/groupMessages/send', headers=headers, data=data, timeout=timeout)
        except Exception as e:
            print(f"钉钉图片发送发生错误: {e}")
            return
        time.sleep(1)

def send_dd_file(media_ids, service, access_token):
    for id in media_ids:
        _, ext = os.path.splitext(media_ids[id])
        fileType = ext[1:]
        headers = {
            'x-acs-dingtalk-access-token': access_token,
            'Content-Type': 'application/json'
        }
        data = {
            "msgParam" : f'{{"mediaId":"{id}", "fileName":"{media_ids[id]}", "fileType":"{fileType}"}}',
            "msgKey" : "sampleFile",
            "robotCode" : service['robotCode'],
            "openConversationId" : service['openConversationId']
        }
        data = json.dumps(data)
        try:
            r = requests.post(
                f'https://api.dingtalk.com/v1.0/robot/groupMessages/send', headers=headers, data=data, timeout=timeout)
        except Exception as e:
            print(f"钉钉文件发送发生错误: {e}")
            return
        time.sleep(1)

def upload_fs_image(filepath, access_token):
    filepaths = [filepath]
    media_ids = []
    for path in filepaths:
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        data = {
            'image_type': 'message'
        }
        files = {
            'image': open(path, 'rb')
        }
        try:
            r=requests.post(f'https://open.feishu.cn/open-apis/im/v1/images', headers=headers, data=data, files=files, timeout=timeout)
        except Exception as e:
            print(f"飞书图片上传发生错误: {e}")
            return []
        media_ids.append(r.json()['data']['image_key'])
    return media_ids

def upload_fs_file(filepath, access_token, max_data):
    _, ext = os.path.splitext(filepath)
    fileType = ext[1:]
    if ext.lower() == '.pdf':
        filepaths = split_pdf(filepath, max_data)
    else:
        filepaths = [filepath]
    media_ids = []
    for path in filepaths:
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        data = {
            'file_type': fileType,
            'file_name': os.path.basename(path)
        }
        files = {
            'file': open(path, 'rb')
        }
        try:
            r=requests.post(f'https://open.feishu.cn/open-apis/im/v1/files', headers=headers, data=data, files=files, timeout=timeout)
        except Exception as e:
            print(f"飞书文件上传发生错误: {e}")
            return []
        media_ids.append(r.json()['data']['file_key'])
    return media_ids

def send_fs_msg(parts, service, access_token):
    for part in parts:
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        body = {
            "receive_id": service['openId'],
            "msg_type": "text",
            "content": json.dumps({
                "text": part
            })
        }
        params = {"receive_id_type": "open_id"}
        try:
            r=requests.post(f'https://open.feishu.cn/open-apis/im/v1/messages', params=params, headers=headers, json=body, timeout=timeout)
        except Exception as e:
            print(f"飞书消息发送发生错误: {e}")
            return
        time.sleep(1)

def send_fs_image(media_ids, service, access_token):
    for id in media_ids:
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        body = {
            "receive_id": service['openId'],
            "msg_type": "image",
            "content": json.dumps({
                "image_key": id
            })
        }
        params = {"receive_id_type": "open_id"}
        try:
            r=requests.post(f'https://open.feishu.cn/open-apis/im/v1/messages', params=params, headers=headers, json=body, timeout=timeout)
        except Exception as e:
            print(f"飞书图片发送发生错误: {e}")
            return
        time.sleep(1)

def send_fs_file(media_ids, service, access_token):
    for id in media_ids:
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        body = {
            "receive_id": service['openId'],
            "msg_type": "file",
            "content": json.dumps({
                "file_key": id
            })
        }
        params = {"receive_id_type": "open_id"}
        try:
            r=requests.post(f'https://open.feishu.cn/open-apis/im/v1/messages', params=params, headers=headers, json=body, timeout=timeout)
        except Exception as e:
            print(f"飞书文件发送发生错误: {e}")
            return
        time.sleep(1)
