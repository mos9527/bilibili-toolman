# -*- coding: utf-8 -*-
'''API 实例 - 字幕提交

适用于 VTT，BCC（B站字幕）的互转和上传

本 API 限用 Web 版，需要 Cookies 登陆
'''
import re
from typing import List
from inquirer.shortcuts import confirm, list_input
from requests.models import ProtocolError
from bilibili_toolman.bilisession.common.submission import Submission
from bilibili_toolman.bilisession.web import BiliSession
from pickle import loads
from inquirer import text
import sys,json
sess = None
if len(sys.argv) > 1:
    loaded = loads(open(sys.argv[1],'rb').read())
    sess : BiliSession = loaded['session']
    sess.update(loaded)
else:
    sess = BiliSession()
    sess.LoginViaCookiesQueryString(text("输入 Cookies e.g. SESSDATA=...;bili_jct=..."))

TIMECODE = re.compile(r'\d{2}:\d{2}:\d{2}.\d{3}')
HTMLTAGS = re.compile(r'(<[0-9a-zA-Z\/\.:]*>)')

class SubtitleLine:
    @staticmethod    
    def stamp2tag(timestamp):
        hh = int(timestamp // 3600)
        mm = int(timestamp // 60)
        ss = int((timestamp - mm * 60 - hh * 3600))
        xx = int((timestamp - mm * 60 - hh * 3600 - ss) * 1000)
        hh,mm,ss,xx = str(hh).rjust(2,'0'),str(mm).rjust(2,'0'),str(ss).rjust(2,'0'),str(xx).rjust(3,'0')
        return f'{hh}:{mm}:{ss}.{xx}'                    
    @staticmethod
    def tag2stamp(tag):            
        tag = tag.strip()
        hh,mm,sx = tag.split(':')
        ss,xx = sx.split('.')
        timestamp = int(hh) * 3600 + int(mm) * 60 + int(ss) + int(xx) * (0.1 ** len(xx))        
        return timestamp
    # guess where these come from
    def __init__(self,t_from=0,t_to=0,content='',location=2) -> None:
        self.t_from = t_from
        self.t_to = t_to
        self.content = content
        self.location = location
    def __repr__(self) -> str:        
        return '%s --> %s\n%s' % (self.stamp2tag(self.t_from),self.stamp2tag(self.t_to),self.content)        
    def __dict__(self) -> dict:
        return {'from':round(self.t_from,2),'to':round(self.t_to,2),'content': HTMLTAGS.sub('',self.content),'location':self.location}

class Subtitles(list):
    '''简单 VTT,BCC 解编码器'''
    def append(self, line : SubtitleLine):        
        return super().append(line)        
    @property
    def sorted(self) -> List[SubtitleLine]:
        '''排序后字幕内容'''
        return Subtitles(from_subtitles=sorted(self,key=lambda v:v.t_from))
    @property
    def propagated(self,t_delta=0.5):
        '''限制字幕出现时间差，备用'''
        i,t_last,buffer,new = 0,0,[],Subtitles()
        lst = self.sorted
        for i in range(0,len(lst)):
            line = lst[i]
            if line.t_from - t_last < t_delta:
                buffer.append(line.content)
            else:            
                new.append(SubtitleLine(round(t_last,2),round(line.t_to,2),'\n'.join(buffer + [line.content])))
                t_last = line.t_to + t_delta
                buffer.clear()
        if buffer:
            new[-1].t_to = lst[-1].t_to
            new[-1].content = new[-1].content + '\n%s' % lst[-1].content
        return new
    @property
    def archive(self) -> List[dict]:
        '''输出字典，供 B 站使用'''
        return [v.__dict__() for v in self.sorted]
    def __repr__(self) -> str:
        '''输出 VTT'''
        return 'WEBVTT\n'+'\n\n'.join(['%s\n%s' % (i+1,v) for i,v in enumerate(self.sorted)])
    def __init__(self,from_json=None,from_vtt='',from_subtitles=None):
        if from_json:
            for line in from_json:
                self.append(SubtitleLine(line['from'],line['to'],line['content'],line['location']))
        elif from_vtt:        
            lines,i = from_vtt.split('\n'),0            
            while i < len(lines):                
                if '-->' in lines[i]:
                    t_start,t_end = TIMECODE.findall(lines[i])
                    i+=1
                    content = []
                    while lines[i]:
                        content.append(lines[i])
                        i+=1
                    self.append(SubtitleLine(SubtitleLine.tag2stamp(t_start),SubtitleLine.tag2stamp(t_end),'\n'.join(content)))                    
                i+=1
        elif from_subtitles:
            super().__init__(from_subtitles)

class ReprByKey(dict):
    def __init__(self,dict,key):
        self.key = key
        super().__init__(dict)
    def __repr__(self) -> str:
        return self[self.key]

class AttributeDict(dict):
    def __getattribute__(self, name: str):
        if name in self:return self[name]
        return super().__getattribute__(name)
    def __dir__(self):
        return super().__dir__() + self.keys()

def to_yymmdd(ts):
    from datetime import datetime
    ts = datetime.fromtimestamp(ts)
    return ts.strftime('%Y/%m/%d %H:%M:%S')
def add_indent(s : str,indent):
    return ''.join('%s%s\n'%(indent,i) for i in s.split('\n'))
def build_dict(by_key,from_list : list):
    return {getattr(i,by_key):i for i in from_list}
def register(key,calltable):    
    def wrapper(func):
        calltable[key] = func
        return func
    return wrapper

def select_and_execute(from_calltable):
    choices={**from_calltable,'退出':lambda:False}
    choice = list_input('',choices=choices)
    result = choices[choice]()
    return result == None or result
routines = {}
@register('选择作品',routines)
def main_entrance():
    bvid = text('BVid 号 [留空进入选择页面]')
    if not bvid:
        subs = sess.ListSubmissions(limit=10)
        bvid=list_input('选择视频',choices=[f'{sub.title}' for sub in subs])
        bvid=build_dict('title',subs)[bvid].bvid
    sub = AttributeDict(sess.ViewPublicArchive(bvid)['data'])
    print(f'''[-] {sub.title}：
        - BV号     ： {sub.bvid}
        - 上传时间  :  {to_yymmdd(sub.pubdate)}
        - UP       :  {sub.owner['name']}
        - 描述     :  
        {add_indent(sub.desc,'      ')[3:]}''')
    routines = {}
   
    @register('编辑子视频',routines)
    def edit_sub_archive():            
        vid = list_input('选择子视频',choices=[ReprByKey(v,'part') for v in sub.pages])    
        print(vid,'时长：',vid['duration'])
        routines = {}    
        @register('查看已有字幕',routines)
        def view_current_subs():
            vs = sess.ViewPlayerArchive(vid['cid'],sub.bvid)['data']['subtitle']['subtitles']
            if not vs:return print('无字幕') or False
            v = list_input('选择字幕',choices=[ReprByKey(i,'lan_doc') for i in vs])
            @register('查看字幕',routines)
            def view_sub():
                s = sess.GetSubtitleDetail(vid['cid'],v['id'])['data']            
                json = sess.get(s['subtitle_url']).json()['body']
                vsub = Subtitles(from_json=json)
                print(vsub)
            @register('撤回字幕',routines)
            def revoke_sub():
                t = text('撤回理由')
                result=sess.RevokeSubtitle(vid['cid'],v['id'],t)                
                return print(result) or False                
        @register('上传字幕',routines)
        def upload_sub():            
            lan=list_input('字幕语言',choices=['zh-CN','zh-HK','zh-TW','en-US','ja','ko'])
            fp=text('输入 VTT 格式字幕路径：')
            vsub = Subtitles(from_vtt=open(fp,encoding='utf-8').read())
            asub = vsub.archive
            # 检查时长
            flag = False
            buffer = []
            for line in asub[::-1]:                                
                if line['to'] > vid['duration']:
                    line['to'] = vid['duration']                
                    flag = True
                if line['from'] > vid['duration']:       
                    buffer.append(line['content'])
                    del line                                 
                    flag = True
                if not flag:break              
            if buffer:
                asub[-1].content = [asub[-1].content] + buffer
                asub[-1].content = '\n'.join(asub[-1].content)                
            result=sess.SaveSubtitleDraft(
                sub.bvid,vid['cid'],
                data={"font_size":0.4,"font_color":"#FFFFFF","background_alpha":0.5,"background_color":"#9C27B0","Stroke":"none","body":asub},
                lang=lan
            )
            return print(result) or False
        while select_and_execute(routines):pass
    while select_and_execute(routines):pass

if __name__ == '__main__':
    while select_and_execute(routines):pass