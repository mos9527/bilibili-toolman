# -*- coding: utf-8 -*-
'''获取 Youtube 最新视频链接，多个视频空格隔开'''
import yt_dlp,argparse
parser = argparse.ArgumentParser(description='获取 Youtuber 的最新视频')
parser.add_argument('url',help='Youtuber 频道 URL',type=str)
parser.add_argument('--max',help='获取最新视频量,默认为 1',type=int,default=1)
args = parser.parse_args()

ydl = yt_dlp.YoutubeDL(params={'playlistend':args.max,'quiet':True})
info = ydl.extract_info(args.url,download=False)

entires = [entry for entry in info['entries'][0]['entries']]
# 取得最新视频列表
print(*['https://youtu.be/'+entry['id'] for entry in entires])