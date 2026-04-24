import asyncio
import websockets
import json
import requests
import os
import time
import re
import ast
from datetime import datetime
from weakref import WeakValueDictionary
from random import randint
from send import SendManager
from llm import LLMManager
from draw import compose_from_strlist
from util import *

current_dir = os.path.dirname(os.path.abspath(__file__))
home_dir = os.environ.get("YUKETANG_HOME", current_dir)
data_dir = os.path.join(home_dir, "data")
os.makedirs(data_dir, exist_ok=True)
cookie_dir = os.path.join(data_dir, "cookie")
token_dir = os.path.join(data_dir, "token")
qr_dir = os.path.join(data_dir, "qr")
file_dir = os.path.join(data_dir, "file")
for path in (cookie_dir, token_dir, qr_dir, file_dir):
    os.makedirs(path, exist_ok=True)
os.chdir(home_dir)

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

timeout = config['yuketang']['timeout']
users = config['yuketang']['users']
exam_answer_cache = {}

_FETCH_LOCKS: dict[int, WeakValueDictionary] = {}

def _get_fetch_lock(att, index):
    key = str(att)
    fetch_lock = _FETCH_LOCKS.get(index)
    if fetch_lock is None:
        fetch_lock = WeakValueDictionary()
        _FETCH_LOCKS[index] = fetch_lock

    lock = fetch_lock.get(key)
    if lock is None:
        lock = asyncio.Lock()
        fetch_lock[key] = lock

    return lock

