#!/bin/bash
# 上传单个 youtube 视频，并烧入硬字幕
# 需要已安装 ffmpeg,python >= 3.7

credentials=$(dialog --backtitle "上传 Youtube 视频到 B 站" \
       --title "登陆"                       \
       --form "认证信息"                     \
       15 50 0                              \
       "用户名" 1 1 "" 1 10 30 0    \
       "密码" 2 1 "" 2 10 30 0     \
       --output-fd 1)
username=$(echo $credentials | cut -f1 -d ' ';)
password=$(echo $credentials | cut -f2 -d ' ';)

if [ -z "$username" ] || [ -z "$password" ] ; then exit 1 ; fi

yt_url=$(dialog --backtitle "上传 Youtube 视频到 B 站" \
                --title     "转载 URL"                \
                --inputbox "e.g. https://youtu.be/BaW_jenozKc" 0 60  --output-fd 1)
if [ -z "$yt_url" ] ; then exit 1 ; fi

python -m bilibili_toolman \
--username $username \
--pwd $password \
--youtube $yt_url \
--title "[bilibili-toolman] {title}" \
--tags "测试" \
--thread_id 127 \
--opts "hardcode=output: -crf 17 -b:v 5M"                                              
