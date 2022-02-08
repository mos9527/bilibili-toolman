# -*- coding: utf-8 -*-
from bilibili_toolman.bilisession.client import BiliSession
import sys
def print_usage_and_quit():
    print('usage : python token-info.py 登陆凭据')
    print('        详情见 README / 准备凭据')
if len(sys.argv) > 1:
    try:
        sess = BiliSession.from_base64_string(sys.argv[1])
    except Exception as e:        
        print(e)
        print_usage_and_quit()        
else:
    print_usage_and_quit()        

print('** Type             :','上传助手 (PC)' if type(sess) == BiliSession else 'Web' ,'端')
print('** login_tokens (PC):',getattr(sess,'login_tokens','N/A'))
print('** Cookies          ：',dict(sess.cookies.__dict__) or 'PC端，或无 Cookies')