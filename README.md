# bilibili-toolman 哔哩哔哩搬运工具
搬运各大(youtube-dl支持的)网站的视频资源到 Bilibili

# 亮点
- PC 端 （账号密码），Web 端 (Cookies) 多 API 实现
- 多 P 上传 (PC 端 API)
- 多线程上传
- 自定义编码流水线
- ...

# 安装

    pip install bilibili_toolman

## 参数说明
    usage: -h [-h] [--username USERNAME] [--pwd PWD] [--cookies COOKIES] [--load LOAD] [--save SAVE] [--http] [--cdn {ws,qn,bda2,kodo,gcs,bos}] [--opts OPTS] [--thread_id THREAD_ID]
            [--tags TAGS] [--desc DESC] [--title TITLE] [--seperate_parts] [--no_upload] [--original] [--no_reprint] [--localfile LOCALFILE-URL] [--youtube YOUTUBE-URL]

    使用帮助

    optional arguments:
    -h, --help            show this help message and exit

    身份设置 （随方式优先级排序）:
    --username USERNAME   PC API - 账号密码登陆 - Bilibili 账号名
    --pwd PWD             PC API - 账号密码登陆 - Bilibili 账号明文密码
    --cookies COOKIES     Web API - Cookies 登陆 - Bilibili 所用 Cookies ( 需要 SESSDATA 及 bili_jct ) e.g.SESSDATA=cb0..; bili_jct=6750... 
    --load LOAD           从保存的文件中拉取认证信息，作为认证方式
    --save SAVE           在输入上述认证方式之一的前提下，保存该信息于文件，并退出
    --http                强制使用 HTTP （不推荐）
    --cdn {ws,qn,bda2,kodo,gcs,bos}
                            上传用 CDN （限 Web API) （对应 网宿，七牛，百度，七牛，谷歌，百度）

    上传设置:
    --opts OPTS           解析可选参数 ，详见 --opts 格式
    --thread_id THREAD_ID
                            分区 ID
    --tags TAGS           标签
    --desc DESC           描述格式 e.g. "原描述：{desc}" (其他变量详见下文)
    --title TITLE         标题格式 e.g. "[Youtube] {title} (其他变量详见下文)"
    --seperate_parts      不分P （e.g. --youtube [播放列表],--localfile [文件夹]）独立投稿（不分P）（Web上传默认不分 P）
    --no_upload           只下载资源
    --original            设置稿件为原创
    --no_reprint          设置稿件不允许转载

    解析可选参数 "opts" （格式 ： [参数1]=[值1];[参数2]=[值2] (query-string)）:
    --localfile LOCALFILE-URL
                            本地文件
                            参数:
                                cover (str) - 封面图片路径
                            e.g. --localfile "le videos/" --opts cover="le cover.png" --tags ...
    --youtube YOUTUBE-URL
                            Youtube / Twitch / etc 视频下载 (youtube-dl)
                            参数:youtube-dl 参数：
                                format (str) - 同 youtube-dl -f
                                quite (True,False) - 是否屏蔽 youtube-dl 日志 (默认 False)
                            特殊参数：
                                hardcode - 烧入硬字幕选项
                                    e.g. 启用    ..;hardcode;...
                                    e.g. 换用字体 ..;hardcode=style:FontName=Segoe UI
                                    e.g. NV硬解码   ..;hardcode=input:-hwaccel cuda/output:-c:v h264_nvenc -crf 17 -b:v 5M
                                    多个选项用 / 隔开
                            e.g. --youtube "..." --opts "format=best;quiet=True;hardcode" --tags ...
                                此外，还提供其他变量:
                                    {id}
                                    {title}
                                    {descrption}
                                    {upload_date}
                                    {uploader}
                                    {uploader_id}
                                    {uploader_url}
                                    {channel_id}
                                    {channel_url}
                                    {duration}
                                    {view_count}
                                    {avereage_rating}
                                    ...
                            默认配置：不烧入字幕，下载最高质量音视频，下载字幕但不操作

    变量：
        {title},{desc} 等变量适用于：
            title, desc, tags

    本工具支持将给定视频源转载至哔哩哔哩

    详见项目 README 以获取更多例程 ： github.com/greats3an/bilibili-toolman

## API / 命令行 使用说明
### 使用 Github Actions 转载视频：
- [reupload-video.yml](https://github.com/greats3an/bilibili-toolman/blob/master/.github/workflows/reupload-video.yml)
#### 使用：
- Fork 此项目
- 在项目 Settings > Secret > New repository secret 创建：
    - Name  : USER_CRED
    
    若使用 PC API：
    - Value : --username [ B站用户名 ] --pwd [ B站密码 ]

    若使用 Web API:
    - Value : --cookies [ SESSDATA=cb0..; bili_jct=6750... ]
- 在项目 Actions > 转载 Youtube 视频 > Run Workflow 填入值
- 运行即可

### 例程 :
- [examples](https://github.com/greats3an/bilibili-toolman/tree/master/examples)
- - [控制台编辑稿件信息](https://github.com/greats3an/bilibili-toolman/blob/master/examples/submission-editor.py)
- - [控制台投稿VTT字幕](https://github.com/greats3an/bilibili-toolman/blob/master/examples/subtitle-helper.py)
- [main.py](https://github.com/greats3an/bilibili-toolman/blob/master/bilibili_toolman/cli/main.py)
### API 实现 ：
- [client.py](https://github.com/greats3an/bilibili-toolman/blob/master/bilibili_toolman/bilisession/client.py)
- [web.py](https://github.com/greats3an/bilibili-toolman/blob/master/bilibili_toolman/bilisession/web.py)
# 截图
![le screen shot of le console](https://raw.githubusercontent.com/greats3an/bilibili-toolman/master/readme.png)

# 感谢
[PC 上传助手逆向 · FortuneDayssss/BilibiliUploader](https://github.com/FortuneDayssss/BilibiliUploader)

[分区数据，API 参考 · Passkou/bilibili_api](https://github.com/Passkou/bilibili_api "Passkou · bilibili_api")

[Youtube 解析 · ytdl-org/youtube-dl](https://github.com/ytdl-org/youtube-dl "ytdl-org · youtube-dl")

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
