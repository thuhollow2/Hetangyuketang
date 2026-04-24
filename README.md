# 安装

<details>
<summary>Android（<a href="https://github.com/thuhollow2/yuketang/releases/latest">可直接安装软件“雨课堂助手”</a>）</summary>

## 安装 Termux

Termux 是一个面向 Android 的开源终端仿真器和 Linux 环境应用。它通过应用包管理系统提供了一系列 Unix 软件包，可以直接在 Android 设备上运行，详细介绍及安装方法移步[官网](https://termux.dev/cn/index.html)，使用需要一定 Linux 基础

## 使用 Termux

启动 Termux，进入命令行界面，为获取系统文件权限，输入
```shell
termux-setup-storage
```
为查看当前目录，输入
```shell
pwd
```
每次启动当前目录默认为 `/data/data/com.termux/files/home/`，未获取 root 权限时文件管理器无法访问该目录。如未 root，之后在此目录下运行程序请提前修改 `config.json`（熟悉程序后推荐使用，具体见后续 **运行** 及 **说明** ），否则应使用`cp`工具将文件从 `/data/data/com.termux/files/home/` 传输到 `/storage/emulated/0/`（手机内部存储**根目录**，可用文件管理器直接访问）

也可切换当前目录到内部存储，即输入
```shell
cd /storage/emulated/0
```
此时可直接在文件管理器中查看并修改文件，推荐小白使用

## 安装项目及依赖
```shell
pkg update
pkg upgrade -y
pkg install -y python git libjpeg-turbo python-pillow dbus zbar
git clone https://github.com/thuhollow2/yuketang.git # 如需提前修改文件，可先自行fork
cd yuketang
pip install -r requirements.txt
```

</details>

<details>
<summary><code>iOS</code></summary>

## 安装 iSH Shell

iSH Shell 是一款运行在 iOS 系统上的 App，可以运行 Linux Shell，底层操作系统基于 Alpine Linux。它提供标准的 Linux 命令行接口，使用 apk 包管理器安装和管理软件包，无需越狱，可从 [App Store](https://apps.apple.com/app/ish-shell/id1436902243) 下载，使用需要一定 Linux 基础

## 使用 iSH Shell

启动 iSH，进入命令行界面，输入
```shell
pwd
```
查看当前目录，每次启动当前目录默认为 `/root` ，可在 **文件** > **浏览** > **iSH** > **root 文件夹** 访问，之后运行程序可在此查看或修改文件

## 安装项目及依赖
```shell
apk update
apk upgrade
apk add python3 py3-pip git py3-pillow zbar
ln -sf /usr/bin/python3 /usr/bin/python
git clone https://github.com/thuhollow2/yuketang.git # 如需提前修改文件，可先自行fork
cd yuketang
pip install -r requirements.txt
```

</details>

<details>
<summary><code>Other</code></summary>

下载本项目后，切换到项目根目录，执行以下命令安装依赖

```shell
pip install -r requirements.txt
```
 - `pyzbar` 是对 **ZBar** 的 Python 封装，本身需要系统里有 **libzbar** 动态库；非 Windows 上必须先装 zbar 才能用，详情见 [pyzbar 安装说明](https://github.com/NaturalHistoryMuseum/pyzbar#installation)

</details>

---
# 运行

在项目根目录下，执行

```shell
python main.py
```

## 配置文件
<details>
<summary><code>config.json</code></summary>

```json
{
    "yuketang": {
        "users": [
            {
                "name": "user1",
                "enabled": false,
                "domain": "pro.yuketang.cn",
                "lesson": {
                    "classroomWhiteList": [],
                    "classroomBlackList": ["未央.机器学习", "未央.深度学习"],
                    "classroomStartTimeDict": {
                        "未央.机器学习": {"1": "08:00", "2": "13:30"},
                        "未央.深度学习": {"1": "13:30"}
                    },
                    "llm": false,
                    "an": false,
                    "ppt": false,
                    "si": false
                },
                "exam": {
                    "classroomWhiteList": ["未央.机器学习"],
                    "llm": false,
                    "an": false,
                    "paper": false,
                    "isMaster": false,
                    "isSlave": false,
                    "x_access_token": ""
                },
                "other": {
                    "classroomCodeList": ["94RGB"]
                },
                "services": ["dingtalk", "feishu"]
            },
            {
                "name": "user2",
                "enabled": false,
                "domain": "pro.yuketang.cn",
                "lesson": {
                    "classroomWhiteList": [],
                    "classroomBlackList": ["未央.机器学习", "未央.深度学习"],
                    "classroomStartTimeDict": {
                        "未央.机器学习": {"1": "08:00", "2": "13:30"},
                        "未央.深度学习": {"1": "13:30"}
                    },
                    "llm": false,
                    "an": false,
                    "ppt": false,
                    "si": false
                },
                "exam": {
                    "classroomWhiteList": ["未央.机器学习"],
                    "llm": false,
                    "an": false,
                    "paper": false,
                    "isMaster": false,
                    "isSlave": false,
                    "x_access_token": ""
                },
                "other": {
                    "classroomCodeList": ["94RGB"]
                },
                "services": ["dingtalk", "feishu"]
            }
        ],
        "timeout": 30
    },
    "send": {
        "services": [
            {
                "name": "wechat",
                "enabled": false,
                "type": "wechat",
                "touser": "@all",
                "agentId": "####",
                "secret": "####",
                "companyId": "####",
                "msgLimit": 500,
                "dataLimit": 20971520
            },
            {
                "name": "dingtalk",
                "enabled": false,
                "type": "dingtalk",
                "appKey": "####",
                "appSecret": "####",
                "robotCode": "####",
                "openConversationId": "####",
                "msgLimit": 3000,
                "dataLimit": 20971520
            },
            {
                "name": "feishu",
                "enabled": false,
                "type": "feishu",
                "appId": "####",
                "appSecret": "####",
                "openId": "####",
                "msgLimit": 10000,
                "dataLimit": 31457280
            }
        ],
        "threads": 5,
        "timeout": 30
    },
    "llm": {
        "models": [
            {
                "name": "openai-gpt-5.4",
                "enabled": false,
                "type": "openai",
                "apiKey": "####",
                "model": "gpt-5.4",
                "prompt": "You are a helpful assistant.",
                "temperature": 1,
                "score": 100
            },
            {
                "name": "claude-opus-4-6",
                "enabled": false,
                "type": "claude",
                "apiKey": "####",
                "model": "claude-opus-4-6",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "grok-4.20-0309-reasoning",
                "enabled": false,
                "type": "grok",
                "apiKey": "####",
                "model": "grok-4.20-0309-reasoning",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "gemini-3-flash-preview",
                "enabled": false,
                "type": "gemini",
                "apiKey": "####",
                "model": "gemini-3-flash-preview",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "cloudflare-kimi-k2.5",
                "enabled": false,
                "type": "cloudflare",
                "accountId": "####",
                "apiToken": "####",
                "model": "@cf/moonshotai/kimi-k2.5",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "openrouter-gpt-oss-120b",
                "enabled": false,
                "type": "openrouter",
                "apiKey": "####",
                "model": "openai/gpt-oss-120b:free",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "poixe-gpt-5.2",
                "enabled": false,
                "type": "poixe",
                "apiKey": "####",
                "model": "gpt-5.2:free",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "siliconflow-Kimi-K2.5",
                "enabled": false,
                "type": "siliconflow",
                "apiKey": "####",
                "model": "Pro/moonshotai/Kimi-K2.5",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "infinigence-kimi-k2.5",
                "enabled": false,
                "type": "infinigence",
                "apiKey": "####",
                "model": "kimi-k2.5",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "zhipu-glm-5v-turbo",
                "enabled": false,
                "type": "zhipu",
                "apiKey": "####",
                "model": "glm-5v-turbo",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "dmxapi-glm-4.1v-9b-thinking",
                "enabled": false,
                "type": "dmxapi",
                "apiKey": "####",
                "model": "GLM-4.1V-9B-Thinking",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "modelscope-Kimi-K2.5",
                "enabled": false,
                "type": "modelscope",
                "accessToken": "####",
                "model": "moonshotai/Kimi-K2.5",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "moonshot-kimi-k2.5",
                "enabled": false,
                "type": "moonshot",
                "apiKey": "####",
                "model": "kimi-k2.5",
                "prompt": "You are a helpful assistant.",
                "temperature": 1,
                "score": 100
            },
            {
                "name": "volcengine-doubao-seed-2-0-pro-260215",
                "enabled": false,
                "type": "volcengine",
                "apiKey": "####",
                "model": "doubao-seed-2-0-pro-260215",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "poloapi-gemini-2.5-flash",
                "enabled": false,
                "type": "poloapi",
                "apiKey": "####",
                "model": "gemini-2.5-flash",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "bailian-qwen3.6-plus",
                "enabled": false,
                "type": "bailian",
                "apiKey": "####",
                "model": "qwen3.6-plus",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "qianfan-ernie-5.0-thinking-preview",
                "enabled": false,
                "type": "qianfan",
                "apiKey": "####",
                "model": "ernie-5.0-thinking-preview",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "xunfei-xop3qwen32bvl",
                "enabled": false,
                "type": "xunfei",
                "apiKey": "####",
                "model": "xop3qwen32bvl",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "minimax-MiniMax-M2.7",
                "enabled": false,
                "type": "minimax",
                "apiKey": "####",
                "model": "MiniMax-M2.7",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "sensecore-SenseNova-V6-Pro",
                "enabled": false,
                "type": "sensecore",
                "accessKeyId": "####",
                "accessKeySecret": "####",
                "model": "SenseNova-V6-Pro",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "mistral-mistral-small-latest",
                "enabled": false,
                "type": "mistral",
                "apiKey": "####",
                "model": "mistral-small-latest",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            },
            {
                "name": "tencent-kimi-k2.5",
                "enabled": false,
                "type": "tencent",
                "apiKey": "####",
                "model": "kimi-k2.5",
                "prompt": "You are a helpful assistant.",
                "temperature": 1,
                "score": 100
            },
            {
                "name": "cohere-command-a-vision-07-2025",
                "enabled": false,
                "type": "cohere",
                "apiKey": "####",
                "model": "command-a-vision-07-2025",
                "prompt": "You are a helpful assistant.",
                "temperature": 0.2,
                "score": 100
            }
        ],
        "threads": 5,
        "timeout": 300
    },
    "util": {
        "timezone": "Asia/Shanghai",
        "threads": 20,
        "timeout": 30
    }
}
```

</details>

---
# 说明

 - 首次运行将下载、发送并在终端展示雨课堂登录二维码，微信扫码获取 cookie，有效期约两周；有效期少于两天时，每小时初将发送二维码提醒，请及时扫码更新，谨防失效后消息轰炸

 - 支持多用户配置，每个用户独立运行，互不影响

 - 支持多协程监听：每 30 秒扫描新课堂、尝试使用班级邀请码/课堂暗号加入新班级，随后自动签到、下载课件（PDF）、打印题目、生成并打印答案、获取 PPT 进度、自动答题等；每 30 秒扫描新考试，待用户开始考试后，下载试卷、打印题目、生成并打印答案、自动答题、同步答案等

 - 课程名可在雨课堂首页的课程标签里查找，具体如图中红框所示

 ![](classroomName-1.png)

 ![](classroomName-2.png)

 - 课堂签到方式为通过“正在上课”提示进入课堂，不支持动态二维码签到

 - 答案已无法从雨课堂前端获取，支持使用**大语言模型**生成

 - 自动答题支持单选题、多选题、投票题、填空题、主观题和判断题

 - 若课堂自动答题未获取到答案，将提交默认答案（可修改[此处](yuketang.py#L938-L951)）

 - 考试自动答题，指程序检测到用户已开始考试时，将生成或同步答案并上传至考试系统缓存；其并非正式提交，需用户手动提交试卷或考试截止自动提交试卷

 - 考试自动答题支持用户间同步，使能 `isMaster` 的用户答题时，所有使能 `isSlave` 的用户将同步提交相同答案，同步间隔时间约 30 秒

 - 考试系统缓存答案时，会记录 IP 地址和缓存时刻，请尽量使用同一 IP 地址参加考试，手动切换各题答案以保证缓存时刻合理

 - 考试系统不在雨课堂，因此从雨课堂进入考试系统，将通过以下按钮之一跳转到考试系统

 ![](exam-1.png)

 ![](exam-2.png)

 在跳转过程中，考试系统将利用雨课堂 cookie 生成考试系统 `x_access_token`，其有效期约一天，且同一用户同一时间唯一，若用户先在网页端进入考试页面并开始考试，后使用程序进入考试系统，将导致 `x_access_token` 更新，使得网页端考试页面失效

 ![](exam-3.png)

 若考试启用了在线监考，考试开始后可能会随机截屏。为避免以上问题，建议用户在初次进入考试页面，且未开始考试时，调取浏览器开发者工具，进入**网络**选项卡，刷新考试页面，找到任意请求，查看请求头中的 `x_access_token` 字段，并复制该值，填入到 `config.json` 中 `exam` 配置下的对应用户的 `x_access_token` 字段，再启动程序、网页端开始考试；此时程序将直接使用该值进入考试系统，不会生成新的 `x_access_token` 导致网页端考试页面失效

 ![](exam-4.png)

## 配置文件

### yuketang

<details>
<summary><code>users</code></summary>

用户配置列表。参数如下：

 - <code>name</code>

用于标识用户，自定义

 - <code>enabled</code>

是否启用该用户

 - <code>domain</code>

雨课堂域名，按需选择
| 网站 | 域名 |
| -------- | -------- |
| 雨课堂 | [www.yuketang.cn](https://www.yuketang.cn) |
| 荷塘雨课堂 | [pro.yuketang.cn](https://pro.yuketang.cn) |
| 长江雨课堂 | [changjiang.yuketang.cn](https://changjiang.yuketang.cn) |
| 黄河雨课堂 | [huanghe.yuketang.cn](https://huanghe.yuketang.cn) |

 - <code>lesson</code>课程签到、答题等配置：

   - <code>classroomWhiteList</code>

   课程白名单。记录课程名，课程名采用完全匹配，优先级低于黑名单，为空时不启用

   - <code>classroomBlackList</code>

   课程黑名单。记录课程名，课程名采用完全匹配，优先级高于白名单，为空时不启用

   - <code>classroomStartTimeDict</code>

   课程星期内各日最早进入时间。课程名采用完全匹配；使用指定时区，周一-周日对应 `1 - 7`，时间格式为 `HH:MM`；当日时间值不为空且此时早于该值不签到，数字或时间为空不启用

   - <code>llm</code>

   是否使用大语言模型生成答案

   - <code>an</code>

   是否自动答题

   - <code>ppt</code>

   是否发送 PPT 文件

   - <code>si</code>

   是否实时推送 PPT 进度

 - <code>exam</code>考试答题配置：

   - <code>classroomWhiteList</code>

   课程白名单。记录课程名，优先级低于黑名单，课程名采用完全匹配，为空时表示不启用考试答题功能

   - <code>llm</code>

   是否使用大语言模型生成答案

   - <code>an</code>

   是否自动答题

   - <code>paper</code>

   是否发送试卷文件

   - <code>isMaster</code>

   是否为主控用户，主控用户答题时，所有使能从控用户将同步提交相同答案

   - <code>isSlave</code>

   是否为从控用户，从控用户将同步主控用户的答案

   - <code>x_access_token</code>

   考试系统访问令牌，若填写则直接使用该值进入考试系统，不会生成新的令牌；若不填写，程序将自行生成

 - <code>other</code>其他配置：

   - <code>classroomCodeList</code>

   班级邀请码/课堂暗号列表。每 30 秒尝试加入相应班级，班级满员时可启用此功能待成员退出抢占名额

 - <code>services</code>

推送服务名称列表，填写 `send.services` 中配置的 `name`

</details>

<details>
<summary><code>timeout</code></summary>

连接雨课堂、考试系统的超时秒数

</details>

### send

<details>
<summary><code>services</code></summary>

推送方式配置，目前支持企业微信、钉钉、飞书

#### 通用字段
| 字段 | 说明 |
| --- | --- |
| name | 服务名称（自定义，用于通行密钥标识） |
| enabled | 是否启用 |
| type | 服务类型（wechat/dingtalk/feishu） |
| msgLimit | 单次文本长度限制（字符） |
| dataLimit | 单次文件大小限制（字节） |

#### 服务凭证

 - 企业微信：[注册企业微信](https://work.weixin.qq.com/wework_admin/register_wx?from=myhome)、[创建应用](https://work.weixin.qq.com/wework_admin/frame#apps/createApiApp)、[**配置企业可信 IP**](https://work.weixin.qq.com/wework_admin/frame#apps)，填充 `touser`、`agentId`、`secret`、`companyId`

 - 钉钉：[注册钉钉开发者账号](https://open-dev.dingtalk.com/)、[创建并发布企业内部应用（应用内创建机器人）](https://open-dev.dingtalk.com/fe/app#/corp/app)、创建群会话、[获取群会话 openConversationId](https://open.dingtalk.com/tools/explorer/jsapi?id=10303)、机器人添加进群，填充 `appKey`、`appSecret`、`robotCode`、`openConversationId`

 - 飞书：[注册飞书开发者账号、创建并发布企业内部应用](https://open.feishu.cn/app?lang=zh-CN)、[开启机器人能力](https://open.feishu.cn/document/faq/trouble-shooting/how-to-enable-bot-ability)、[获取 OpenId](https://open.feishu.cn/document/server-docs/im-v1/message/create)、开通权限（[*以应用的身份发消息*](https://open.feishu.cn/document/server-docs/im-v1/message/create)，[*获取与上传图片或文件资源*](https://open.feishu.cn/document/server-docs/im-v1/file/create)），填充 `appId`、`appSecret`、`openId`

#### 分块限制

单次推送有大小限制，超过将分块传输，可设置
| 推送方式 | 消息限制 (`msgLimit`) | 文件限制 (`dataLimit`) |
| -------- | -------- | -------- |
| 企业微信 (`wx`) | 500字符 (500) | 20MB (20971520) |
| 钉钉 (`dd`) | 3000字符 (3000) | 20MB (20971520) |
| 飞书 (`fs`) | 10000字符 (10000) | 30MB (31457280) |

</details>

<details>
<summary><code>threads</code></summary>

并行服务的最大线程数

</details>

<details>
<summary><code>timeout</code></summary>

连接服务的超时秒数

</details>

### llm

<details>
<summary><code>models</code></summary>

大语言模型配置，目前支持 [OpenAI](https://platform.openai.com/docs/models)、[Claude](https://docs.claude.com/en/docs/about-claude/models/overview)、[Grok](https://docs.x.ai/docs/models)、[Gemini](https://ai.google.dev/gemini-api/docs/models)、[Cloudflare](https://developers.cloudflare.com/workers-ai/models/)、[OpenRouter](https://openrouter.ai/models)、[Poixe](https://poixe.com/model)、[硅基流动](https://cloud.siliconflow.cn/me/models)、[无问芯穹](https://cloud.infini-ai.com/genstudio/model)、[智谱](https://bigmodel.cn/console/modelcenter/square)、[DMXAPI](https://www.dmxapi.com/pricing)、[魔塔社区](https://modelscope.cn/models)、[月之暗面](https://platform.moonshot.cn/docs/pricing/chat)、[火山方舟](https://console.volcengine.com/ark/region:ark+cn-beijing/model)、[PoloAPI](https://poloapi.com/models)、[阿里云百炼](https://bailian.console.aliyun.com/?tab=model#/model-market)、[百度千帆](https://console.bce.baidu.com/qianfan/modelcenter/model/buildIn/list)、[讯飞星辰](https://maas.xfyun.cn/modelSquare)、[MiniMax](https://www.minimaxi.com/)、[商汤大装置](https://console.sensecore.cn/aistudio/plaza)、[Mistral](https://mistral.ai/pricing#api-pricing)、[腾讯云](https://console.cloud.tencent.com/tokenhub/models)、[Cohere](https://docs.cohere.com/docs/models) 等服务商或中转站

#### 通用字段
| 字段 | 说明 |
| --- | --- |
| name | 服务名称（自定义，用于答案标识） |
| enabled | 是否启用 |
| type | 服务类型（openai、claude 等） |
| model | 模型名称 |
| prompt | 系统提示词 |
| temperature | 采样温度，推荐取 `0 ~ 0.3`  |
| score | 模型评分，数值越大生成答案优先级越高 |

#### 服务凭证

可到各官网注册、充值获取填充

#### 模型选用

 - 选用模型时应综合考虑响应速度、生成质量、使用限制、费用等因素

 - 尽量使用支持 PDF 文件或图片输入的多模态模型

 - 推荐使用 OpenAI、Claude、Gemini 等主流模型

 - 预置模型优先采用效果最好的免费模型

 - 使用非预置模型可能需要适配，可自行修改 `llm.py`

#### 答案选取

 - 多模型并行生成答案，优先选取总评分最高的结果

 - 若多个结果评分相同，选取出现频率最高的结果

 - 若有多个结果频率相同且题型为多选题，选取选项最少的结果

 - 若仍有多个结果，选取所有结果中耗时最长的模型生成的结果

#### 模型测试

使用模型前务必测试效果，确保能正确处理题目并生成合理答案

预置了 [PPT 文件夹](./data/file/pro.yuketang.cn/lesson/1529274209982060032)，可用来测试各模型效果。直接运行 `llm.py` 观察输出即可

```shell
python llm.py
```

若想测试其他课堂，可在使用程序签到该课堂、生成 PPT 文件夹后，修改 [PPT 路径](llm.py#L1249)

</details>

<details>
<summary><code>threads</code></summary>

并行模型的最大线程数

</details>

<details>
<summary><code>timeout</code></summary>

连接模型的超时秒数

</details>

### util

<details>
<summary><code>timezone</code></summary>

时区

</details>

<details>
<summary><code>threads</code></summary>

下载 PPT 图片的最大线程数

</details>

<details>
<summary><code>timeout</code></summary>

下载资源的超时秒数

</details>

---
# 声明

 - 项目尚有许多不足

 - 修改自 [timeflykai/lazytool](https://github.com/timeflykai/lazytool/tree/main)
