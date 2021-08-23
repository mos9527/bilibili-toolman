# -*- coding: utf-8 -*-
'''API 实例 - 稿件修改

可提供 '--save' 产生的登陆态跳过登陆过程, e.g. this.py credentials.sav

附加依赖：

    inquirer

除【删除稿件】限 PC端 API 外，其余 API 不限版本,
'''

from inquirer.shortcuts import confirm, list_input
from bilibili_toolman.bilisession.common.submission import Submission
from bilibili_toolman.bilisession.client import BiliSession
from pickle import loads
from inquirer import text
import sys
sess = None
if len(sys.argv) > 1:
    loaded = loads(open(sys.argv[1],'rb').read())
    sess : BiliSession = loaded['session']
    sess.update(loaded)
else:
    sess = BiliSession()
    sess.LoginViaUsername(text('用户名'),text('密码'))

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
    sub = sess.ViewSubmission(bvid)
    print(f'''[-] {sub.title}：
        - BV号     ： {sub.bvid}
        - 状态     :  {sub.state_desc}
        - 上传时间  :  {to_yymmdd(sub.stat['ptime'])}
        - 标签     :  {','.join(sub.tags)}
        - 描述     :  
        {add_indent(sub.description,'      ')[3:]}''')
    routines = {}
    @register('编辑描述',routines)
    def edit_title():        
        sub.description = text('输入新标题')    
    @register('编辑标题',routines)
    def edit_title():        
        sub.title = text('输入新标题')
    @register('编辑标签',routines)
    def edit_tags():
        new_tags = text('输入新标签（逗号隔开）')
        sub.tags = new_tags.split(',')
    @register('编辑子视频',routines)
    def edit_sub_archive():    
        v = list_input('选择子视频',choices=[v for v in sub.videos])    
        routines = {}    
        @register('修改子视频标题',routines)
        def edit_sub_title():
            v.title = text('新标题')
        @register('修改子视频内容',routines)
        def edit_sub_video():
            path = text('新视频路径')
            ep,bid = sess.UploadVideo(path)            
            print('新节点：',ep)
            if bid:v.biz_id = bid
            v.video_endpoint = ep        
        while select_and_execute(routines):
            print(v)
    @register('提交更改',routines)
    def submit_sub_video():
        print(sess.EditSubmission(sub))
        return False            
    @register('删除作品',routines)
    def delete_archive():
        if confirm('该操作不可逆，确定？'):
            print(sess.DeleteArchive(sub.bvid))
            return False        
    while select_and_execute(routines):pass

if __name__ == '__main__':
    while select_and_execute(routines):pass