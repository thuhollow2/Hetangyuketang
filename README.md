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
        self.wx=False # 设置为True时启用企业微信推送，须在send.py设置个人CompanyId、AgentId、Secret
        self.an=False # 设置为True时自动答题
        self.si=False # 设置为True时实时推送PPT进度
        ...
```

说明：
--
首次运行将下载雨课堂登录二维码（启用企业微信可推送到客户端），扫码允许获取cookie，有效期约两周<br>
每30秒扫描新课堂，随后自动签到、下载课件（pdf）、打印题目及答案、查看当前PPT进度<br>
自动答题仅限选择题（单选和多选），若未查到答案，将以第一个选项提交（如有它需可修改[此处](https://github.com/thuhollow2/Hetangyuketang/blob/main/yuketang.py#L242-L243)）<br>
许多不足亟待完善<br>
项目修改自[timeflykai/lazytool](https://github.com/timeflykai/lazytool/tree/main)
