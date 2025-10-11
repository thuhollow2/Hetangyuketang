import asyncio
import websockets
import json
import requests
import os
import time
import traceback
from util import *
from send import *
from llm import *
from random import *

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

yt_config = config['yuketang']
timeout = yt_config['timeout']
domain = yt_config['domain']

class yuketang:
    def __init__(self) -> None:
        self.cookie = ''
        self.cookie_time = ''
        self.lessonIdNewList = []
        self.lessonIdDict = {}
        self.classroomCodeList = yt_config['classroomCodeList']
        self.classroomWhiteList = yt_config['classroomWhiteList']
        self.classroomBlackList = yt_config['classroomBlackList']
        self.classroomStartTimeDict = yt_config['classroomStartTimeDict']
        self.llm = yt_config['llm']
        self.an = yt_config['an']
        self.ppt = yt_config['ppt']
        self.si = yt_config['si']
        self.msgmgr = SendManager()

    async def getcookie(self):
        flag = 0
        def read_cookie():
            with open("cookie", "r") as f:
                lines = f.readlines()
            self.cookie = lines[0].strip()
            if len(lines) >= 2:
                self.cookie_time = convert_date(int(lines[1].strip()))
            else:
                self.cookie_time = ''
        while True:
            if not os.path.exists("cookie"):
                flag = 1
                self.msgmgr.sendMsg("正在第一次获取登录cookie, 请微信扫码")
                await self.ws_controller(self.ws_login, retries=1000, delay=1)
            if not self.cookie:
                flag = 1
                read_cookie()
            if self.cookie_time and not check_time(self.cookie_time, 0):
                flag = 1
                self.msgmgr.sendMsg(f"cookie已失效, 请重新扫码")
                await self.ws_controller(self.ws_login, retries=1000, delay=1)
                read_cookie()
                continue
            elif self.cookie_time and (not check_time(self.cookie_time, 2880) and datetime.now().minute < 5 or not check_time(self.cookie_time, 120)):
                flag = 1
                self.msgmgr.sendMsg(f"cookie有效至{self.cookie_time}, 即将失效, 请重新扫码")
                await self.ws_controller(self.ws_login, retries=0, delay=1)
                read_cookie()
                continue
            code = self.check_cookie()
            if code == 1:
                flag = 1
                self.msgmgr.sendMsg(f"cookie已失效, 请重新扫码")
                await self.ws_controller(self.ws_login, retries=1000, delay=1)
                read_cookie()
            elif code == 0:
                if self.cookie_time and flag == 1 and check_time(self.cookie_time, 2880):
                    self.msgmgr.sendMsg(f"cookie有效至{self.cookie_time}")
                elif self.cookie_time and flag == 1:
                    self.msgmgr.sendMsg(f"cookie有效至{self.cookie_time}, 即将失效, 下个小时初注意扫码")
                elif flag == 1:
                    self.msgmgr.sendMsg(f"cookie有效, 有效期未知")
                break

    def weblogin(self,UserID,Auth):
        url=f"https://{domain}/pc/web_login"
        data={
            "UserID":UserID,
            "Auth":Auth
        }
        headers={
            "referer":f"https://{domain}/web?next=/v2/web/index&type=3",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Content-Type":"application/json"
        }
        try:
            res=requests.post(url=url,headers=headers,json=data,timeout=timeout)
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
            self.cookie_time = convert_date(int(date))
        else:
            content = self.cookie
        with open("cookie","w") as f:
            f.write(content)

    def check_cookie(self):
        info=self.get_basicinfo()
        if not info:
            return 2
        if info.get("code") == 0:
            return 0
        return 1
    
    def setAuthorization(self,res,lessonId):
        if res.headers.get("Set-Auth") is not None:
            self.lessonIdDict[lessonId]['Authorization']="Bearer "+res.headers.get("Set-Auth")

    def join_classroom(self):
        url=f"https://{domain}/v/course_meta/join_classroom"
        headers={
            "cookie":self.cookie,
            "x-csrftoken":self.cookie.split("csrftoken=")[1].split(";")[0],
            "Content-Type":"application/json"
        }
        classroomCodeList_del = []
        for classroomCode in self.classroomCodeList:
            data={"id":classroomCode}
            try:
                res=requests.post(url=url,headers=headers,json=data,timeout=timeout)
            except Exception as e:
                return
            if res.json().get("success", False) == True:
                self.msgmgr.sendMsg(f"班级邀请码/课堂暗号{classroomCode}使用成功")
                classroomCodeList_del.append(classroomCode)
            elif "班级邀请码或课堂暗号不存在" in res.json().get("msg", ""):
                self.msgmgr.sendMsg(f"班级邀请码/课堂暗号{classroomCode}不存在")
                classroomCodeList_del.append(classroomCode)
            # else:
            #    self.msgmgr.sendMsg(f"班级邀请码/课堂暗号{classroomCode}使用失败")
        self.classroomCodeList = list(set(self.classroomCodeList) - set(classroomCodeList_del))

    def get_basicinfo(self):
        url=f"https://{domain}/api/v3/user/basic-info"
        headers={
            "referer":f"https://{domain}/web?next=/v2/web/index&type=3",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie":self.cookie
        }
        try:
            res=requests.get(url=url,headers=headers,timeout=timeout).json()
            return res
        except Exception as e:
            return {}

    def lesson_info(self,lessonId):
        url=f"https://{domain}/api/v3/lesson/basic-info"
        headers={
            "referer":f"https://{domain}/lesson/fullscreen/v3/{lessonId}?source=5",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie":self.cookie,
            "Authorization":self.lessonIdDict[lessonId]['Authorization']
        }
        try:
            res=requests.get(url=url,headers=headers,timeout=timeout)
        except Exception as e:
            return
        self.setAuthorization(res,lessonId)
        classroomName = self.lessonIdDict[lessonId]['classroomName']
        try:
            self.lessonIdDict[lessonId]['title'] = res.json()['data']['title']
            self.lessonIdDict[lessonId]['header'] = f"课程: {classroomName}\n标题: {self.lessonIdDict[lessonId]['title']}\n教师: {res.json()['data']['teacher']['name']}\n开始时间: {convert_date(res.json()['data']['startTime'])}"
        except Exception as e:
            self.lessonIdDict[lessonId]['title'] = '未知标题'
            self.lessonIdDict[lessonId]['header'] = f"课程: {classroomName}\n标题: 获取失败\n教师: 获取失败\n开始时间: 获取失败"

    def getlesson(self):
        url=f"https://{domain}/api/v3/classroom/on-lesson-upcoming-exam"
        headers={
            "referer":f"https://{domain}/web?next=/v2/web/index&type=3",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie":self.cookie
        }
        try:
            online_data=requests.get(url=url,headers=headers,timeout=timeout).json()
        except Exception as e:
            return False
        try:
            self.lessonIdNewList = []
            if online_data['data']['onLessonClassrooms'] == []:
                for lessonId in self.lessonIdDict:
                    self.lessonIdDict[lessonId].get('websocket', '').close()
                self.lessonIdDict = {}
                return False
            for item in online_data['data']['onLessonClassrooms']:
                if (self.classroomWhiteList and item['classroomName'] not in self.classroomWhiteList) or item['classroomName'] in self.classroomBlackList or (self.classroomStartTimeDict and item['classroomName'] in self.classroomStartTimeDict and not check_time2(self.classroomStartTimeDict[item['classroomName']])):
                    continue
                lessonId = item['lessonId']
                if lessonId not in self.lessonIdDict:
                    self.lessonIdNewList.append(lessonId)
                    self.lessonIdDict[lessonId] = {}
                    self.lessonIdDict[lessonId]['start_time'] = time.time()
                    self.lessonIdDict[lessonId]['classroomName'] = item['classroomName']
                self.lessonIdDict[lessonId]['active'] = '1'
            to_delete = [lessonId for lessonId, details in self.lessonIdDict.items() if not details.get('active', '0') == '1']
            for lessonId in to_delete:
                del self.lessonIdDict[lessonId]
                self.lessonIdDict[lessonId].get('websocket', '').close()
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
            url=f"https://{domain}/api/v3/lesson/checkin"
            headers={
                "referer":f"https://{domain}/lesson/fullscreen/v3/{lessonId}?source=5",
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Content-Type":"application/json; charset=utf-8",
                "cookie":self.cookie
            }
            data={
                "source":5,
                "lessonId":lessonId
            }
            try:
                res=requests.post(url=url,headers=headers,json=data,timeout=timeout)
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
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 签到成功")
            elif checkin_status == 'LESSON_END':
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 课程已结束")
            else:
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 签到失败")
    
    async def fetch_presentation(self, lessonId):
        url = f"https://{domain}/api/v3/lesson/presentation/fetch?presentation_id={self.lessonIdDict[lessonId]['presentation']}"
        headers = {
            "referer": f"https://{domain}/lesson/fullscreen/v3/{lessonId}?source=5",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie": self.cookie,
            "Authorization": self.lessonIdDict[lessonId]['Authorization']
        }
        res=requests.get(url, headers=headers, timeout=timeout)
        self.setAuthorization(res, lessonId)
        info = res.json()
        slides=info['data']['slides']    #获得幻灯片列表
        problems = {}
        self.lessonIdDict[lessonId]['problems']={}
        self.lessonIdDict[lessonId]['covers']=[slide['index'] for slide in slides if slide.get('cover') is not None]
        for slide in slides:
            if slide.get("problem") is not None:
                self.lessonIdDict[lessonId]['problems'][slide['id']]=slide['problem']
                self.lessonIdDict[lessonId]['problems'][slide['id']]['index']=slide['index']
                problems[slide['index']] = {"problemType": int(slide['problem']['problemType']), "option_keys": [opt['key'] for opt in slide['problem'].get('options', [])], "option_values": [opt['value'] for opt in slide['problem'].get('options', [])], "num_blanks": len(slide['problem'].get('blanks', []))}
                if slide['problem']['body'] == '':
                    shapes = slide.get('shapes', [])
                    if shapes:
                        min_left_item = min(shapes, key=lambda item: item.get('Left', 9999999))
                        if min_left_item != 9999999 and min_left_item.get('Text') is not None:
                            self.lessonIdDict[lessonId]['problems'][slide['id']]['body'] = min_left_item['Text'] or '未知问题'
                        else:
                            self.lessonIdDict[lessonId]['problems'][slide['id']]['body'] = '未知问题'
                    else:
                        self.lessonIdDict[lessonId]['problems'][slide['id']]['body'] = '未知问题'
                problems[slide['index']]['body'] = self.lessonIdDict[lessonId]['problems'][slide['id']]['body'] if self.lessonIdDict[lessonId]['problems'][slide['id']]['body'] != '未知问题' else ''
        self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n{format_json_to_text(self.lessonIdDict[lessonId]['problems'], self.lessonIdDict[lessonId].get('unlockedproblem', []))}")
        folder_path=lessonId
        async def fetch_presentation_background():
            loop = asyncio.get_event_loop()
            problems_keys = [int(k) for k in problems.keys()]
            await loop.run_in_executor(None, clear_folder, folder_path)
            await loop.run_in_executor(None, download_images_to_folder, slides, folder_path)
            await loop.run_in_executor(None, concat_vertical_cv, folder_path, 0, 100)
            await loop.run_in_executor(None, concat_vertical_cv, folder_path, 1, 100)
            await loop.run_in_executor(None, concat_vertical_cv, folder_path, 2, 100)
            await loop.run_in_executor(None, concat_vertical_cv, folder_path, 3, 100, problems_keys)
            output_pdf_path=os.path.join(folder_path, f"{self.lessonIdDict[lessonId]['classroomName']}-{self.lessonIdDict[lessonId]['title']}.pdf")
            await loop.run_in_executor(None, images_to_pdf, folder_path, output_pdf_path)
            with open(os.path.join(folder_path, "problems.txt"), "w", encoding="utf-8") as f:
                f.write(str(problems))
            if self.ppt:
                if os.path.exists(output_pdf_path):
                    try:
                        self.msgmgr.sendFile(output_pdf_path)
                    except Exception as e:
                        self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: PPT推送失败")
                else:
                    self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 没有PPT")

            if self.llm:
                reply = await loop.run_in_executor(None, LLMManager().generateAnswer, folder_path)
                reply_text = "LLM答案列表:\n"
                for key in problems_keys:
                    reply_text += "-"*20 + "\n"
                    problemId = next((pid for pid, prob in self.lessonIdDict[lessonId]['problems'].items() if prob.get('index') == key), None)
                    problemType = {1:"单选题", 2:"多选题", 3:"投票题", 4:"填空题", 5:"主观题"}.get(self.lessonIdDict[lessonId]['problems'][problemId]['problemType'], "其它题型")
                    reply_text += f"PPT: 第{key}页 {problemType}\n"
                    if reply['best_answer'].get(key):
                        self.lessonIdDict[lessonId]['problems'][problemId]['llm_answer'] = reply['best_answer'][key]
                        reply_text += f"最佳答案: {reply['best_answer'][key]}\n所有答案:\n"
                        for r in reply["result"]:
                            if r["answer_dict"].get(key):
                                reply_text += f"[{r['score']}, {r['usedTime']}] {r['name']}: {r['answer_dict'][key]}\n"
                    else:
                        reply_text += f"无答案\n"
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: {reply_text}")

        asyncio.create_task(fetch_presentation_background())

    def answer(self,lessonId):
        url=f"https://{domain}/api/v3/lesson/problem/answer"
        headers={
            "referer":f"https://{domain}/lesson/fullscreen/v3/{lessonId}?source=5",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "cookie":self.cookie,
            "Content-Type":"application/json",
            "Authorization":self.lessonIdDict[lessonId]['Authorization']
        }
        llm_answer = self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']].get('llm_answer')
        if llm_answer:
            answer = llm_answer
        else:
            tp = self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['problemType']
            if tp == 1: # 单选题
                answer = [self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options'][0]['key']]
                problemType = "单选题"
            elif tp == 2: # 多选题
                answer = [self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options'][0]['key']]
                problemType = "多选题"
            elif tp == 3: # 投票题
                answer = [self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options'][0]['key']]
                problemType = "投票题"
            elif tp == 4: # 填空题
                answer = [''] * len(self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['blanks'])
                problemType = "填空题"
            elif tp == 5: # 主观题
                answer = ['']
                problemType = "主观题"
            else: # 其它题型
                answer = ['']
                problemType = "其它题型"
        data={
            "dt":int(time.time()*1000),
            "problemId":self.lessonIdDict[lessonId]['problemId'],
            "problemType":self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['problemType'],
            "result":answer
        }
        try:
            res=requests.post(url=url,headers=headers,json=data,timeout=timeout)
        except Exception as e:
            return
        self.setAuthorization(res,lessonId)
        self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\nPPT: 第{self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['index']}页 {problemType}\n问题: {self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['body']}\n提交答案: {answer}")

    async def ws_controller(self, func, *args, retries=3, delay=10):
        attempt = 0
        while attempt <= retries:
            try:
                await func(*args)
                return  # 如果成功就直接返回
            except Exception as e:
                print(traceback.format_exc())
                attempt += 1
                if attempt <= retries:
                    await asyncio.sleep(delay)
                    print(f"出现异常, 尝试重试 ({attempt}/{retries})")

    async def ws_login(self):
        uri = f"wss://{domain}/wsapp/"
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
            self.msgmgr.sendImage("qrcode.jpg")
            server_response = await asyncio.wait_for(recv_json(websocket),timeout=60)
            self.weblogin(server_response['UserID'],server_response['Auth'])

    async def ws_lesson(self,lessonId):
        flag_ppt=1
        flag_si=1
        def del_dict():
            nonlocal flag_ppt, flag_si
            flag_ppt=1
            flag_si=1
            keys_to_remove = ['presentation', 'si', 'unlockedproblem', 'covers']
            for key in keys_to_remove:
                if self.lessonIdDict[lessonId].get(key) is not None:
                    del self.lessonIdDict[lessonId][key]
        del_dict()
        uri = f"wss://{domain}/wsapp/"
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
            self.lessonIdDict[lessonId]['websocket'] = websocket
            while True and time.time()-self.lessonIdDict[lessonId]['start_time']<36000:
                try:
                    server_response = await recv_json(websocket)
                except Exception as e:
                    self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 连接断开")
                    break
                op=server_response['op']
                if op=="hello" or op=="fetchtimeline":
                    reversed_timeline = list(reversed(server_response['timeline']))
                    for item in reversed_timeline:
                        if 'pres' in item:
                            if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != item['pres']:
                                del_dict()
                                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                            self.lessonIdDict[lessonId]['presentation']=item['pres']
                            self.lessonIdDict[lessonId]['si']=item['si']
                            break
                    if server_response.get('presentation'):
                        if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != server_response['presentation']:
                            del_dict()
                            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                        self.lessonIdDict[lessonId]['presentation']=server_response['presentation']
                    if server_response.get('slideindex'):
                        self.lessonIdDict[lessonId]['si']=server_response['slideindex']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem']=server_response['unlockedproblem']
                elif op=="showpresentation" or op=="presentationupdated" or op=="presentationcreated":
                    if server_response.get('presentation'):
                        if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != server_response['presentation']:
                            del_dict()
                            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                        self.lessonIdDict[lessonId]['presentation']=server_response['presentation']
                    if server_response.get('slideindex'):
                        self.lessonIdDict[lessonId]['si']=server_response['slideindex']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem']=server_response['unlockedproblem']
                elif op=="slidenav":
                    if server_response['slide'].get('pres'):
                        if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != server_response['slide']['pres']:
                            del_dict()
                            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                        self.lessonIdDict[lessonId]['presentation']=server_response['slide']['pres']
                    if server_response['slide'].get('si'):
                        self.lessonIdDict[lessonId]['si']=server_response['slide']['si']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem']=server_response['unlockedproblem']
                elif op=="unlockproblem":
                    if server_response['problem'].get('pres'):
                        if flag_ppt==0 and self.lessonIdDict[lessonId]['presentation'] != server_response['problem']['pres']:
                            del_dict()
                            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                        self.lessonIdDict[lessonId]['presentation']=server_response['problem']['pres']
                    if server_response['problem'].get('si'):
                        self.lessonIdDict[lessonId]['si']=server_response['problem']['si']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem']=server_response['unlockedproblem']
                    self.lessonIdDict[lessonId]['problemId']=server_response['problem']['prob']
                    problemType = {1:"单选题", 2:"多选题", 3:"投票题", 4:"填空题", 5:"主观题"}.get(self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['problemType'], "其它题型")
                    text_result = f"PPT: 第{self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['index']}页 {problemType}\n问题: {self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['body']}\n"
                    answer = self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']].get('llm_answer', [])
                    if 'options' in self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]:
                        for option in self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options']:
                            text_result += f"- {option['key']}: {option['value']}\n"
                    if answer not in [[],None,'null']:
                        answer_text = ', '.join(answer)
                        text_result += f"答案: {answer_text}\n"
                    else:
                        text_result += "答案: 暂无\n"
                    self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n解锁问题:\n{text_result}")
                    if self.an:
                        await asyncio.sleep(randint(5,10))
                        self.answer(lessonId)
                elif op=="lessonfinished":
                    self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 下课了")
                    break
                if flag_ppt==1 and self.lessonIdDict[lessonId].get('presentation') is not None:
                    flag_ppt=0
                    await self.fetch_presentation(lessonId)
                if flag_si==1 and self.lessonIdDict[lessonId].get('si') is not None and self.lessonIdDict[lessonId].get('covers') is not None and self.lessonIdDict[lessonId]['si'] in self.lessonIdDict[lessonId]['covers']:
                    self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 正在播放PPT第{self.lessonIdDict[lessonId]['si']}页")
                    if self.si:
                        del self.lessonIdDict[lessonId]['si']
                    else:
                        flag_si=0
            self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 连接关闭")
            del self.lessonIdDict[lessonId]

    async def lesson_attend(self):
        tasks = [asyncio.create_task(self.ws_lesson(lessonId)) for lessonId in self.lessonIdNewList]
        asyncio.gather(*tasks)
        self.lessonIdNewList = []

async def ykt_user():
    ykt = yuketang()
    while True:
        await ykt.getcookie()
        ykt.join_classroom()
        if ykt.getlesson():
            ykt.lesson_checkin()
            await ykt.lesson_attend()
        await asyncio.sleep(30)
