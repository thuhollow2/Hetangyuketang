**Android 使用请移步 [termux 分支](../../tree/termux)**

**iOS 使用请移步 [ish 分支](../../tree/ish)**

---
# 安装依赖

```shell
pip install -r requirements.txt 
```
 - `pyzbar` 是对 **ZBar** 的 Python 封装，本身需要系统里有 **libzbar** 动态库；非 Windows 上必须先装 zbar 才能用

---
# 运行

```shell
python main.py
```

## 配置文件
<details>
<summary><code>config.json</code></summary>

```json
{
  "yuketang": {
    "domain": "pro.yuketang.cn",
    "classroomCodeList": ["JZOJ5C", "G84UAB"],
    "classroomWhiteList": [],
    "classroomBlackList": ["2023秋-机器学习-0", "2023清华实践"],
    "classroomStartTimeDict": {
      "2023秋-机器学习-0": {"1": "08:00", "2": "13:30"},
      "2023清华实践": {"1": "13:30"}
    },
    "llm": false,
    "an": false,
    "ppt": false,
    "si": false,
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
        "name": "openai-o4-mini",
        "enabled": false,
        "type": "openai",
        "apiKey": "####",
        "model": "o4-mini",
        "prompt": "You are a helpful assistant.",
        "score": 100
      },
      {
        "name": "claude-3-5",
        "enabled": false,
        "type": "claude",
        "apiKey": "####",
        "model": "claude-3-5",
        "prompt": "You are a helpful assistant.",
        "temperature": 0.2,
        "score": 100
      },
      {
        "name": "grok-4-0709",
        "enabled": false,
        "type": "grok",
        "apiKey": "####",
        "model": "grok-4-0709",
        "prompt": "You are a helpful assistant.",
        "temperature": 0.2,
        "score": 100
      },
      {
        "name": "gemini-2.5-flash",
        "enabled": false,
        "type": "gemini",
        "apiKey": "####",
        "model": "gemini-2.5-flash",
        "prompt": "You are a helpful assistant.",
        "temperature": 0.2,
        "score": 100
      },
      {
        "name": "cloudflare-llama-4-scout-17b",
        "enabled": false,
        "type": "cloudflare",
        "accountId": "####",
        "apiToken": "####",
        "model": "@cf/meta/llama-4-scout-17b-16e-instruct",
        "prompt": "You are a helpful assistant.",
        "temperature": 0.2,
        "score": 100
      },
      {
        "name": "openrouter-gpt-oss-20b",
        "enabled": false,
        "type": "openrouter",
        "apiKey": "####",
        "model": "openai/gpt-oss-20b:free",
        "prompt": "You are a helpful assistant.",
        "temperature": 0.2,
        "score": 100
      },
      {
        "name": "poixe-gemini-2.5-flash",
        "enabled": false,
        "type": "poixe",
        "apiKey": "####",
        "model": "gemini-2.5-flash:free",
        "prompt": "You are a helpful assistant.",
        "temperature": 0.2,
        "score": 100
      },
      {
        "name": "siliconflow-glm-4.1v-9b-thinking",
        "enabled": false,
        "type": "siliconflow",
        "apiKey": "####",
        "model": "THUDM/GLM-4.1V-9B-Thinking",
        "prompt": "You are a helpful assistant.",
        "temperature": 0.2,
        "score": 100
      },
      {
        "name": "infinigence-glm-4.5v",
        "enabled": false,
        "type": "infinigence",
        "apiKey": "####",
        "model": "glm-4.5v",
        "prompt": "You are a helpful assistant.",
        "temperature": 0.2,
        "score": 100
      },
      {
        "name": "zhipu-glm-4.1v-thinking-flash",
        "enabled": false,
        "type": "zhipu",
        "apiKey": "####",
        "model": "GLM-4.1V-Thinking-Flash",
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
        "name": "modelscope-intern-s1",
        "enabled": false,
        "type": "modelscope",
        "accessToken": "####",
        "model": "Shanghai_AI_Laboratory/Intern-S1",
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

 - 支持多线程监听，每 30 秒扫描新课堂、尝试使用邀请码/课堂暗号加入新班级，随后自动签到、下载课件（PDF）、打印题目、生成并打印答案、获取 PPT 进度、自动答题等

 - 签到方式为通过“正在上课”提示进入课堂

 - 答案已无法从雨课堂前端获取，现改用大语言模型生成

 - 自动答题支持单选题、多选题、投票题、填空题和主观题（未曾测试过主观题，可能报错）；若未获取到答案，将提交默认答案（可修改[此处](yuketang.py#L343-L354)）

 - 课程名可在雨课堂首页的课程标签里查找，具体如[图](classroomName.png)中蓝框所示

## 配置文件

### yuketang

<details>
<summary><code>domain</code></summary>

雨课堂域名
| 网站 | 域名 |
| -------- | -------- |
| 雨课堂 | [www.yuketang.cn](https://www.yuketang.cn) |
| 荷塘雨课堂 | [pro.yuketang.cn](https://pro.yuketang.cn) |
| 长江雨课堂 | [changjiang.yuketang.cn](https://changjiang.yuketang.cn) |
| 黄河雨课堂 | [huanghe.yuketang.cn](https://huanghe.yuketang.cn) |

</details>

<details>
<summary><code>classroomCodeList</code></summary>

邀请码/课堂暗号列表。每 30 秒尝试加入相应班级，班级满员时可启用此功能待成员退出抢占名额

</details>

<details>
<summary><code>classroomWhiteList</code></summary>

课程白名单。记录课程名，优先级低于黑名单，课程名采用完全匹配，为空时不启用

</details>

<details>
<summary><code>classroomBlackList</code></summary>

课程黑名单。记录课程名，优先级高于白名单，课程名采用完全匹配，为空时不启用

</details>

<details>
<summary><code>classroomStartTimeDict</code></summary>

课程星期内各日最早进入时间。课程名采用完全匹配；使用指定时区，周一-周日对应 `1 - 7`，时间格式为 `HH:MM`；当日时间值不为空且此时早于该值不签到，数字或时间为空不启用

</details>

<details>
<summary><code>llm</code></summary>

是否使用大语言模型生成答案

</details>

<details>
<summary><code>an</code></summary>

是否自动答题

</details>

<details>
<summary><code>ppt</code></summary>

是否发送 PPT 文件

</details>

<details>
<summary><code>si</code></summary>

是否实时推送 PPT 进度

</details>

<details>
<summary><code>timeout</code></summary>

连接雨课堂的超时秒数

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

 - 企业微信：[注册企业微信](https://work.weixin.qq.com/wework_admin/register_wx?from=myhome)、[创建应用](https://work.weixin.qq.com/wework_admin/frame#apps/createApiApp)、[**配置企业可信IP**](https://work.weixin.qq.com/wework_admin/frame#apps)，填充 `touser`、`agentId`、`secret`、`companyId`

 - 钉钉：[注册钉钉开发者账号](https://open-dev.dingtalk.com/)、[创建并发布企业内部应用（应用内创建机器人）](https://open-dev.dingtalk.com/fe/app#/corp/app)、创建群会话、[获取群会话openConversationId](https://open.dingtalk.com/tools/explorer/jsapi?id=10303)、机器人添加进群，填充 `appKey`、`appSecret`、`robotCode`、`openConversationId`

 - 飞书：[注册飞书开发者账号、创建并发布企业内部应用](https://open.feishu.cn/app?lang=zh-CN)、[开启机器人能力](https://open.feishu.cn/document/faq/trouble-shooting/how-to-enable-bot-ability)、[获取OpenId](https://open.feishu.cn/document/server-docs/im-v1/message/create)、开通权限（[*以应用的身份发消息*](https://open.feishu.cn/document/server-docs/im-v1/message/create)，[*获取与上传图片或文件资源*](https://open.feishu.cn/document/server-docs/im-v1/file/create)），填充 `appId`、`appSecret`、`openId`

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

大语言模型配置，目前支持 [OpenAI](https://platform.openai.com/docs/models)、[Claude](https://docs.claude.com/en/docs/about-claude/models/overview)、[Grok](https://docs.x.ai/docs/models)、[Gemini](https://ai.google.dev/gemini-api/docs/models)、[Cloudflare](https://developers.cloudflare.com/workers-ai/models/)、[OpenRouter](https://openrouter.ai/models)、[Poixe](https://poixe.com/model)、[硅基流动](https://cloud.siliconflow.cn/me/models)、[无问芯穹](https://cloud.infini-ai.com/genstudio/model)、[智谱](https://bigmodel.cn/console/modelcenter/square)、[DMXAPI](https://www.dmxapi.com/pricing)、[魔塔社区](https://modelscope.cn/models)等服务商或中转站

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

 - 推荐使用 OpenAI、Claude、Gemini 等大厂模型

 - 预置模型优先采用效果最好的免费模型

 - 使用非预置模型可能需要适配，可自行修改 `llm.py`

#### 答案选取

 - 多模型并行生成答案，优先选取总评分最高的结果

 - 若多个结果评分相同，选取出现频率最高的结果

 - 若有多个结果频率相同且题型为多选题，选取选项最少的结果

 - 若仍有多个结果，选取所有结果中耗时最长的模型生成的结果

#### 模型测试

使用模型前务必测试效果，确保能正确处理题目并生成合理答案

预置了[课程文件夹](./1415648550412734208)和[题目](llm.py#L1019-L1025)，可用来测试各模型效果。直接运行 `llm.py` 观察输出即可

```shell
python llm.py
```

若想测试其他课程，可在使用程序签到该课程后，找到程序目录下对应的课程文件夹，修改[课程文件夹名称](llm.py#L1018)；并按照[程序逻辑](llm.py#L342-L387)还原[题目](llm.py#L1019-L1025)

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
