# 上传单个 youtube 视频，并烧入硬字幕
# 需要已安装 ffmpeg
echo 输入用户名
read username
echo 输入密码
read password
echo 输入视频链接 e.g. https://youtu.be/BaW_jenozKc
read yt_url

python -m bilibili_toolman --title "[bilibili-toolman] {title}" --tags "测试" --thread_id 127 --opts "cookies=./test_youtube_cookies;hardcode=output: -crf 17 -b:v 5M"