class yuketang:
    def __init__(self, yt_config, idx):
        self.idx = idx
        self.cookie = ''
        self.cookieTime = ''
        self.username = ''
        self.lessonIdNewList = []
        self.examIdNewList = []
        self.lessonIdDict = {}
        self.examIdDict = {}
        self.name = yt_config['name']
        self.domain = yt_config['domain']
        self.services = yt_config.get('services', [])
        self.lessonConfig = {
            **{
                "classroomWhiteList": [],
                "classroomBlackList": [],
                "classroomStartTimeDict": {},
                "llm": False,
                "an": False,
                "ppt": False,
                "si": False,
            },
            **yt_config.get("lesson", {})
        }
        self.examConfig = {
            **{
                "classroomWhiteList": [],
                "llm": False,
                "an": False,
                "paper": False,
                "isMaster": False,
                "isSlave": False,
                "x_access_token": ""
            },
            **yt_config.get("exam", {})
        }
        self.otherConfig = {
            **{
                "classroomCodeList": []
            },
            **yt_config.get("other", {})
        }
        self.msgmgr = SendManager(f"[{self.name}]\n", self.services)
        self.ua = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36"

    async def get_cookie(self):
        flag = 0
        qr_filename = os.path.join(qr_dir, f"qrcode_{sanitize_filename(self.name)}.jpg")
        cookie_filename = os.path.join(cookie_dir, f"cookie_{sanitize_filename(self.name)}.txt")
        def read_cookie():
            with open(cookie_filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            self.cookie = lines[0].strip()
            self.cookieTime = convert_date(int(lines[1].strip())) if len(lines) > 1 else ''
            self.username = lines[2].strip() if len(lines) > 2 else ''
            self.msgmgr = SendManager(f"[{self.name}] {self.username}\n", self.services)
        while True:
            if not os.path.exists(cookie_filename):
                flag = 1
                await asyncio.to_thread(self.msgmgr.sendMsg, "正在第一次获取登录cookie, 请微信扫码")
                await self.ws_controller(self.ws_login, retries=1000, delay=1)
            if not self.cookie:
                flag = 1
                read_cookie()
            if self.cookieTime and not check_time(self.cookieTime, 0):
                flag = 1
                await asyncio.to_thread(self.msgmgr.sendMsg, "cookie已失效, 请重新扫码")
                await self.ws_controller(self.ws_login, retries=1000, delay=1)
                read_cookie()
                continue
            elif self.cookieTime and (not check_time(self.cookieTime, 2880) and datetime.now().minute < 5 or not check_time(self.cookieTime, 120)):
                flag = 1
                await asyncio.to_thread(self.msgmgr.sendMsg, f"cookie有效至{self.cookieTime}, 即将失效, 请重新扫码")
                await self.ws_controller(self.ws_login, retries=0, delay=1)
                read_cookie()
                continue
            code = self.check_yuketang_cookie()
            if code == 1:
                flag = 1
                await asyncio.to_thread(self.msgmgr.sendMsg, "cookie已失效, 请重新扫码")
                await self.ws_controller(self.ws_login, retries=1000, delay=1)
                read_cookie()
            elif code == 0:
                if self.cookieTime and flag == 1 and check_time(self.cookieTime, 2880):
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"cookie有效至{self.cookieTime}")
                elif self.cookieTime and flag == 1:
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"cookie有效至{self.cookieTime}, 即将失效, 下个小时初注意扫码")
                elif flag == 1:
                    await asyncio.to_thread(self.msgmgr.sendMsg, "cookie有效, 有效期未知")
                if not self.username:
                    self.get_username()
                if os.path.exists(qr_filename):
                    try:
                        os.remove(qr_filename)
                    except Exception:
                        pass
                break

    def get_username(self):
        url = f"https://{self.domain}/v2/api/web/userinfo"
        headers = {
            "referer": f"https://{self.domain}/v2/web/index",
            "User-Agent": self.ua,
            "cookie": self.cookie
        }
        try:
            res = requests.get(url, headers=headers, timeout=timeout)
            name = res.json()['data'][0]['name']
            self.username = name
            self.msgmgr = SendManager(f"[{self.name}] {self.username}\n", self.services)
        except Exception as e:
            print(f"获取用户信息失败: {e}")

    def login_yuketang(self, UserID, Auth):
        url = f"https://{self.domain}/pc/web_login"
        data = {
            "UserID": UserID,
            "Auth": Auth
        }
        headers = {
            "referer" : f"https://{self.domain}/web?next=/v2/web/index&type=3",
            "User-Agent" : self.ua,
            "Content-Type" : "application/json"
        }
        try:
            res = requests.post(url=url, headers=headers, json=data, timeout=timeout)
        except Exception as e:
            print(f"登录失败: {e}")
            return
        cookies = res.cookies
        self.cookie = ""
        for k, v in cookies.items():
            self.cookie += f'{k}={v};'
        date = cookie_date(res)
        self.get_username()
        content = f'{self.cookie}\n{date}\n{self.username}'
        self.cookieTime = convert_date(int(date))
        with open(os.path.join(cookie_dir, f"cookie_{sanitize_filename(self.name)}.txt"), "w", encoding="utf-8") as f:
            f.write(content)

    def check_yuketang_cookie(self):
        url = f"https://{self.domain}/api/v3/user/basic-info"
        headers = {
            "referer": f"https://{self.domain}/web?next=/v2/web/index&type=3",
            "User-Agent": self.ua,
            "cookie": self.cookie
        }
        try:
            res = requests.get(url=url, headers=headers, timeout=timeout).json()
            if res.get("code") == 0:
                return 0
            return 1
        except:
            return 2

    def set_authorization(self, res, lessonId):
        if res.headers.get("Set-Auth") is not None:
            self.lessonIdDict[lessonId]['Authorization'] = "Bearer " + res.headers.get("Set-Auth")

    def join_classroom(self):
        classroomCodeList_del = []
        for classroomCode in self.otherConfig['classroomCodeList']:
            if len(classroomCode) == 5:
                data = {"source": 14, "inviteCode": classroomCode}
                url = f"https://{self.domain}/api/v3/lesson/notkn/checkin"
                headers = {
                    "cookie" : self.cookie,
                    "x-csrftoken" : self.cookie.split("csrftoken=")[1].split(";")[0],
                    "Content-Type" : "application/json"
                }
                try:
                    res = requests.post(url=url, headers=headers, json=data, timeout=timeout)
                except:
                    continue
                if res.json().get("msg", "") == "OK":
                    self.msgmgr.sendMsg(f"课堂暗号{classroomCode}使用成功, 正在上课")
                    classroomCodeList_del.append(classroomCode)
                elif res.json().get("msg", "") == "LESSON_END_JOIN":
                    self.msgmgr.sendMsg(f"课堂暗号{classroomCode}使用成功, 课堂已结束")
                    classroomCodeList_del.append(classroomCode)
                elif res.json().get("msg", "") == "LESSON_INVITE_CODE_TIMEOUT":
                    self.msgmgr.sendMsg(f"课堂暗号{classroomCode}不存在")
                    classroomCodeList_del.append(classroomCode)
                # else:
                #    self.msgmgr.sendMsg(f"课堂暗号{classroomCode}使用失败")
            elif len(classroomCode) == 6:
                data = {"id": classroomCode}
                url = f"https://{self.domain}/v/course_meta/join_classroom"
                headers = {
                    "cookie": self.cookie,
                    "x-csrftoken": self.cookie.split("csrftoken=")[1].split(";")[0],
                    "Content-Type": "application/json"
                }
                try:
                    res = requests.post(url=url, headers=headers, json=data, timeout=timeout)
                except:
                    continue
                if res.json().get("success", False) == True:
                    self.msgmgr.sendMsg(f"班级邀请码{classroomCode}使用成功")
                    classroomCodeList_del.append(classroomCode)
                elif "班级邀请码或课堂暗号不存在" in res.json().get("msg", ""):
                    self.msgmgr.sendMsg(f"班级邀请码{classroomCode}不存在")
                    classroomCodeList_del.append(classroomCode)
                # else:
                #    self.msgmgr.sendMsg(f"班级邀请码{classroomCode}使用失败")
            else:
                self.msgmgr.sendMsg(f"班级邀请码/课堂暗号{classroomCode}格式错误")
                classroomCodeList_del.append(classroomCode)
                continue
        self.otherConfig['classroomCodeList'] = list(set(self.otherConfig['classroomCodeList']) - set(classroomCodeList_del))

    def get_lesson_info(self, lessonId):
        url = f"https://{self.domain}/api/v3/lesson/basic-info"
        headers = {
            "referer": f"https://{self.domain}/lesson/fullscreen/v3/{lessonId}?source=5",
            "User-Agent": self.ua,
            "cookie": self.cookie,
            "Authorization": self.lessonIdDict[lessonId]['Authorization']
        }
        try:
            res = requests.get(url=url, headers=headers, timeout=timeout)
        except:
            return
        self.set_authorization(res, lessonId)
        classroomName = self.lessonIdDict[lessonId]['classroomName']
        self.lessonIdDict[lessonId]['header'] = f"PPT编号: {self.lessonIdDict[lessonId].get('presentation', '待获取')}\n课程: {classroomName}\n"
        try:
            self.lessonIdDict[lessonId]['title'] = res.json()['data']['title']
            self.lessonIdDict[lessonId]['header'] += f"标题: {self.lessonIdDict[lessonId]['title']}\n教师: {res.json()['data']['teacher']['name']}\n开始时间: {convert_date(res.json()['data']['startTime'])}"
        except:
            self.lessonIdDict[lessonId]['title'] = '未知标题'
            self.lessonIdDict[lessonId]['header'] += f"标题: 获取失败\n教师: 获取失败\n开始时间: 获取失败"

    def get_lesson(self):
        to_close_ids = []
        self.lessonIdNewList = []
        url = f"https://{self.domain}/api/v3/classroom/on-lesson-upcoming-exam"
        headers = {
            "referer": f"https://{self.domain}/web?next=/v2/web/index&type=3",
            "User-Agent": self.ua,
            "cookie": self.cookie
        }
        try:
            data = requests.get(url=url, headers=headers, timeout=timeout).json()['data']

            for item in data['onLessonClassrooms']:
                if (self.lessonConfig['classroomWhiteList'] and item['classroomName'] not in self.lessonConfig['classroomWhiteList']) or item['classroomName'] in self.lessonConfig['classroomBlackList'] or (self.lessonConfig['classroomStartTimeDict'] and item['classroomName'] in self.lessonConfig['classroomStartTimeDict'] and not check_time2(self.lessonConfig['classroomStartTimeDict'][item['classroomName']])):
                    continue
                lessonId = item['lessonId']
                if lessonId not in self.lessonIdDict:
                    self.lessonIdNewList.append(lessonId)
                    self.lessonIdDict[lessonId] = {}
                    self.lessonIdDict[lessonId]['startTime'] = time.time()
                    self.lessonIdDict[lessonId]['classroomName'] = item['classroomName']
                self.lessonIdDict[lessonId]['active'] = '1'

            to_delete = [lessonId for lessonId, details in self.lessonIdDict.items() if details.get('active', '0') != '1']
            to_close_ids.extend(to_delete)

            for lessonId in self.lessonIdDict:
                self.lessonIdDict[lessonId]['active'] = '0'

            return (bool(self.lessonIdNewList), to_close_ids)
        except:
            return (False, [])

    def checkin_lesson(self):
        newList = self.lessonIdNewList.copy()
        for lessonId in newList:
            url = f"https://{self.domain}/api/v3/lesson/checkin"
            headers = {
                "referer": f"https://{self.domain}/lesson/fullscreen/v3/{lessonId}?source=5",
                "User-Agent": self.ua,
                "Content-Type": "application/json; charset=utf-8",
                "cookie": self.cookie
            }
            data = {
                "source": 5,
                "lessonId": lessonId
            }
            try:
                res = requests.post(url=url, headers=headers, json=data, timeout=timeout)
            except:
                continue
            self.set_authorization(res, lessonId)
            self.get_lesson_info(lessonId)
            try:
                self.lessonIdDict[lessonId]['Auth'] = res.json()['data']['lessonToken']
                self.lessonIdDict[lessonId]['userid'] = res.json()['data']['identityId']
            except:
                self.lessonIdDict[lessonId]['Auth'] = ''
                self.lessonIdDict[lessonId]['userid'] = ''
            checkin_status = res.json()['msg']
            if checkin_status == 'OK':
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 签到成功")
            elif checkin_status == 'LESSON_END':
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 课程已结束")
            else:
                self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\n消息: 签到失败")

    def get_course_list(self):
        url = f"https://{self.domain}/v2/api/web/courses/list?identity=2"
        headers = {
            "referer": f"https://{self.domain}/v2/web/index",
            "User-Agent": self.ua,
            "Content-Type": "application/json; charset=utf-8",
            "cookie": self.cookie
        }
        try:
            courseList = requests.get(url, headers=headers, timeout=timeout).json()['data']['list']
            return courseList
        except:
            return []

    def get_exam_info(self, examId, classroomId):
        folder = os.path.join(file_dir, self.domain, "exam", examId)
        if os.path.exists(os.path.join(folder, "cover.json")):
            with open(os.path.join(folder, "cover.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        url = f"https://{self.domain}/v/exam/cover?exam_id={examId}&classroom_id={classroomId}"
        headers = {
            "referer": f"https://{self.domain}/v2/web/exam/{classroomId}/{examId}",
            "User-Agent": self.ua,
            "Content-Type": "application/json; charset=utf-8",
            "cookie": self.cookie
        }
        try:
            r = requests.get(url=url, headers=headers, timeout=timeout).json()
            if r.get('status', -1) == 200: return r
            return {}
        except:
            return {}

    async def get_exam(self, courseList):
        self.examIdNewList = []
        to_close_ids = []
        for course in courseList:
            if course['name'] not in self.examConfig['classroomWhiteList']: continue
            url = f"https://{self.domain}/v2/api/web/logs/learn/{course['classroom_id']}?actype=5&page=0&offset=100&sort=-1"
            headers = {
                "User-Agent": self.ua,
                "Content-Type": "application/json; charset=utf-8",
                "cookie": self.cookie
            }
            try:
                resp = await asyncio.to_thread(requests.get, url, headers=headers, timeout=timeout)
                exams = resp.json()['data']['activities']
                valid_ids = {exam['courseware_id'] for exam in exams}
                to_close_ids.extend([exam_id for exam_id in self.examIdDict if exam_id not in valid_ids])
                for exam in exams:
                    examId = exam['courseware_id']
                    text = ''
                    if exam['status'] in [0, 1] and examId not in self.examIdDict:
                        info = await asyncio.to_thread(self.get_exam_info, examId, course['classroom_id'])
                        data = info.get('data', {})
                        if not data: continue
                        self.examIdDict[examId] = {
                            'cover': info,
                            'paper_status': False,
                            'cookie': "x_access_token=" + self.examConfig['x_access_token'] if self.examConfig['x_access_token'] else '',
                            'cookie_timestamp': 0,
                            'classroom_id': course['classroom_id'],
                            'classroom_name': course['course']['name'],
                            'teacher': course['teacher']['name'],
                            'create_time': exam['create_time'],
                            'title': exam['title'],
                            'limit': exam['limit'],
                            'deadline': exam['deadline'],
                            'total_score': exam['total_score'],
                            'problem_count': exam['problem_count'],
                            'online_proctor': exam['online_proctor'],
                            'description': data['description'],
                            'show_score': data['show_score'],
                            'show_score_time': data['show_score_time'],
                            'start_time': data['start_time'],
                            'limit_early_submission': data['limit_early_submission'],
                            'limit_early_submission_time': data['limit_early_submission_time'],
                            'identity_auth': data['identity_auth'],
                            'max_retry': data['max_retry'],
                            'way_of_score': data['way_of_score'],
                            'web_random_take_face_photo': data['web_random_take_face_photo'],
                            'page_switch_detection': data['page_switch_detection'],
                            'screen_capture': data['face_auth_status'].get('screen_capture', 0),
                            'max_screen_cuts_num': data['max_screen_cuts_num'],
                            'is_manual_review': data['is_manual_review'],
                            'en_copy': data['en_copy'],
                            'en_crypt': data['en_crypt'],
                            'force_confirm': data['force_confirm'],
                            'active': '0'
                        }
                        if exam['status'] == 0:
                            text = "您有一门考试待开始"
                    if exam['status'] == 1 and self.examIdDict[examId]['active'] == '0':
                        text = "您有一门考试正在进行中"
                        self.examIdNewList.append(examId)
                        self.examIdDict[examId]['active'] = '1'
                    if text:
                        text += f"\n试卷编号: {examId}\n课程: {self.examIdDict[examId]['classroom_name']}\n教师: {self.examIdDict[examId]['teacher']}\n标题: {self.examIdDict[examId]['title']}\n发布时间: {convert_date(self.examIdDict[examId]['create_time'])}\n总分: {self.examIdDict[examId]['total_score']} 分\n题目数量: {self.examIdDict[examId]['problem_count']} 道\n考试时长: {str(self.examIdDict[examId]['limit'] // 60) + ' 分钟' if self.examIdDict[examId]['limit'] > 0 else '不限'}\n开始时间: {convert_date(self.examIdDict[examId]['start_time'])}\n截止时间: {convert_date(self.examIdDict[examId]['deadline']) if self.examIdDict[examId]['deadline'] > 0 else '无'}\n考试说明: {self.examIdDict[examId]['description'] or '无'}\n作答次数: {self.examIdDict[examId]['max_retry' if self.examIdDict[examId]['max_retry'] > 0 else '不限']} 次"
                        if self.examIdDict[examId]['max_retry'] != 1:
                            if self.examIdDict[examId]['way_of_score'] == 1:
                                text += "\n评分方式: 取最高成绩"
                            else:
                                text += "\n评分方式: 取最后一次成绩"
                        if self.examIdDict[examId]['limit_early_submission']:
                            text += f"\n是否限制提前交卷: 是, 考试前 {self.examIdDict[examId]['limit_early_submission_time']} 分钟内不可交卷"
                        else:
                            text += "\n是否限制提前交卷: 否"
                        if self.examIdDict[examId]['online_proctor'] == 1:
                            text += f"\n在线监考: 启用\n身份认证: {'启用' if self.examIdDict[examId]['identity_auth'] == 1 else '未启用'}\n面部随机拍照: {'启用' if self.examIdDict[examId]['web_random_take_face_photo'] == 1 else '未启用'}\n电脑桌面截屏: {'启用' if self.examIdDict[examId]['screen_capture'] == 1 else '未启用'}\n考前身份人工审核: {'启用' if self.examIdDict[examId]['is_manual_review'] == 1 else '未启用'}"
                            if self.examIdDict[examId]['page_switch_detection'] == 1:
                                text += "\n页面切换检测: 启用"
                                if self.examIdDict[examId]['max_screen_cuts_num'] > 0:
                                    text += f", 离开作答界面 {self.examIdDict[examId]['max_screen_cuts_num']} 次, 系统自动收卷"
                                else:
                                    text += ", 离开作答界面次数不限"
                            else:
                                text += "\n页面切换检测: 未启用"
                        else:
                            text += "\n在线监考: 未启用"
                        if self.examIdDict[examId]['show_score']:
                            text += "\n成绩公布时间: 提交后立即显示"
                        elif self.examIdDict[examId]['show_score_time'] > 0:
                            text += f"\n成绩公布时间: {convert_date(self.examIdDict[examId]['show_score_time'])}"
                        else:
                            text += "\n成绩公布时间: 不显示成绩"
                        text += f"\n是否允许复制粘贴: {'是' if self.examIdDict[examId]['en_copy'] else '否'}\n是否强制确认: {'是' if self.examIdDict[examId]['force_confirm'] else '否'}\n试卷加密: {'是' if self.examIdDict[examId]['en_crypt'] else '否'}"
                        await asyncio.to_thread(self.msgmgr.sendMsg, text)
                    if exam['status'] == 1 and self.examIdDict[examId]['paper_status'] and self.examConfig['isMaster']:
                        answer = await self.get_cache_answer(examId)
                        if answer:
                            global exam_answer_cache
                            exam_answer_cache[self.idx][examId] = answer
                    if exam['status'] == 1 and self.examIdDict[examId]['paper_status'] and self.examConfig['isSlave']:
                        master_answer_cache = exam_answer_cache.copy()
                        synchronized = True
                        for answer_cache in master_answer_cache.values():
                            if examId not in answer_cache: continue
                            for problemId, ans in answer_cache[examId].items():
                                self.examIdDict[examId]['problems'][problemId]['master_answer'] = ans
                                submitted_answer = self.examIdDict[examId]['problems'][problemId].get('submitted_answer', None)
                                if not submitted_answer or not equal_unordered(ans, submitted_answer):
                                    synchronized = False
                        if not synchronized:
                            await asyncio.to_thread(self.msgmgr.sendMsg, f"试卷编号: {examId}\n试卷答案待同步")
                            await self.answer_exam(examId)
                    if exam['status'] not in [0, 1]:
                        to_close_ids.append(examId)
            except:
                pass
        return to_close_ids

    def generate_xuetangx_token(self, examId):
        url = f"https://{self.domain}/v/exam/gen_token"
        headers = {
            "cookie": self.cookie,
            "x-csrftoken": self.cookie.split("csrftoken=")[1].split(";")[0],
            "User-Agent": self.ua
        }
        data = {
            "exam_id": examId,
            "classroom_id": self.examIdDict[examId]['classroom_id']
        }
        try:
            r = requests.post(url, headers=headers, json=data, timeout=timeout).json()['data']
            return r
        except:
            return None

    def check_xuetangx_cookie(self, examId):
        url = f"https://examination.xuetangx.com/exam_room/refresh_time?exam_id={examId}"
        headers = {
            "cookie": self.examIdDict[examId]['cookie'],
            "User-Agent": self.ua
        }
        try:
            r = requests.get(url, headers=headers, timeout=timeout).json()
            return int(r['errcode']) == 0
        except:
            return False

    async def login_xuetangx(self, examId):
        async with _get_fetch_lock(self.idx, 3):  # 同一用户串行, 跨用户并行
            await asyncio.sleep(5)
            if examId not in self.examIdDict: return
            if self.examConfig['x_access_token'] or self.examIdDict[examId]['cookie'] and self.examIdDict[examId]['cookie_timestamp'] > time.time() + 600 and self.check_xuetangx_cookie(examId): return
            self.examIdDict[examId]['cookie'] = ''
            self.examIdDict[examId]['cookie_timestamp'] = 0
            data = await asyncio.to_thread(self.generate_xuetangx_token, examId)
            if not data: return
            token = data["token"]
            userId = data["user_id"]
            url = "https://examination.xuetangx.com/login"
            headers = {
                "User-Agent": self.ua
            }
            params = {
                "exam_id": examId,
                "user_id": userId,
                "crypt": token,
                "next": f"https://examination.xuetangx.com/exam/{examId}?isFrom=2",
                "language": "zh"
            }
            try:
                res = await asyncio.to_thread(requests.get, url, headers=headers, params=params, allow_redirects=True, timeout=timeout)
                cookie = res.history[0].headers['Set-Cookie']
                if examId not in self.examIdDict: return
                self.examIdDict[examId]['cookie'] = cookie
                self.examIdDict[examId]['cookie_timestamp'] = rfc1123_gmt_to_ts(cookie.split("expires=")[1].split(";")[0])
            except Exception as e:
                print(f"登录失败: {e}")

    async def fetch_paper(self, examId):
        async with _get_fetch_lock(self.idx, 4):  # 同一用户串行, 跨用户并行
            if examId not in self.examIdDict: return
            exam = self.examIdDict[examId].copy()
            folder = os.path.join(file_dir, self.domain, "exam", examId)
            if os.path.exists(os.path.join(folder, "paper.json")):
                with open(os.path.join(folder, "paper.json"), "r", encoding="utf-8") as f:
                    info = json.load(f)
            else:
                await self.login_xuetangx(examId)
                url = f"https://examination.xuetangx.com/exam_room/show_paper?exam_id={examId}"
                headers = {
                    "referer": f"https://examination.xuetangx.com/exam/{examId}?isFrom=2",
                    "User-Agent": self.ua,
                    "cookie": self.examIdDict[examId]['cookie']
                }
                res = await asyncio.to_thread(requests.get, url, headers=headers, timeout=timeout)
                info = res.json()
                if info.get('errcode', -1) != 0: return

            problems = {}
            problemsIdList = []
            problemsBlockList = []
            text = '问题列表:'
            i = 0
            if info['data']['has_problem_dict']:
                for item in info['data']['problems']:
                    desc = convert_body_to_text(item['Body'])
                    text += "\r" + "-"*30 + "\r" + item['title'].strip()
                    if desc: text += "\r" + desc
                    for problem in item['problems']:
                        i += 1
                        renameTxt = problem.get('TypeRenameText', '').strip()
                        prefix = (desc + '\r' if desc else '') + (renameTxt + '\r' if renameTxt else '')
                        body = convert_body_to_text(problem['Body'])
                        body2 = convert_body_to_text(problem['Body'], True)
                        problemsIdList.append(int(problem['ProblemID']))
                        problems[i] = {"problemType": int(problem['ProblemType']), "option_keys": [opt['key'] for opt in problem['Options']], "option_values": [convert_body_to_text(opt['value']) for opt in problem['Options']], "num_blanks": len(problem.get('Blanks', [])), "pollingCount": int(problem.get('PollingCount', 1)), "score": float(problem.get('Score', 0)), "body": prefix + body}
                        problemType = {1: "单选题", 2: "多选题", 3: "投票题", 4: "填空题", 5: "主观题", 6: "判断题"}.get(problems[i]['problemType'], "其它题型")
                        text += "\r" + "-"*20 + f"\r第{i}题 {problemType} {fmt_num(problems[i]['score'] * 100.0)}分"
                        text2 = desc + f"\r第{i}题 {problemType}"
                        if problems[i]['problemType'] == 3:
                            text += f" 最多投票{problems[i]['pollingCount']}项"
                            text += " 匿名投票" if problem['Anonymous'] else " 非匿名投票"
                            text2 += f" 最多投票{problems[i]['pollingCount']}项"
                        if renameTxt: text += f"\r{renameTxt}"
                        text += "\r问题: " + body
                        text2 += "\r问题: " + body2
                        if problems[i]['problemType'] in [1, 2, 3]:
                            for key, value in zip(problems[i]['option_keys'], problems[i]['option_values']):
                                text += f"\r- {key}: {value}"
                            for opt in problem['Options']:
                                key = opt['key']
                                value = convert_body_to_text(opt['value'], True)
                                text2 += f"\r- {key}:\r{value}"
                        elif problems[i]['problemType'] == 6:
                            for key in problems[i]['option_keys']:
                                text += f"\r- {key}"
                                text2 += f"\r- {key}"
                        problemsBlockList.append(text2)
            else:
                for problem in info['data']['problems']:
                    i += 1
                    renameTxt = problem.get('TypeRenameText', '').strip()
                    prefix = renameTxt + '\r' if renameTxt else ''
                    body = convert_body_to_text(problem['Body'])
                    body2 = convert_body_to_text(problem['Body'], True)
                    problemsIdList.append(int(problem['ProblemID']))
                    problems[i] = {"problemType": int(problem['ProblemType']), "option_keys": [opt['key'] for opt in problem['Options']], "option_values": [convert_body_to_text(opt['value']) for opt in problem['Options']], "num_blanks": len(problem.get('Blanks', [])), "pollingCount": int(problem.get('PollingCount', 1)), "score": float(problem.get('Score', 0)), "body": prefix + body}
                    problemType = {1: "单选题", 2: "多选题", 3: "投票题", 4: "填空题", 5: "主观题", 6: "判断题"}.get(problems[i]['problemType'], "其它题型")
                    text += "\r" + "-"*20 + f"\r第{i}题 {problemType} {fmt_num(problems[i]['score'] * 100.0)}分"
                    text2 = f"第{i}题 {problemType}"
                    if problems[i]['problemType'] == 3:
                        text += f" 最多投票{problems[i]['pollingCount']}项"
                        text += " 匿名投票" if problem['Anonymous'] else " 非匿名投票"
                        text2 += f" 最多投票{problems[i]['pollingCount']}项"
                    if renameTxt: text += f"\r{renameTxt}"
                    text += "\r问题: " + body
                    text2 += "\r问题: " + body2
                    if problems[i]['problemType'] in [1, 2, 3]:
                        for key, value in zip(problems[i]['option_keys'], problems[i]['option_values']):
                            text += f"\r- {key}: {value}"
                        for opt in problem['Options']:
                            key = opt['key']
                            value = convert_body_to_text(opt['value'], True)
                            text2 += f"\r- {key}:\r{value}"
                    elif problems[i]['problemType'] == 6:
                        for key in problems[i]['option_keys']:
                            text += f"\r- {key}"
                            text2 += f"\r- {key}"
                    problemsBlockList.append(text2)
            problemsIdList.sort()
            text = text.replace('\r', '\n')
            await asyncio.to_thread(self.msgmgr.sendMsg, f"试卷编号: {examId}\n{text}")

        async with _get_fetch_lock(self.idx, 5):  # 同一用户串行, 跨用户并行
            if examId not in self.examIdDict: return
            if not os.path.exists(folder) or not os.path.exists(os.path.join(folder, "paper.json")):
                await asyncio.to_thread(clear_folder, folder)
                with open(os.path.join(folder, "cover.json"), "w", encoding="utf-8") as f:
                    json.dump(exam['cover'], f, ensure_ascii=False, indent=4)
                with open(os.path.join(folder, "paper.json"), "w", encoding="utf-8") as f:
                    json.dump(info, f, ensure_ascii=False, indent=4)

            output_pdf_path = os.path.join(folder, sanitize_filename(exam['title'].strip()) + ".pdf")
            if not os.path.exists(folder) or not os.path.exists(output_pdf_path):
                for idx, block in enumerate(problemsBlockList):
                    await asyncio.to_thread(compose_from_strlist, block.split("\r"), os.path.join(folder, f"raw_{idx + 1}.jpg"))
                await asyncio.to_thread(images_to_pdf, folder, output_pdf_path)

            if self.examConfig['paper']:
                if os.path.exists(output_pdf_path):
                    try:
                        await asyncio.to_thread(self.msgmgr.sendFile, output_pdf_path)
                    except:
                        await asyncio.to_thread(self.msgmgr.sendMsg, f"试卷编号: {examId}\n消息: 试卷推送失败")
                else:
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"试卷编号: {examId}\n消息: 没有试卷")

            problems_keys = [int(k) for k in problems.keys()]
            if not os.path.exists(os.path.join(folder, "problems.txt")):
                if problems:
                    await asyncio.to_thread(concat_vertical_cv, folder, 0, 100, [], False)
                    await asyncio.to_thread(concat_vertical_cv, folder, 1, 100, [], False)
                    await asyncio.to_thread(concat_vertical_cv, folder, 2, 100, [], False)
                    await asyncio.to_thread(concat_vertical_cv, folder, 3, 100, problems_keys, False)
                    await asyncio.to_thread(concat_vertical_cv, folder, 4, 100, [], False)
                with open(os.path.join(folder, "problems.txt"), "w", encoding="utf-8") as f:
                    f.write(str(problems))

            reply = None
            results = {key: {} for key in problemsIdList}
            if problems:
                if os.path.exists(os.path.join(folder, "reply.txt")):
                    with open(os.path.join(folder, "reply.txt"), "r", encoding="utf-8") as f:
                        reply = ast.literal_eval(f.read().strip())
                elif self.examConfig['llm']:
                    reply = await asyncio.to_thread(LLMManager().generateAnswer, folder)
                    if reply.get('best_answer', {}):
                        with open(os.path.join(folder, "reply.txt"), "w", encoding="utf-8") as f:
                            f.write(str(reply))
                    else:
                        reply = None
                if reply is not None:
                    reply_text = "LLM答案列表:"
                    for key in problems_keys:
                        reply_text += "\n" + "-"*20
                        problemType = {1: "单选题", 2: "多选题", 3: "投票题", 4: "填空题", 5: "主观题", 6: "判断题"}.get(problems[key]['problemType'], "其它题型")
                        reply_text += f"\nPPT: 第{key}页 {problemType} {fmt_num(problems[key].get('score', 0) * 100.0)}分"
                        problemId = problemsIdList[key - 1]
                        results[problemId]['problemType'] = problems[key]['problemType']
                        answer = reply['best_answer'].get(key, [])
                        llm_answer = None
                        if answer:
                            if results[problemId]['problemType'] == 1:  # 单选题
                                llm_answer = answer
                            elif results[problemId]['problemType'] == 2:  # 多选题
                                llm_answer = answer
                            elif results[problemId]['problemType'] == 3:  # 投票题
                                llm_answer = answer
                            elif results[problemId]['problemType'] == 4:  # 填空题
                                llm_answer = {str(i + 1): answer[i] for i in range(len(answer))}
                            elif results[problemId]['problemType'] == 5:  # 主观题
                                llm_answer = {
                                    "content": f"<div class=\"custom_ueditor_cn_body\"><p>{answer[0]}</p></div>",
                                    "attachments": {"filelist": []}
                                }
                            elif results[problemId]['problemType'] == 6:  # 判断题
                                llm_answer = answer
                            reply_text += f"\n最佳答案: {reply['best_answer'][key]}\n所有答案:"
                            for r in reply["result"]:
                                if r["answer_dict"].get(key):
                                    reply_text += f"\n[{r['score']}, {r['usedTime']}] {r['name']}: {r['answer_dict'][key]}"
                        else:
                            reply_text += f"\n无答案"
                        results[problemId]['llm_answer'] = llm_answer
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"试卷编号: {examId}\n消息: {reply_text}")

            if examId in self.examIdDict:
                self.examIdDict[examId]['problems'] = results
                if self.examConfig['an']: await self.answer_exam(examId)
                self.examIdDict[examId]['paper_status'] = True

    async def get_cache_answer(self, examId):
        if examId not in self.examIdDict: return {}
        await self.login_xuetangx(examId)
        url = f"https://examination.xuetangx.com/exam_room/cache_results?exam_id={examId}"
        headers = {
            "referer": f"https://examination.xuetangx.com/exam/{examId}?isFrom=2",
            "User-Agent": self.ua,
            "cookie": self.examIdDict[examId]['cookie']
        }
        try:
            r = requests.get(url, headers=headers, timeout=timeout).json()
            if r.get('errcode', -1) != 0:
                return {}
            results = r['data']['results']
            problemsIdList = [int(result['problem_id']) for result in results]
            problemsIdList.sort()
            answer = {pid: {} for pid in problemsIdList}
            for result in results:
                if not result.get('result', None): continue
                problemId = result['problem_id']
                answer[problemId] = result['result']
            return answer
        except:
            return {}

    async def answer_exam(self, examId):
        async with _get_fetch_lock(self.idx, 6):  # 同一用户串行, 跨用户并行
            if self.examIdDict.get(examId, {}).get('problems', {}) == {}: return
            await self.login_xuetangx(examId)
            url = 'https://examination.xuetangx.com/exam_room/answer_problem'
            headers = {
                "referer": f"https://examination.xuetangx.com/exam/{examId}?isFrom=2",
                "User-Agent": self.ua,
                "cookie": self.examIdDict[examId]['cookie']
            }
            data = {
                "exam_id": examId,
                "record": [],
                "results": []
            }
            submitted_answer = {}
            for problemId, ans in self.examIdDict[examId]['problems'].items():
                answer = ans.get('master_answer', []) or ans.get('llm_answer', [])
                if not answer: continue
                submitted_answer[problemId] = answer
                data['results'].append({
                    "problem_id": problemId,
                    "result": answer,
                    "time": int(time.time() * 1000) - randint(1000, 20000)
                })
            res = None
            try:
                retries = 3
                while retries > 0:
                    res = await asyncio.to_thread(requests.post, url, headers=headers, json=data, timeout=timeout)
                    if res.json().get('errcode') != 0:
                        retries -= 1
                        await asyncio.sleep(1)
                    else:
                        for problemId, ans in submitted_answer.items():
                            self.examIdDict[examId]['problems'][problemId]['submitted_answer'] = ans
                        break
            except:
                pass

    async def fetch_presentation(self, lessonId, ppt_id):
        async with _get_fetch_lock(lessonId, 1):  # 同一 lessonId 串行, 跨 lessonId 并行
            await asyncio.sleep(5)
            if self.lessonIdDict.get(lessonId, {}).get('presentation', 0) != ppt_id: return
            if self.lessonIdDict[lessonId].get('presentation_status', False): return
            lesson = self.lessonIdDict[lessonId].copy()
            folder = os.path.join(file_dir, self.domain, "lesson", ppt_id)
            if os.path.exists(os.path.join(folder, "ppt.json")):
                with open(os.path.join(folder, "ppt.json"), "r", encoding="utf-8") as f:
                    info = json.load(f)
            else:
                url = f"https://{self.domain}/api/v3/lesson/presentation/fetch?presentation_id={ppt_id}"
                headers = {
                    "referer": f"https://{self.domain}/lesson/fullscreen/v3/{lessonId}?source=5",
                    "User-Agent": self.ua,
                    "cookie": self.cookie,
                    "Authorization": lesson['Authorization']
                }
                res = await asyncio.to_thread(requests.get, url, headers=headers, timeout=timeout)
                self.set_authorization(res, lessonId)
                info = res.json()

            slides = info['data']['slides']
            problems = {}
            lesson['problems'] = {}
            lesson['covers'] = [slide['index'] for slide in slides if slide.get('cover') is not None]
            for slide in slides:
                if slide.get("problem") is not None:
                    lesson['problems'][slide['id']] = slide['problem']
                    lesson['problems'][slide['id']]['index'] = slide['index']
                    problems[slide['index']] = {"problemType": int(slide['problem']['problemType']), "option_keys": [opt['key'] for opt in slide['problem'].get('options', [])], "option_values": [opt['value'] for opt in slide['problem'].get('options', [])], "num_blanks": len(slide['problem'].get('blanks', [])), "pollingCount": int(slide['problem'].get('pollingCount', 1)), "score": float(slide['problem'].get('score', 0))}
                    if slide['problem']['body'] == '':
                        shapes = slide.get('shapes', [])
                        if shapes:
                            min_left_item = min(shapes, key=lambda item: item.get('Left', 9999999))
                            left_val = min_left_item.get('Left', 9999999)
                            if left_val != 9999999 and min_left_item.get('Text') is not None:
                                lesson['problems'][slide['id']]['body'] = min_left_item['Text'] or '未知问题'
                            else:
                                lesson['problems'][slide['id']]['body'] = '未知问题'
                        else:
                            lesson['problems'][slide['id']]['body'] = '未知问题'
                    problems[slide['index']]['body'] = lesson['problems'][slide['id']]['body'] if lesson['problems'][slide['id']]['body'] != '未知问题' else ''
            await asyncio.to_thread(self.msgmgr.sendMsg, f"{lesson['header']}\n{format_json_to_text(lesson['problems'], lesson.get('unlockedproblem', []))}")
            if self.lessonIdDict.get(lessonId, {}).get('presentation', 0) != ppt_id: return
            self.lessonIdDict[lessonId]['problems'] = lesson['problems']
            self.lessonIdDict[lessonId]['covers'] = lesson['covers']

        async with _get_fetch_lock(lessonId, 2):  # 同一 lessonId 串行, 跨 lessonId 并行
            if self.lessonIdDict.get(lessonId, {}).get('presentation', 0) != ppt_id: return
            if self.lessonIdDict[lessonId].get('presentation_status', False): return
            output_pdf_path = os.path.join(folder, sanitize_filename(lesson['classroomName'].strip() + "-" + lesson['title'].strip()) + ".pdf")
            if not os.path.exists(folder) or not os.path.exists(output_pdf_path):
                await asyncio.to_thread(clear_folder, folder)
                with open(os.path.join(folder, "ppt.json"), "w", encoding="utf-8") as f:
                    json.dump(info, f, ensure_ascii=False, indent=4)
                await asyncio.to_thread(download_images_to_folder, slides, folder)
                await asyncio.to_thread(images_to_pdf, folder, output_pdf_path)

            if self.lessonConfig['ppt']:
                if os.path.exists(output_pdf_path):
                    try:
                        await asyncio.to_thread(self.msgmgr.sendFile, output_pdf_path)
                    except:
                        await asyncio.to_thread(self.msgmgr.sendMsg, f"{lesson['header']}\n消息: PPT推送失败")
                else:
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"{lesson['header']}\n消息: 没有PPT")

            problems_keys = [int(k) for k in problems.keys()]
            if not os.path.exists(os.path.join(folder, "problems.txt")):
                if problems:
                    await asyncio.to_thread(concat_vertical_cv, folder, 0, 100, [], True)
                    await asyncio.to_thread(concat_vertical_cv, folder, 1, 100, [], True)
                    await asyncio.to_thread(concat_vertical_cv, folder, 2, 100, [], True)
                    await asyncio.to_thread(concat_vertical_cv, folder, 3, 100, problems_keys, True)
                    await asyncio.to_thread(concat_vertical_cv, folder, 4, 100, [], True)
                with open(os.path.join(folder, "problems.txt"), "w", encoding="utf-8") as f:
                    f.write(str(problems))

            reply = None
            if problems:
                if os.path.exists(os.path.join(folder, "reply.txt")):
                    with open(os.path.join(folder, "reply.txt"), "r", encoding="utf-8") as f:
                        reply = ast.literal_eval(f.read().strip())
                elif self.lessonConfig['llm']:
                    reply = await asyncio.to_thread(LLMManager().generateAnswer, folder)
                    if reply.get('best_answer', {}):
                        with open(os.path.join(folder, "reply.txt"), "w", encoding="utf-8") as f:
                            f.write(str(reply))
                    else:
                        reply = None
                if reply is not None:
                    reply_text = "LLM答案列表:"
                    for key in problems_keys:
                        reply_text += "\n" + "-"*20
                        problemType = {1: "单选题", 2: "多选题", 3: "投票题", 4: "填空题", 5: "主观题", 6: "判断题"}.get(problems[key]['problemType'], "其它题型")
                        reply_text += f"\nPPT: 第{key}页 {problemType} {fmt_num(problems[key].get('score', 0))}分"
                        if reply['best_answer'].get(key):
                            if self.lessonIdDict.get(lessonId, {}).get('presentation', 0) == ppt_id:
                                problemId = next((pid for pid, prob in lesson['problems'].items() if prob.get('index') == key), None)
                                self.lessonIdDict[lessonId]['problems'][problemId]['llm_answer'] = reply['best_answer'][key]
                            reply_text += f"\n最佳答案: {reply['best_answer'][key]}\n所有答案:"
                            for r in reply["result"]:
                                if r["answer_dict"].get(key):
                                    reply_text += f"\n[{r['score']}, {r['usedTime']}] {r['name']}: {r['answer_dict'][key]}"
                        else:
                            reply_text += f"\n无答案"
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"{lesson['header']}\n消息: {reply_text}")

            if self.lessonIdDict.get(lessonId, {}).get('presentation', 0) == ppt_id: self.lessonIdDict[lessonId]['presentation_status'] = True

    def answer_lesson(self, lessonId):
        url = f"https://{self.domain}/api/v3/lesson/problem/answer"
        headers = {
            "referer": f"https://{self.domain}/lesson/fullscreen/v3/{lessonId}?source=5",
            "User-Agent": self.ua,
            "cookie": self.cookie,
            "Content-Type": "application/json",
            "Authorization": self.lessonIdDict[lessonId]['Authorization']
        }
        llm_answer = self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']].get('llm_answer')
        tp = self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['problemType']
        problemType = {1: "单选题", 2: "多选题", 3: "投票题", 4: "填空题", 5: "主观题", 6: "判断题"}.get(tp, "其它题型")
        if llm_answer:
            answer = llm_answer
        else:
            if tp == 1: # 单选题
                answer = [self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options'][0]['key']]
            elif tp == 2: # 多选题
                answer = [self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options'][0]['key']]
            elif tp == 3: # 投票题
                answer = [self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options'][0]['key']]
            elif tp == 4: # 填空题
                answer = [''] * len(self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['blanks'])
            elif tp == 5: # 主观题
                answer = ['']
            elif tp == 6: # 判断题
                answer = [self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options'][0]['key']]
            else: # 其它题型
                answer = ['']
        data = {
            "dt": int(time.time() * 1000) - randint(1, 1000),
            "problemId": self.lessonIdDict[lessonId]['problemId'],
            "problemType": tp,
            "result": answer if tp != 5 else {"content": answer[0], "pics": [{"pic": "", "thumb": ""}]}
        }
        res = None
        try:
            retries = 3
            while retries > 0:
                res = requests.post(url=url, headers=headers, json=data, timeout=timeout)
                if res.json().get('msg') != 'OK':
                    retries -= 1
                    time.sleep(1)
                else:
                    break
        except:
            pass
        if res is not None:
            self.set_authorization(res, lessonId)
        self.msgmgr.sendMsg(f"{self.lessonIdDict[lessonId]['header']}\nPPT: 第{self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['index']}页 {problemType} {fmt_num(self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']].get('score', 0))}分\n问题: {self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['body']}\n提交答案: {answer}")

    async def ws_controller(self, func, *args, retries=3, delay=10):
        attempt = 0
        while attempt <= retries:
            try:
                await func(*args)
                return  # 如果成功就直接返回
            except:
                attempt += 1
                if attempt <= retries:
                    await asyncio.sleep(delay)
                    print(f"重试 ({attempt}/{retries})")

    async def ws_login(self):
        uri = f"wss://{self.domain}/wsapp/"
        async with websockets.connect(uri, ping_timeout=100, ping_interval=5) as websocket:
            # 发送 "hello" 消息以建立连接
            hello_message = {
                "op": "requestlogin",
                "role": "web",
                "version": 1.4,
                "type": "qrcode",
                "from": "web"
            }
            await websocket.send(json.dumps(hello_message))
            server_response = await recv_json(websocket)
            qrcode_url = server_response['ticket']
            download_qrcode(qrcode_url, self.name)
            await asyncio.to_thread(self.msgmgr.sendImage, os.path.join(qr_dir, f"qrcode_{sanitize_filename(self.name)}.jpg"))
            server_response = await asyncio.wait_for(recv_json(websocket), timeout=60)
            self.login_yuketang(server_response['UserID'], server_response['Auth'])

    async def ws_lesson(self, lessonId):
        flag_ppt = 1
        flag_si = 1
        fetch_task = None
        def del_dict():
            nonlocal flag_ppt, flag_si, fetch_task
            flag_ppt = 1
            flag_si = 1
            fetch_task = None
            keys_to_remove = ['presentation', 'presentation_status', 'si', 'unlockedproblem', 'covers', 'problems', 'problemId']
            for key in keys_to_remove:
                if self.lessonIdDict[lessonId].get(key) is not None:
                    del self.lessonIdDict[lessonId][key]
        del_dict()
        uri = f"wss://{self.domain}/wsapp/"
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
            while True and time.time() - self.lessonIdDict[lessonId]['startTime'] < 36000:
                try:
                    server_response = await recv_json(websocket)
                except:
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n消息: 连接断开")
                    break
                op = server_response['op']
                if op in ["hello", "fetchtimeline"]:
                    reversed_timeline = list(reversed(server_response['timeline']))
                    for item in reversed_timeline:
                        if 'pres' in item:
                            if flag_ppt == 0 and self.lessonIdDict[lessonId]['presentation'] != item['pres']:
                                del_dict()
                                await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                            self.lessonIdDict[lessonId]['presentation'] = item['pres']
                            self.lessonIdDict[lessonId]['header'] = re.sub(r'PPT编号: .*?\n', f"PPT编号: {self.lessonIdDict[lessonId]['presentation']}\n", self.lessonIdDict[lessonId]['header'])
                            self.lessonIdDict[lessonId]['si'] = item['si']
                            break
                    if server_response.get('presentation'):
                        if flag_ppt == 0 and self.lessonIdDict[lessonId]['presentation'] != server_response['presentation']:
                            del_dict()
                            await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                        self.lessonIdDict[lessonId]['presentation'] = server_response['presentation']
                        self.lessonIdDict[lessonId]['header'] = re.sub(r'PPT编号: .*?\n', f"PPT编号: {self.lessonIdDict[lessonId]['presentation']}\n", self.lessonIdDict[lessonId]['header'])
                    if server_response.get('slideindex'):
                        self.lessonIdDict[lessonId]['si'] = server_response['slideindex']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem'] = server_response['unlockedproblem']
                elif op in ["showpresentation", "presentationupdated", "presentationcreated", "showfinished"]:
                    if server_response.get('presentation'):
                        if flag_ppt == 0 and self.lessonIdDict[lessonId]['presentation'] != server_response['presentation']:
                            del_dict()
                            await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                        self.lessonIdDict[lessonId]['presentation'] = server_response['presentation']
                        self.lessonIdDict[lessonId]['header'] = re.sub(r'PPT编号: .*?\n', f"PPT编号: {self.lessonIdDict[lessonId]['presentation']}\n", self.lessonIdDict[lessonId]['header'])
                    if server_response.get('slideindex'):
                        self.lessonIdDict[lessonId]['si'] = server_response['slideindex']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem'] = server_response['unlockedproblem']
                elif op in ["slidenav"]:
                    if server_response['slide'].get('pres'):
                        if flag_ppt == 0 and self.lessonIdDict[lessonId]['presentation'] != server_response['slide']['pres']:
                            del_dict()
                            await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                        self.lessonIdDict[lessonId]['presentation'] = server_response['slide']['pres']
                        self.lessonIdDict[lessonId]['header'] = re.sub(r'PPT编号: .*?\n', f"PPT编号: {self.lessonIdDict[lessonId]['presentation']}\n", self.lessonIdDict[lessonId]['header'])
                    if server_response['slide'].get('si'):
                        self.lessonIdDict[lessonId]['si'] = server_response['slide']['si']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem'] = server_response['unlockedproblem']
                elif op in ["unlockproblem", "extendtime"]:
                    if server_response['problem'].get('pres'):
                        if flag_ppt == 0 and self.lessonIdDict[lessonId]['presentation'] != server_response['problem']['pres']:
                            del_dict()
                            await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n消息: 课件更新")
                        self.lessonIdDict[lessonId]['presentation'] = server_response['problem']['pres']
                        self.lessonIdDict[lessonId]['header'] = re.sub(r'PPT编号: .*?\n', f"PPT编号: {self.lessonIdDict[lessonId]['presentation']}\n", self.lessonIdDict[lessonId]['header'])
                    if server_response['problem'].get('si'):
                        self.lessonIdDict[lessonId]['si'] = server_response['problem']['si']
                    if server_response.get('unlockedproblem'):
                        self.lessonIdDict[lessonId]['unlockedproblem'] = server_response['unlockedproblem']
                    self.lessonIdDict[lessonId]['problemId'] = server_response['problem']['prob']
                    problemType = {1: "单选题", 2: "多选题", 3: "投票题", 4: "填空题", 5: "主观题", 6: "判断题"}.get(self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['problemType'], "其它题型")
                    text_result = f"PPT: 第{self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['index']}页 {problemType} {fmt_num(self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']].get('score', 0))}分\n问题: {self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['body']}"
                    answer = self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']].get('llm_answer', [])
                    if 'options' in self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]:
                        for option in self.lessonIdDict[lessonId]['problems'][self.lessonIdDict[lessonId]['problemId']]['options']:
                            text_result += f"\n- {option['key']}: {option['value']}"
                    if answer not in [[], None, 'null']:
                        answer_text = ', '.join(answer)
                        text_result += f"\n答案: {answer_text}"
                    else:
                        text_result += "\n答案: 暂无"
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n解锁问题:\n{text_result}")
                    if self.lessonConfig['an']:
                        await asyncio.sleep(randint(5, 10))
                        await asyncio.to_thread(self.answer_lesson, lessonId)
                elif op in ["lessonfinished"]:
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n消息: 下课了")
                    break
                if self.lessonIdDict[lessonId].get('presentation') is not None:
                    flag_ppt = 0
                    if not self.lessonIdDict[lessonId].get('presentation_status', False) and (fetch_task is None or fetch_task.done()):
                        fetch_task = asyncio.create_task(self.fetch_presentation(lessonId, self.lessonIdDict[lessonId]['presentation']))
                if flag_si == 1 and self.lessonIdDict[lessonId].get('si') is not None and self.lessonIdDict[lessonId].get('covers') is not None and self.lessonIdDict[lessonId]['si'] in self.lessonIdDict[lessonId]['covers']:
                    await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n消息: 正在播放PPT第{self.lessonIdDict[lessonId]['si']}页")
                    if self.lessonConfig['si']:
                        del self.lessonIdDict[lessonId]['si']
                    else:
                        flag_si = 0
            await asyncio.to_thread(self.msgmgr.sendMsg, f"{self.lessonIdDict[lessonId]['header']}\n消息: 连接关闭")
            del self.lessonIdDict[lessonId]

    async def attend_lesson(self):
        if not self.lessonIdNewList: return
        coros = [self.ws_lesson(lessonId) for lessonId in self.lessonIdNewList]
        self.lessonIdNewList = []
        results = await asyncio.gather(*coros, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                print(f"ws_lesson 任务异常: {r}")

    async def attend_exam(self):
        if not self.examIdNewList: return
        coros = [self.fetch_paper(examId) for examId in self.examIdNewList]
        self.examIdNewList = []
        await asyncio.gather(*coros, return_exceptions=True)

async def _handle_ykt_one(ykt):
    await ykt.get_cookie()
    await asyncio.to_thread(ykt.join_classroom)
    got, to_close_ids = await asyncio.to_thread(ykt.get_lesson)
    if got:
        await asyncio.to_thread(ykt.checkin_lesson)

    for lessonId in to_close_ids:
        ws = ykt.lessonIdDict.get(lessonId, {}).get('websocket')
        if ws is not None:
            try:
                await ws.close()
            except Exception as e:
                print(f"关闭 websocket 失败: {e}")
        ykt.lessonIdDict.pop(lessonId, None)

    asyncio.create_task(ykt.attend_lesson())

    courseList = await asyncio.to_thread(ykt.get_course_list)
    to_close_ids = await ykt.get_exam(courseList)
    for examId in to_close_ids:
        ykt.examIdDict.pop(examId, None)
    asyncio.create_task(ykt.attend_exam())

async def ykt_users():
    ykts = [yuketang(user, idx) for idx, user in enumerate(users) if user.get('enabled', False)]
    global exam_answer_cache
    exam_answer_cache = {ykt.idx: {} for ykt in ykts}
    while True:
        await asyncio.gather(*(_handle_ykt_one(ykt) for ykt in ykts), return_exceptions=True)
        await asyncio.sleep(30)
