# bilibili-toolman 哔哩哔哩机器人
搬运各*(?)*大网站的视频资源到 Bilibili

# 依赖
    
    pip install -U requests youtube-dl

# 使用

	python bilibili-toolman.py --cookies "SESSDATA=cb0..; bili_jct=6750..." --youtube "https://www.youtube.com/watch?v=_3Mo7U0XSFo" --opts "no_check_certificate=True" --thread_id 17 --tags "..." 

## 参数说明

详见 `--help` 输出

    usage: -h [-h] [--cookies COOKIES] [--show_progress SHOW_PROGRESS] [--opts OPTS] [--thread_id THREAD_ID] [--tags TAGS] [--desc_fmt DESC_FMT] [--title_fmt TITLE_FMT] [--seperate_parts SEPERATE_PARTS] [--no_upload NO_UPLOAD] [--localfile LOCALFILE-URL]
            [--youtube YOUTUBE-URL]

    bilibili-toolman 哔哩哔哩工具人

    optional arguments:
    -h, --help            show this help message and exit
    --cookies COOKIES     Bilibili 所用 Cookies ( 需要 SESSDATA 及 bili_jct ) e.g.cookies=SESSDATA=cb0..; bili_jct=6750...
    --show_progress SHOW_PROGRESS
                            显示上传进度
    --opts OPTS             (视频源选项) 解析设置
    --thread_id THREAD_ID
                            (视频源选项) 分区 ID
    --tags TAGS             (视频源选项) 标签
    --desc_fmt DESC_FMT     (视频源选项) 描述格式 e.g. ％(desc)s
    --title_fmt TITLE_FMT
                            (视频源选项) 标题格式 e.g. ％(title)s
    --seperate_parts SEPERATE_PARTS
                            (视频源选项) 多个视频独立投稿（不分P）
    --no_upload NO_UPLOAD
                            (视频源选项) 只下载资源
    --localfile LOCALFILE-URL
                            (解析器选项) 本地文件
                            Options: cover - 封面图片路径
    --youtube YOUTUBE-URL
                            (解析器选项) Youtube 视频
                            Options: format - 同 youtube-dl -f
                            ( 另可跟随其他 yotube-dl 参数 e.g. format=best;quiet=True )

    本工具支持将给定视频源转载至哔哩哔哩

    参数可由 解析器 (如 --youtube) 引导参数串连 视频源选项 (如 "https://youtube.com..." --thread_id 1..）. 此格式可被重复 (如 --youtube ... --youtube ...)

# 注意

- Web端分P上传 API 自 2020/03 起被限制，目前除换用 PC 客户端 API (WIP) 外别无他法

# 截图
![le screen shot of le console](https://raw.githubusercontent.com/greats3an/bilibili-toolman/master/readme.png)

# 感谢
[分区数据，API 参考 · Passkou · bilibili_api](https://github.com/Passkou/bilibili_api "Passkou · bilibili_api")

[Youtube 解析 · ytdl-org · youtube-dl](https://github.com/ytdl-org/youtube-dl "ytdl-org · youtube-dl")

# 分区表

## 动画
|分区| 分区 ID (tid) |
|-|-|
|MAD·AMV|24|
|MMD·3D|25|
|综合|27|
|短片·手书·配音|47|
|特摄|86|
|手办·模玩|210|
## 番剧
|分区| 分区 ID (tid) |
|-|-|
|完结动画|32|
|连载动画|33|
|资讯|51|
|官方延伸|152|
## 国创
|分区| 分区 ID (tid) |
|-|-|
|国产动画|153|
|国产原创相关|168|
|布袋戏|169|
|资讯|170|
|动态漫·广播剧|195|
## 音乐
|分区| 分区 ID (tid) |
|-|-|
|原创音乐|28|
|音乐现场|29|
|VOCALOID·UTAU|30|
|翻唱|31|
|演奏|59|
|音乐综合|130|
|MV|193|
|电音|194|
## 舞蹈
|分区| 分区 ID (tid) |
|-|-|
|宅舞|20|
|舞蹈综合|154|
|舞蹈教程|156|
|街舞|198|
|明星舞蹈|199|
|中国舞|200|
## 游戏
|分区| 分区 ID (tid) |
|-|-|
|单机游戏|17|
|Mugen|19|
|网络游戏|65|
|GMV|121|
|音游|136|
|电子竞技|171|
|手机游戏|172|
|桌游棋牌|173|
## 知识
|分区| 分区 ID (tid) |
|-|-|
|野生技术协会|122|
|社科人文|124|
|科学科普|201|
|财经|207|
|校园学习|208|
|职业职场|209|
## 数码
|分区| 分区 ID (tid) |
|-|-|
|手机平板|95|
|电脑装机|189|
|摄影摄像|190|
|影音智能|191|
## 生活
|分区| 分区 ID (tid) |
|-|-|
|日常|21|
|动物圈|75|
|美食圈|76|
|搞笑|138|
|手工|161|
|绘画|162|
|运动|163|
|其他|174|
|汽车|176|
## 鬼畜
|分区| 分区 ID (tid) |
|-|-|
|鬼畜调教|22|
|音MAD|26|
|人力VOCALOID|126|
|教程演示|127|
## 时尚
|分区| 分区 ID (tid) |
|-|-|
|美妆|157|
|服饰|158|
|T台|159|
|健身|164|
|风尚标|192|
## 资讯
|分区| 分区 ID (tid) |
|-|-|
|热点|203|
|环球|204|
|社会|205|
|综合|206|
## 娱乐
|分区| 分区 ID (tid) |
|-|-|
|综艺|71|
|明星|137|
## 影视
|分区| 分区 ID (tid) |
|-|-|
|短片|85|
|影视杂谈|182|
|影视剪辑|183|
|预告·资讯|184|
## 纪录片
|分区| 分区 ID (tid) |
|-|-|
|人文·历史|37|
|科学·探索·自然|178|
|军事|179|
|社会·美食·旅行|180|
## 电影
|分区| 分区 ID (tid) |
|-|-|
|其他国家|83|
|欧美电影|145|
|日本电影|146|
|华语电影|147|
## 电视剧
|分区| 分区 ID (tid) |
|-|-|
|国产剧|185|
|海外剧|187|
