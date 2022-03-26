# 安装

    pip install bilibili_toolman

# 使用
## 以 Github Actions 转载视频：
### 准备凭据
凭据需要在本地准备
- [pip 安装 bilibili_toolman](#安装)
- 使用 Web 端 API
    
        python -m bilibili_toolman --save --cookies "SESSDATA=8aafe8**********;bili_jct=4f39b**********"
    `SESSDATA`,`bili_jct` 可在XHR请求头中获得，这里不将阐述
- 使用 上传助手 API
        
        python -m bilibili_toolman --save --sms
    跟随输出操作即可
- 凭据即输出的 Base64 编码内容
### 准备 Actions
- Fork 此项目
- 在项目 Settings > Secret > New repository secret 创建：
    - Name  : `SESSION`
    - Value : `此处为准备好的凭据`
- *可选* 替换不同凭据上传、投稿
   
    **指定上传凭据**
    
    - Name  : `SESSION_UPLOAD`
    - Value : `此处为准备好的凭据`
    
    **指定投稿凭据**
    
    - Name  : `SESSION_SUBMIT`
    - Value : `此处为准备好的凭据`

    一般推荐使用 Web 凭据上传，上传助手凭据投稿（高速 (~400Mbps) 上传，多P投稿）

- 在项目 Actions > 转载 Youtube 视频 > Run Workflow 填入值（[详见参数说明](#参数说明)）
- 运行即可
## API 使用示例
```python
>>> from bilibili_toolman import BiliWebSession,Submission,SubmissionVideos
# 取决于欲使用的 API，详见 Wiki
>>> session = BiliWebSession.from_base64_string("H4sIADKW+2EC/5VVWW/bRhB2EF216...") 
# 从 --save 凭据恢复登录态
>>> endpoint_1,cid_1 = session.UploadVideo("unfathomably_original_content.mp4")
('n220208141kq78....', ...)
>>> endpoint_1,cid_2 = session.UploadVideo("disgracefully_stolen_video.mp4")
('n220209892re88....', ...)
# 上传视频并拿 key
>>> submission = Submission(
    title="【转载】 Boss...",
    desc="THEY PLAYED US LIKE A DAMN FIDDLE"
)
# 新建多 P 稿件 (标题描述内非 CJK/ASCII（如emoji）字符会导致稿件无效)（单 P 过程详见Wiki）
>>> submission.videos.append(
    Submission(
        title="The Ruse",
        video_endpoint=endpoint_1
    )
)
>>> submission.videos.append(
    Submission(
        title="The Fall",
        video_endpoint=endpoint_2
    )
)    
# 添加视频 (P)，注意仅父节点（稿件）描述会被显示；分 P 视频和父稿件同类型
>>> cover = session.UploadCover('nice_image_bro.png')
>>> submission.cover_url = cover['data']['url']    
# 上传，设置封面
>>> submission.source = 'uhhhhh internet?'        
# 设置转载来源
>>> submission.tags.append('转载')
# 添加标签
>>> submission.thread = 69
# 设置分区（详见Wiki）
>>> session.SubmitSubmission(submission)           
{'code:': 0,
    'results': [{'code': 0, 'message': '0','ttl': 1,
    'data': {'aid': 5939...., 'bvid': 'BV1oq....'}}]}
```
## 其它
### 例程 :
- [examples](https://github.com/greats3an/bilibili-toolman/tree/master/examples)
- - [编辑稿件信息](https://github.com/greats3an/bilibili-toolman/blob/master/examples/submission-editor.py)
- - [投稿VTT字幕](https://github.com/greats3an/bilibili-toolman/blob/master/examples/subtitle-helper.py)
- - [解码 `--save` 凭据](https://github.com/greats3an/bilibili-toolman/blob/master/examples/token-info.py)
- [main.py](https://github.com/greats3an/bilibili-toolman/blob/master/bilibili_toolman/cli/main.py)
### API 实现 ：
- [client.py](https://github.com/greats3an/bilibili-toolman/blob/master/bilibili_toolman/bilisession/client.py)
- [web.py](https://github.com/greats3an/bilibili-toolman/blob/master/bilibili_toolman/bilisession/web.py)
# 截图
![le screen shot of le console](https://raw.githubusercontent.com/greats3an/bilibili-toolman/master/readme.png)

# 感谢
[PC 上传助手逆向 · FortuneDayssss/BilibiliUploader](https://github.com/FortuneDayssss/BilibiliUploader)

[分区数据，API 参考 · Passkou/bilibili_api](https://github.com/Passkou/bilibili_api "Passkou · bilibili_api")

[Youtube 解析 · yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp "yt-dlp · yt-dlp")


## 参数说明
    usage: -h [-h] [--cookies COOKIES] [--sms] [--load LOAD]
            [--load_upload LOAD_UPLOAD] [--load_submit LOAD_SUBMIT] [--save]
            [--http] [--noenv] [--cdn {ws,qn,bda2,kodo,gcs,bos}] [--opts OPTS]
            [--thread_id THREAD_ID] [--tags TAGS] [--desc DESC] [--title TITLE]
            [--seperate_parts] [--no_upload] [--no_submit] [--original]
            [--no_reprint] [--localfile LOCALFILE-URL] [--youtube YOUTUBE-URL]

    使用帮助

    optional arguments:
    -h, --help            show this help message and exit

    身份设置 （随方式优先级排序）:
    --cookies COOKIES     登陆： 使用 Cookies 登陆，即使用 Web API （不可多 P 上传） ( 需要 SESSDATA 及 bili_jct ) e.g.SESSDATA=cb0..; bili_jct=6750...
    --sms                 登陆：使用短信验证码登陆，即使用 上传助手 API （可多 P 上传）（需手动交互）（有日获取限制，请配合 --save 使用）
    --load LOAD           登陆：加载凭据，同时用于上传及投稿
    --load_upload LOAD_UPLOAD
                            登陆：使用该凭据上传，而不用--load凭据上传
    --load_submit LOAD_SUBMIT
                            登陆：使用该凭据投稿，而不用--load凭据投稿
    --save                登陆：向stdout输出当前登陆凭据并退出（其他输出转移至stderr）
    --http                强制使用 HTTP （不推荐）
    --noenv               上传时，不采用环境变量（如代理）
    --cdn {ws,qn,bda2,kodo,gcs,bos}
                            上传用 CDN （限 Web API) （对应 网宿（适合海外），七牛，百度（默认），七牛，谷歌，百度）

    上传设置:
    --opts OPTS           解析可选参数 ，详见 --opts 格式
    --thread_id THREAD_ID
                            分区 ID
    --tags TAGS           标签
    --desc DESC           描述格式 e.g. "原描述：{desc}" (其他变量详见下文)（仅稿件有描述）
    --title TITLE         标题格式 e.g. "[Youtube] {title} (其他变量详见下文)（使用于稿件及分P）"
    --seperate_parts      不分P （e.g. --youtube [播放列表],--localfile [文件夹]）独立投稿（不分P）（Web上传默认不分 P）
    --no_upload           只下载资源
    --no_submit           不提交稿件，适用于获取filename参数
    --original            设置稿件为原创
    --no_reprint          设置稿件不允许转载

    解析可选参数 "opts" （格式 ： [参数1]=[值1];[参数2]=[值2] (query-string)）:
    --localfile LOCALFILE-URL
                            本地文件
                            参数:
                                cover (str) - 封面图片路径
                            e.g. --localfile "le videos/" --opts cover="le cover.png" --tags ...
    --youtube YOUTUBE-URL
                            Youtube / Twitch / etc 视频下载 (yt-dlp)
                            参数:yt-dlp 参数：
                                format (str) - 同 yt-dlp -f
                                quite (True,False) - 是否屏蔽 yt-dlp 日志 (默认 False)
                            特殊参数：
                                hardcode - 烧入硬字幕选项
                                    e.g. 启用    ..;hardcode;...
                                    e.g. 换用字体 ..;hardcode=style:FontName=Segoe UI       
                                    e.g. NV硬解码   ..;hardcode=input:-hwaccel cuda/output:-c:v h264_nvenc -crf 17 -b:v 5M
                                    多个选项用 / 隔开   
                            e.g. --youtube "..." --opts "format=best;quiet=True;hardcode" --tags ...
                                此外，针对视频对象，还提供其他变量:
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
                                注：输入播放列表且多 P 时，稿件标题为播放列表标题，稿件描述仅为 `来自Youtube`
                            
                            默认配置：不烧入字幕，下载最高质量音视频，下载字幕但不操作

    变量：
        {title},{desc} 等变量适用于：
            title, desc, tags

    本工具支持将给定视频源转载至哔哩哔哩

    详见项目 README 以获取更多例程 ： github.com/greats3an/bilibili-toolman

# 分区ID (tid) 表

## 动画
|分区| TID|
|-|-|
|MAD·AMV|24|完结动画|32|
|MMD·3D|25|
|综合|27|
|短片·手书·配音|47|
|特摄|86|
|手办·模玩|210|
## 番剧
|分区| TID|
|-|-|
|连载动画|33|
|资讯|51|
|官方延伸|152|
## 国创
|分区| TID|
|-|-|
|国产动画|153|
|国产原创相关|168|
|布袋戏|169|
|资讯|170|
|动态漫·广播剧|195|
## 音乐
|分区| TID|
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
|分区| TID|
|-|-|
|宅舞|20|
|舞蹈综合|154|
|舞蹈教程|156|
|街舞|198|
|明星舞蹈|199|
|中国舞|200|
## 游戏
|分区| TID|
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
|分区| TID|
|-|-|
|野生技术协会|122|
|社科人文|124|
|科学科普|201|
|财经|207|
|校园学习|208|
|职业职场|209|
## 数码
|分区| TID|
|-|-|
|手机平板|95|
|电脑装机|189|
|摄影摄像|190|
|影音智能|191|
## 生活
|分区| TID|
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
|分区| TID|
|-|-|
|鬼畜调教|22|
|音MAD|26|
|人力VOCALOID|126|
|教程演示|127|
## 时尚
|分区| TID|
|-|-|
|美妆|157|
|服饰|158|
|T台|159|
|健身|164|
|风尚标|192|
## 资讯
|分区| TID|
|-|-|
|热点|203|
|环球|204|
|社会|205|
|综合|206|
## 娱乐
|分区| TID|
|-|-|
|综艺|71|
|明星|137|
## 影视
|分区| TID|
|-|-|
|短片|85|
|影视杂谈|182|
|影视剪辑|183|
|预告·资讯|184|
## 纪录片
|分区| TID|
|-|-|
|人文·历史|37|
|科学·探索·自然|178|
|军事|179|
|社会·美食·旅行|180|
## 电影
|分区| TID|
|-|-|
|其他国家|83|
|欧美电影|145|
|日本电影|146|
|华语电影|147|
## 电视剧
|分区| TID|
|-|-|
|国产剧|185|
|海外剧|187|
