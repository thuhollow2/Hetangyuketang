import asyncio
import websockets
import json
import requests
import os
import time
import traceback
from util import *
from send import *
from random import *

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

class yuketang:
    def __init__(self) -> None:
        self.cookie_filename="cookie"
        self.cookie=""
        self.lessonIdNewList=[]
        self.lessonIdDict = {}
        self.start_time=time.time()
        self.debug=True
        self.wx=False # 设置为True时启用企业微信推送，须在send.py设置个人CompanyId、AgentId、Secret
        self.an=False # 设置为True时自动答题
        self.si=False # 设置为True时实时推送PPT进度
        self.msgmgr=MsgManager(debug=self.debug,wx=self.wx)

    async def getcookie(self):
        while True:
            if not os.path.exists(self.cookie_filename):
                self.msgmgr.sendMsg("正在第一次获取登录cookie，请注意扫码")
                await self.ws_controller(self.ws_login, retries=1000, delay=0)
            with open(self.cookie_filename, "r") as f:
                lines = f.readlines()
            self.cookie = lines[0].strip()
            if not self.check_cookie():
                self.msgmgr.sendMsg("cookie已失效，请重新扫码")
                await self.ws_controller(self.ws_login, retries=1000, delay=0)
            else:
                if len(lines) >= 2:
                    self.msgmgr.sendMsg(f"cookie有效，有效期至{lines[1].strip()}")
                else:
                    self.msgmgr.sendMsg("cookie有效，有效期未知")
                break

    def weblogin(self,UserID,Auth):
        url="https://pro.yuketang.cn/pc/web_login"
        data={
            "UserID":UserID,
            "Auth":Auth
        }
        headers={
            "referer":"https://pro.yuketang.cn/web?next=/v2/web/index&type=3",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Content-Type":"application/json"
        }
        try:
            res=requests.post(url=url,headers=headers,json=data,timeout=15)
        except Exception as e:
            print(f"登录失败: {e}")
            return
        cookies = res.cookies
        self.cookie=""
        for k,v in cookies.items():
            self.cookie += f'{k}={v};'
        date = cookie_date(res)
        if date:
            content = f'{self.cookie}\n{date}'
        else:
            content = self.cookie
        with open(self.cookie_filename,"w")as f:
            f.write(content)

    def check_cookie(self):
        info=self.get_basicinfo()
        if info.get("code")==0:
            return True
        return False
    
    def setAuthorization(self,res,lessonId):
        if res.headers.get("Set-Auth") is not None:
            self.lessonIdDict[lessonId]['Authorization']="Bearer "+res.headers.get("Set-Auth")

    def get_basicinfo(self):
        url="https://pro.yuketang.cn/api/v3/user/basic-info"
        headers={
            "referer":"https://pro.yuketang.cn/web?next=/v2/web/index&type=3",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie":self.cookie
        }
        try:
            res=requests.get(url=url,headers=headers,timeout=15).json()
            return res
        except Exception as e:
            return {}

    def lesson_info(self,lessonId):
        url="https://pro.yuketang.cn/api/v3/lesson/basic-info"
        headers={
            "referer":f"https://pro.yuketang.cn/lesson/fullscreen/v3/{lessonId}?source=5",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie":self.cookie,
            "Authorization":self.lessonIdDict[lessonId]['Authorization']
        }
        try:
            res=requests.get(url=url,headers=headers,timeout=15)
        except Exception as e:
            return
        self.setAuthorization(res,lessonId)
        classroomName = self.lessonIdDict[lessonId]['classroomName']
        try:
            self.lessonIdDict[lessonId]['title'] = res.json()['data']['title']
            self.lessonIdDict[lessonId]['header'] = f"课程：{classroomName}\n标题：{self.lessonIdDict[lessonId]['title']}\n教师：{res.json()['data']['teacher']['name']}\n开始时间：{convert_date(res.json()['data']['startTime'])}"
        except Exception as e:
            self.lessonIdDict[lessonId]['title'] = '未知标题'
            self.lessonIdDict[lessonId]['header'] = f"课程：{classroomName}\n标题：获取失败\n教师：获取失败\n开始时间：获取失败"

    def getlesson(self):
        url="https://pro.yuketang.cn/api/v3/classroom/on-lesson-upcoming-exam"
        headers={
            "referer":"https://pro.yuketang.cn/web?next=/v2/web/index&type=3",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie":self.cookie
        }
        try:
            online_data=requests.get(url=url,headers=headers,timeout=15).json()
        except Exception as e:
            return False
        try:
            self.lessonIdNewList = []
            for item in online_data['data']['onLessonClassrooms']:
                lessonId = item['lessonId']
                if lessonId not in self.lessonIdDict:
                    self.lessonIdDict[lessonId] = {}
                    self.lessonIdNewList.append(lessonId)
                self.lessonIdDict[lessonId]['classroomName'] = item['classroomName']
                self.lessonIdDict[lessonId]['active'] = '1'
            to_delete = [lessonId for lessonId, details in self.lessonIdDict.items() if not details.get('active', '0') == '1']
            for lessonId in to_delete:
                del self.lessonIdDict[lessonId]
            for lessonId in self.lessonIdDict:
                self.lessonIdDict[lessonId]['active'] = '0'
            if self.lessonIdNewList:
                return True
            else:
                return False
        except Exception as e:
            return False

    def lesson_checkin(self):
        for lessonId in self.lessonIdNewList:
            url="https://pro.yuketang.cn/api/v3/lesson/checkin"
            headers={
                "referer":f"https://pro.yuketang.cn/lesson/fullscreen/v3/{lessonId}?source=5",
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Content-Type":"application/json; charset=utf-8",
                "cookie":self.cookie
            }
            data={
                "source":5,
                "lessonId":lessonId
            }
            try:
                res=requests.post(url=url,headers=headers,json=data,timeout=15)
            except Exception as e:
                return
            self.setAuthorization(res,lessonId)
            self.lesson_info(lessonId)
            try:
                self.lessonIdDict[lessonId]['Auth'] = res.json()['data']['lessonToken']
                self.lessonIdDict[lessonId]['userid'] = res.json()['data']['identityId']
            except Exception as e:
                self.lessonIdDict[lessonId]['Auth'] = ''
                self.lessonIdDict[lessonId]['userid'] = ''
            checkin_status = res.json()['msg']
            if checkin_status == 'OK':
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：签到成功")
            elif checkin_status == 'LESSON_END':
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：课程已结束")
            else:
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：签到失败")
    
    async def fetch_presentation(self, lessonId):
        url = f"https://pro.yuketang.cn/api/v3/lesson/presentation/fetch?presentation_id={self.lessonIdDict[lessonId]['presentation']}"
        headers = {
            "referer": f"https://pro.yuketang.cn/lesson/fullscreen/v3/{lessonId}?source=5",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie": self.cookie,
            "Authorization": self.lessonIdDict[lessonId]['Authorization']
        }
        res=requests.get(url, headers=headers, timeout=15)
        self.setAuthorization(res, lessonId)
        info = res.json()
        slides=info['data']['slides']    #获得幻灯片列表
        self.lessonIdDict[lessonId]['problems']={}
        for slide in slides:
            if slide.get("problem") is not None:
                self.lessonIdDict[lessonId]['problems'][slide['id']]=slide['problem']
                self.lessonIdDict[lessonId]['problems'][slide['id']]['index']=slide['index']
                if self.lessonIdDict[lessonId]['problems'][slide['id']]['answers'] in [[],None,'null'] and self.lessonIdDict[lessonId]['problems'][slide['id']]['result'] not in [[],None,'null']:
                    self.lessonIdDict[lessonId]['problems'][slide['id']]['answers']=self.lessonIdDict[lessonId]['problems'][slide['id']]['result']
                if slide['problem']['body'] == '':
                    shapes = slide.get('shapes', [])
                    if shapes:
                        min_left_item = min(shapes, key=lambda item: item.get('Left', 9999999))
                        if min_left_item != 9999999 and min_left_item.get('Text') is not None:
                            self.lessonIdDict[lessonId]['problems'][slide['id']]['body'] = min_left_item['Text']
                        else:
                            self.lessonIdDict[lessonId]['problems'][slide['id']]['body'] = '未知问题'
                    else:
                        self.lessonIdDict[lessonId]['problems'][slide['id']]['body'] = '未知问题'
        if self.lessonIdDict[lessonId]['problems']=={}:
            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n问题列表：无")
        else:
            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n{format_json_to_text(self.lessonIdDict[lessonId]['problems'], self.lessonIdDict[lessonId].get('unlockedproblem', []))}")
        folder_path=lessonId
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, clear_folder, folder_path)
        await loop.run_in_executor(None, download_images_to_folder, slides, folder_path)
        output_pdf_path=os.path.join(folder_path, f"{self.lessonIdDict[lessonId]['classroomName']}-{self.lessonIdDict[lessonId]['title']}.pdf")
        await loop.run_in_executor(None, images_to_pdf, folder_path, output_pdf_path)
        if os.path.exists(output_pdf_path):
            self.lessonIdDict[lessonId]['noPPT']='0'
            if self.wx:
                send_file(upload_file(output_pdf_path))
        else:
            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：没有PPT")
            self.lessonIdDict[lessonId]['noPPT']='1'

    def answer(self,lessonId):
        url="https://pro.yuketang.cn/api/v3/lesson/problem/answer"
        headers={
            "referer":f"https://pro.yuketang.cn/lesson/fullscreen/v3/{lessonId}?source=5",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie":self.cookie,
            "Content-Type":"application/json",
            "Authorization":self.lessonIdDict[lessonId]['Authorization']
        }
        if self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['answers'] in [[],None,'null']:
            self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['answers'].append(self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options'][0]['key'])
        data={
            "dt":int(time.time()*1000),
            "problemId":self.lessonIdDict[lessonId]['problemId'],
            "problemType":self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['problemType'],
            "result":self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['answers']
        }
        try:
            res=requests.post(url=url,headers=headers,json=data,timeout=15)
        except Exception as e:
            return
        self.setAuthorization(res,lessonId)
        self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\nPPT: 第{self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['index']}页\n问题：{self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['body']}\n提交答案：{self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['answers']}")

    async def ws_controller(self, func, *args, retries=3, delay=10):
        attempt = 0
        while attempt < retries:
            try:
                await func(*args)
                return  # 如果成功就直接返回
            except Exception as e:
                print(traceback.format_exc())
                attempt += 1
                print(f"出现异常，尝试重试 ({attempt}/{retries})")
                if attempt < retries:
                    await asyncio.sleep(delay)

    async def ws_login(self):
        uri = "wss://pro.yuketang.cn/wsapp/"
        async with websockets.connect(uri, ping_timeout=100, ping_interval=5) as websocket:
            # 发送 "hello" 消息以建立连接
            hello_message = {
                "op":"requestlogin",
                "role":"web",
                "version":1.4,
                "type":"qrcode",
                "from":"web"
            }
            await websocket.send(json.dumps(hello_message))
            server_response = await recv_json(websocket)
            qrcode_url=server_response['ticket']
            download_qrcode(qrcode_url)
            if self.wx:
                send_image(upload_file("qrcode.jpg"))
            server_response = await asyncio.wait_for(recv_json(websocket),timeout=120)
            self.weblogin(server_response['UserID'],server_response['Auth'])
        await websocket.close()

    async def ws_lesson(self,lessonId):
        flag_ppt=1
        if self.lessonIdDict[lessonId].get('noPPT') is not None:
            flag_ppt=0
        elif self.lessonIdDict[lessonId].get('noPPT') is None and self.lessonIdDict[lessonId].get('presentation') is not None:
            del self.lessonIdDict[lessonId]['presentation']
        flag_si=1
        if self.lessonIdDict[lessonId].get('si') is not None:
            del self.lessonIdDict[lessonId]['si']
        flag_unlock=1
        if self.lessonIdDict[lessonId].get('unlockedproblem') is not None:
            del self.lessonIdDict[lessonId]['unlockedproblem']
        uri = "wss://pro.yuketang.cn/wsapp/"
        async with websockets.connect(uri, ping_timeout=60, ping_interval=5) as websocket:
            # 发送 "hello" 消息以建立连接
            hello_message = {
                "op": "hello",
                "userid": self.lessonIdDict[lessonId]['userid'],
                "role": "student",
                "auth": self.lessonIdDict[lessonId]['Auth'],
                "lessonid": lessonId
            }
            await websocket.send(json.dumps(hello_message))
            while True and time.time()-self.start_time<36000:
                try:
                    server_response = await recv_json(websocket)
                except Exception as e:
                    self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：连接断开")
                    break
                op=server_response['op']
                if op=="hello" or op=="fetchtimeline":
                    reversed_timeline = list(reversed(server_response['timeline']))
                    for item in reversed_timeline:
                        if 'pres' in item:
                            if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != item['pres']:
                                flag_ppt=1
                                flag_si=1
                                flag_unlock=1
                                del self.lessonIdDict[lessonId]['si']
                                del self.lessonIdDict[lessonId]['unlockedproblem']
                                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：课件更新")
                            self.lessonIdDict[lessonId]['presentation']=item['pres']
                            self.lessonIdDict[lessonId]['si']=item['si']
                            break
                    if server_response.get('presentation'):
                        if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != server_response['presentation']:
                            flag_ppt=1
                            flag_si=1
                            flag_unlock=1
                            del self.lessonIdDict[lessonId]['si']
                            del self.lessonIdDict[lessonId]['unlockedproblem']
                            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：课件更新")
                        self.lessonIdDict[lessonId]['presentation']=server_response['presentation']
                    if server_response.get('slideindex'):
                        self.lessonIdDict[lessonId]['si']=server_response['slideindex']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem']=server_response['unlockedproblem']
                elif op=="showpresentation" or op=="presentationupdated" or op=="presentationcreated":
                    if server_response.get('presentation'):
                        if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != server_response['presentation']:
                            flag_ppt=1
                            flag_si=1
                            flag_unlock=1
                            del self.lessonIdDict[lessonId]['si']
                            del self.lessonIdDict[lessonId]['unlockedproblem']
                            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：课件更新")
                        self.lessonIdDict[lessonId]['presentation']=server_response['presentation']
                    if server_response.get('slideindex'):
                        self.lessonIdDict[lessonId]['si']=server_response['slideindex']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem']=server_response['unlockedproblem']
                elif op=="slidenav":
                    if server_response['slide'].get('pres'):
                        if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != server_response['slide']['pres']:
                            flag_ppt=1
                            flag_si=1
                            flag_unlock=1
                            del self.lessonIdDict[lessonId]['si']
                            del self.lessonIdDict[lessonId]['unlockedproblem']
                            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：课件更新")
                        self.lessonIdDict[lessonId]['presentation']=server_response['slide']['pres']
                    if server_response['slide'].get('si'):
                        self.lessonIdDict[lessonId]['si']=server_response['slide']['si']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem']=server_response['unlockedproblem']
                elif op=="unlockproblem":
                    if server_response['problem'].get('pres'):
                        if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != server_response['problem']['pres']:
                            flag_ppt=1
                            flag_si=1
                            flag_unlock=1
                            del self.lessonIdDict[lessonId]['si']
                            del self.lessonIdDict[lessonId]['unlockedproblem']
                            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：课件更新")
                        self.lessonIdDict[lessonId]['presentation']=server_response['problem']['pres']
                    if server_response['problem'].get('si'):
                        self.lessonIdDict[lessonId]['si']=server_response['problem']['si']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem']=server_response['unlockedproblem']
                    self.lessonIdDict[lessonId]['problemId']=server_response['problem']['prob']
                    if self.an:
                        await asyncio.sleep(randint(5,10))
                        self.answer(lessonId)
                elif op=="lessonfinished":
                    self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：下课了")
                    break
                if flag_unlock==1 and self.lessonIdDict[lessonId].get('unlockedproblem') is not None:
                    flag_unlock=0
                if flag_ppt==1 and self.lessonIdDict[lessonId].get('presentation') is not None:
                    flag_ppt=0
                    await self.fetch_presentation(lessonId)
                if flag_si==1 and self.lessonIdDict[lessonId].get('noPPT') is not None and self.lessonIdDict[lessonId].get('si') is not None:
                    if self.lessonIdDict[lessonId]['noPPT'] == '0':
                        self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息：正在播放PPT第{self.lessonIdDict[lessonId]['si']}页")
                    if self.si:
                        del self.lessonIdDict[lessonId]['si']
                    else:
                        flag_si=0
        await websocket.close()
        del self.lessonIdDict[lessonId]

    async def lesson_attend(self):
        tasks = [asyncio.create_task(self.ws_lesson(lessonId)) for lessonId in self.lessonIdNewList]
        asyncio.gather(*tasks)
        self.lessonIdNewList = []

async def ykt_user():
    ykt = yuketang()
    await ykt.getcookie()
    while True:
        if ykt.getlesson():
            ykt.lesson_checkin()
            await ykt.lesson_attend()
        await asyncio.sleep(30)
