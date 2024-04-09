安装依赖：
--
```shell
pip install -r requirements.txt 
```

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
        self.wx=False # 设置为True时启用企业微信推送，须在send.py设置CompanyId、AgentId、Secret
        self.dd=False # 设置为True时启用钉钉推送，须在send.py设置Appkey、Appsecret、RobotCode、OpenConversationId
        self.an=False # 设置为True时自动答题
        self.si=False # 设置为True时实时推送PPT进度
        ...
```

说明：
--
 - 首次运行将下载雨课堂登录二维码（可推送到客户端），扫码获取cookie，有效期约两周<br>
 - 支持多线程，每30秒扫描新课堂，随后自动签到、下载课件（pdf）、打印题目及答案、查看当前PPT进度<br>
 - 签到方式为通过“正在上课”提示进入课堂<br>
 - 自动答题支持选择题（单选和多选）和填空题；若选择题未查到答案，将以第一个选项提交（自定义可修改[此处](https://github.com/thuhollow2/Hetangyuketang/blob/main/yuketang.py#L271-L272)），主观题未测试可能报错<br>
 - 启用企业微信推送需[注册企业](https://work.weixin.qq.com/wework_admin/register_wx?from=myhome)、[创建应用](https://work.weixin.qq.com/wework_admin/frame#apps/createApiApp)、[配置企业可信IP](https://work.weixin.qq.com/wework_admin/frame#apps)<br>
 - 启用钉钉推送需[注册钉钉开发者账号](https://open-dev.dingtalk.com/)、[创建并发布企业内部应用（应用内创建机器人）](https://open-dev.dingtalk.com/fe/app#/corp/app)、[获取群会话OpenConversationId](https://open.dingtalk.com/document/isvapp/get-the-openconversationid-of-the-group-session)
 - 单次推送有大小限制，推送可能将分块传输，默认限制单个pdf文件20MB、企业微信单次消息500字符、钉钉单次消息3000字符<br>
 - 尚有许多不足<br>
 - 项目修改自[timeflykai/lazytool](https://github.com/timeflykai/lazytool/tree/main)
