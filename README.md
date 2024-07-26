安装 iSH Shell：
--
iSH Shell 是一款运行在 iOS 系统上的 App，可以运行 Linux Shell，底层操作系统基于 Alpine Linux。它提供标准的 Linux 命令行接口，使用 apk 包管理器安装和管理软件包，无需越狱，可从 [App Store](https://apps.apple.com/cn/app/ish-shell/id1436902243) 下载，使用需要一定 Linux 基础

使用 iSH Shell：
--

启动 iSH，进入命令行界面，输入
```shell
pwd
```
查看当前目录，每次启动当前目录默认为 `/root` ，可在 **文件** > **浏览** > **iSH** > **root 文件夹** 访问，之后运行程序可在此查看登录二维码，或者修改 `config.json` 以启用推送（熟悉程序后推荐使用，具体见后续 **运行** 及 **说明** ）

### 安装项目及依赖
```shell
apk update
apk upgrade
apk add python3 py3-pip git
git clone --branch ish https://github.com/thuhollow2/Hetangyuketang.git # 如需提前修改以启用推送，请自行fork
pip install -r Hetangyuketang/requirements.txt 
```
 - 已移除终端**显示登录二维码**功能


运行：
--
```shell
python3 Hetangyuketang/main.py
```

### 配置文件
*config.json*
```shell
{
  "yuketang": {
    "domain": "pro.yuketang.cn",
    "classroomWhiteList": [],
    "clashroomBlackList": ["2023秋-机器学习-0", "2023清华实践"],
    "clashroomStartTimeDict": {
      "2023秋-机器学习-0": {"1": "08:00", "2": "13:30"},
      "2023清华实践": {"1": "13:30"}
    },
    "wx": false,
    "dd": false,
    "fs": false,
    "an": false,
    "ppt": false,
    "si": false,
    "timeout": 30
  },
  "send": {
    "wx": {
      "touser": "@all",
      "agentId": "####",
      "secret": "####",
      "companyId": "####",
      "msgLimit": 500,
      "dataLimit": 20971520
    },
    "dd": {
      "appKey": "####",
      "appSecret": "####",
      "robotCode": "####",
      "openConversationId": "####",
      "msgLimit": 3000,
      "dataLimit": 20971520
    },
    "fs": {
      "appId": "####",
      "appSecret": "####",
      "openId": "####",
      "msgLimit": 10000,
      "dataLimit": 31457280
    },
    "timeout": 30
  },
  "util": {
    "threads": 20,
    "timezone": "Asia/Shanghai",
    "timeout": 30
  }
}
```

说明：
--
 - 首次运行将下载雨课堂登录二维码（可推送到客户端），微信扫码获取 cookie，有效期约两周；有效期少于两天时，每小时初将发送二维码提醒，请及时扫码更新，谨防失效后消息轰炸<br>
 - 支持多线程监听，每 30 秒扫描新课堂，随后自动签到、下载课件（pdf）、打印题目及答案、查看当前 PPT 进度<br>
 - 签到方式为通过“正在上课”提示进入课堂<br>
 - 自动答题支持选择题（单选和多选）和填空题；若选择题未查到答案，将以第一个选项提交（自定义可修改[此处](yuketang.py#L322-L323)），主观题未测试（可能报错）<br>

### 配置文件
 - 默认设置雨课堂域名为 `pro.yuketang.cn`<br>
 - `classroomWhiteList`/`clashroomBlackList`/`clashroomStartTimeDict` 等使用的课程名，可在[雨课堂首页](https://pro.yuketang.cn/v2/web/index)课程标签里查找，具体如[图](classroomName.png)中蓝框所示，采用完全匹配，为空时不启用<br>
 - `clashroomStartTimeDict` 中，1-7 代表周一-周日，当日时间值不为空且此时早于该值不签到，数字或时间为空不启用<br>
 - `yuketang` 中，`an` 设置为 `true` 时自动答题，`ppt` 设置为 `true` 时自动下载 PPT，`si` 设置为 `true` 时实时推送 PPT 进度<br>
 - 启用企业微信推送需[注册企业](https://work.weixin.qq.com/wework_admin/register_wx?from=myhome)、[创建应用](https://work.weixin.qq.com/wework_admin/frame#apps/createApiApp)、[**配置企业可信IP**](https://work.weixin.qq.com/wework_admin/frame#apps)，并设置 `yuketang` 的 `wx` 为 `true`，并在 `send` 中填充 `wx` 的 `agentId`、`secret`、`companyId`，默认设置 `touser` 为企业全体成员<br>
 - 启用钉钉推送需[注册钉钉开发者账号](https://open-dev.dingtalk.com/)、[创建并发布企业内部应用（应用内创建机器人）](https://open-dev.dingtalk.com/fe/app#/corp/app)、[获取群会话OpenConversationId](https://open.dingtalk.com/document/isvapp/get-the-openconversationid-of-the-group-session)、机器人添加进群，并设置 `yuketang` 的 `dd` 为 `true`，并在 `send` 中填充 `dd` 的 `appKey`、`appSecret`、`robotCode`、`openConversationId`<br>
 - 启用飞书推送需[注册飞书开发者账号、创建并发布企业内部应用](https://open.feishu.cn/app?lang=zh-CN)、[开启机器人能力](https://open.feishu.cn/document/faq/trouble-shooting/how-to-enable-bot-ability)、[获取OpenId](https://open.feishu.cn/document/server-docs/im-v1/message/create)、开通权限（[*以应用的身份发消息*](https://open.feishu.cn/document/server-docs/im-v1/message/create)，[*获取与上传图片或文件资源*](https://open.feishu.cn/document/server-docs/im-v1/file/create)），并设置 `yuketang` 的 `fs` 为 `true`，并在 `send` 中填充 `fs` 的 `appId`、`appSecret`、`openId`<br>
 - 单次推送有大小限制，超过将分块传输，默认设置 `send`：<br>
 
    | 推送方式 | 消息限制 (`msgLimit`) | 文件限制 (`dataLimit`) |
    | -------- | -------- | -------- |
    | 企业微信 (`wx`) | 500字符 (500) | 20MB (20971520) |
    | 钉钉 (`dd`) | 3000字符 (3000) | 20MB (20971520) |
    | 飞书 (`fs`) | 10000字符 (10000) | 30MB (31457280) |
 - `util` 中，`threads` 为 PPT 文件下载的线程数，`timezone` 选择时区<br>
 - `timeout` 为连接超时秒数<br>
### 声明
 - 项目尚有许多不足<br>
 - 修改自 [timeflykai/lazytool](https://github.com/timeflykai/lazytool/tree/main)<br>
