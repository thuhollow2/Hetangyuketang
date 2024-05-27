安装依赖：
--
```shell
pip install -r requirements.txt 
```
pyzbar为二维码识别库，部分linux安装不全，需用软件包管理工具安装zbar相关依赖；始终失败请注释[1](https://github.com/thuhollow2/Hetangyuketang/blob/main/util.py#L8)和[2](https://github.com/thuhollow2/Hetangyuketang/blob/main/util.py#L29-L35)

运行：
--
```shell
python main.py
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
 - 白/黑名单添加课程名称，可在[雨课堂首页](https://pro.yuketang.cn/v2/web/index)课程标签里查找，具体如[图](https://raw.githubusercontent.com/thuhollow2/Hetangyuketang/main/classroomName.png)中蓝框所示
 - 签到方式为通过“正在上课”提示进入课堂<br>
 - 自动答题支持选择题（单选和多选）和填空题；若选择题未查到答案，将以第一个选项提交（自定义可修改[此处](https://github.com/thuhollow2/Hetangyuketang/blob/main/yuketang.py#L319-L320)），主观题未测试（可能报错）<br>
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
