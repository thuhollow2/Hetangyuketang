安装 Termux：
--
Termux 是一个面向 Android 的开源终端仿真器和 Linux 环境应用。它通过应用包管理系统提供了一系列 Unix 软件包，可以直接在 Android 设备上运行，详细介绍及安装方法移步[官网](https://termux.dev/cn/index.html)，使用需要一定 Linux 基础

使用 Termux：
--

启动 Termux ，进入命令行界面，为获取系统文件权限，输入
```shell
termux-setup-storage
```
为查看当前目录，输入
```shell
pwd
```
每次启动后当前目录默认为 `/data/data/com.termux/files/home/` ,未获取 root 权限时文件管理器无法访问该目录。如未 root ，之后在此目录下运行程序请提前修改 `yuketang.py` 和 `send.py` 以启用推送（熟悉程序后推荐使用，具体见后续 **运行** 及 **说明** ）查看登录二维码，否则应使用`cp`工具将文件从 `/data/data/com.termux/files/home/` 传输到 `/storage/emulated/0/` （手机内部存储**根目录**，可用文件管理器直接访问）

也可切换当前目录到内部存储，即输入
```shell
cd /storage/emulated/0
```
此时可直接在文件管理器中查看并修改文件，推荐小白使用

### 安装项目及依赖：
```shell
pkg update
pkg upgrade
pkg install python git
git clone --branch termux https://github.com/thuhollow2/Hetangyuketang.git # 如需提前修改以启用推送，请自行fork
pip install -r Hetangyuketang/requirements.txt 
```
 - termux 安装 Pillow 易失败，已移除终端**显示登录二维码**功能


运行：
--
```shell
python Hetangyuketang/main.py
```

### 部分参数：
*yuketang.py*
```shell
class yuketang:
    def __init__(self) -> None:
        ...
        self.classroomWhiteList = [] # 课程白名单，名字采用完全匹配，为空时不启用
        self.clashroomBlackList = ['2023秋-机器学习-0', '2023清华实践'] # 课程黑名单，名字采用完全匹配，为空时不启用
        self.clashroomStartTimeDict = {'2023秋-机器学习-0': {'1': '08:00', '2': '13:30'}, '2023清华实践': {'1': '13:30'}} # 课程签到开始时间，名字采用完全匹配，1-7代表周一-周日，当日时间值不为空且此时早于该值不签到，为空时不启用
        self.wx=False # 设置为True时启用企业微信推送，须在send.py设置CompanyId、AgentId、Secret
        self.dd=False # 设置为True时启用钉钉推送，须在send.py设置Appkey、Appsecret、RobotCode、OpenConversationId
        self.fs=False # 设置为True时启用飞书推送，须在send.py设置AppId、AppSecret、OpenId
        self.an=False # 设置为True时自动答题
        self.ppt=False # 设置为True时自动下载PPT
        self.si=False # 设置为True时实时推送PPT进度
        ...
```

说明：
--
 - 首次运行将下载雨课堂登录二维码（可推送到客户端），微信扫码获取cookie，有效期约两周；有效期少于两天时，每小时初将发送二维码提醒，请及时扫码更新，谨防失效后消息轰炸<br>
 - 支持多线程，每30秒扫描新课堂，随后自动签到、下载课件（pdf）、打印题目及答案、查看当前PPT进度<br>
 - 白/黑名单添加课程名称，可在[雨课堂首页](https://pro.yuketang.cn/v2/web/index)课程标签里查找，具体如[图](classroomName.png)中蓝框所示
 - 签到方式为通过“正在上课”提示进入课堂<br>
 - 自动答题支持选择题（单选和多选）和填空题；若选择题未查到答案，将以第一个选项提交（自定义可修改[此处](yuketang.py#L319-L320)），主观题未测试（可能报错）<br>
 - 启用企业微信推送需[注册企业](https://work.weixin.qq.com/wework_admin/register_wx?from=myhome)、[创建应用](https://work.weixin.qq.com/wework_admin/frame#apps/createApiApp)、[**配置企业可信IP**](https://work.weixin.qq.com/wework_admin/frame#apps)<br>
 - 启用钉钉推送需[注册钉钉开发者账号](https://open-dev.dingtalk.com/)、[创建并发布企业内部应用（应用内创建机器人）](https://open-dev.dingtalk.com/fe/app#/corp/app)、[获取群会话OpenConversationId](https://open.dingtalk.com/document/isvapp/get-the-openconversationid-of-the-group-session)、机器人添加进群
 - 启用飞书推送需[注册飞书开发者账号、创建并发布企业内部应用](https://open.feishu.cn/app?lang=zh-CN)、[开启机器人能力](https://open.feishu.cn/document/faq/trouble-shooting/how-to-enable-bot-ability)、[获取OpenId](https://open.feishu.cn/document/server-docs/im-v1/message/create)、开通权限（[*以应用的身份发消息*](https://open.feishu.cn/document/server-docs/im-v1/message/create)，[*获取与上传图片或文件资源*](https://open.feishu.cn/document/server-docs/im-v1/file/create)）
 - 单次推送有大小限制，超过将分块传输，默认设置：<br>
 
    | 推送方式 | 消息限制 | 文件限制 |
    | -------- | -------- | -------- |
    | 企业微信 | 500字符 | 20MB |
    | 钉钉 | 3000字符 | 20MB |
    | 飞书 | 10000字符 | 30MB |

 - 尚有许多不足<br>
 - 项目修改自[timeflykai/lazytool](https://github.com/timeflykai/lazytool/tree/main)
