import os
import argparse
import logging
from pathlib import Path
from .. import providers

class AttribuitedDict(dict):
    def __getattr__(self,name):
        return self[name]
pbar = None
global_args = {    
    'username' : {'help':'账号密码登陆 - Bilibili 账号名'},
    'pwd' : {'help' : '账号密码登陆 - Bilibili 账号明文密码'},
    'cookies': {'help':'Cookies 登陆 - Bilibili 所用 Cookies ( 需要 SESSDATA 及 bili_jct ) e.g.cookies=SESSDATA=cb0..; bili_jct=6750... '},
    'load' : {'help':'从保存的文件中拉取认证信息，作为认证方式'},
    'save' : {'help':'在输入上述认证方式之一的前提下，保存该信息于文件，并退出'}
}
local_args = {
    'opts':{'help':'解析设置，详见 --opts 格式'},
    'thread_id': {'help':'分区 ID','default':17},
    'tags': {'help':'标签','default':'转载'},
    'desc_fmt':{'help':'描述格式 e.g. 原描述：{desc}','default':'{desc}'},
    'title_fmt':{'help':'标题格式 e.g. [Youtube] {title}','default':'{title}'},
    'seperate_parts':{'help':'多个视频（e.g. Youtube 播放列表）独立投稿（不分P）（Web上传默认不分 P）','default':0},
    'no_upload':{'help':'只下载资源','default':0},
}
arg_epilog = '''
本工具支持将给定视频源转载至哔哩哔哩

详见项目 README 以获取更多例程 ： github.com/greats3an/bilibili-toolman
'''
def setup_logging():
    import coloredlogs
    coloredlogs.DEFAULT_LOG_FORMAT = '[ %(asctime)s %(name)8s %(levelname)6s ] %(message)s'
    coloredlogs.install(0);logging.getLogger('urllib3').setLevel(100);logging.getLogger('PIL.Image').setLevel(100)

def prepare_temp(temp_path : str):    
    if not os.path.isdir(temp_path):os.mkdir(temp_path)
    os.chdir(temp_path)    
    return True

def report_progress(current, max_val): 
    from . import precentage_progress
    precentage_progress.report(current,max_val)

def _enumerate_providers():
    provider_dict = dict()
    for provider in dir(providers):
        if not 'provider_' in provider:
            continue
        provider_name = provider.replace('provider_', '')
        provider_dict[provider_name] = getattr(providers, provider)
    return provider_dict

provider_args = _enumerate_providers()

def _create_argparser():
    p = argparse.ArgumentParser(description='使用帮助',formatter_class=argparse.RawTextHelpFormatter,epilog=arg_epilog)
    g = p.add_argument_group('身份设置 （随方式优先级排序）')
    for arg_key, arg in global_args.items():
        g.add_argument('--%s' % arg_key, **arg)
    # global args
    g = p.add_argument_group('上传设置')
    for arg_key, arg in local_args.items():                
        g.add_argument('--%s' % arg_key, **arg)
    # local args (per source)
    g = p.add_argument_group('--opts 格式 ： [参数1]=[值1];[参数2]=[值2] (query-string)')
    for provider_name, provider in provider_args.items():
        g.add_argument(
            '--%s' % provider_name, 
            metavar='%s-URL' % provider_name.upper(),
            type=str, help='%s\n   参数:%s'%(provider.__desc__,provider.__cfg_help__)
        )
    return p

def sanitize_string(string):
    # limits characters to CJK & ascii chars
    import re
    return re.sub('[^\u0000-\u007F\uac00-\ud7a3\u3040-\u30ff\u4e00-\u9FFF]*','',string) # remove emojis

def truncate_string(string,max):
    # truncate & add ... to string over the length of `max`
    if len(string) > max:string = string[:max-3] + '...'
    return string

def prase_args(args: list):    
    if len(args) < 2:
        parser = _create_argparser()    
        parser.print_help()
        return
    args.pop(0)  # remove filename
    parser = _create_argparser()    
    global_args_dict = dict()
    for k, v in parser.parse_args(args).__dict__.items():
        if k in global_args:
            global_args_dict[k] = v
            if not '--%s' % k in args:continue
            args.pop(args.index('--%s' % k) + 1)
            args.pop(args.index('--%s' % k))
    '''pre-parse : fetch global args,then remove them'''
    local_args_group = []
    current_line = []
    current_provider = ''

    def add(): 
        args = parser.parse_args(current_line).__dict__       
        args['resource'] = args[current_provider]
        local_args_group.append((provider_args[current_provider],args))
    
    for arg in args:
        if arg[2:] in provider_args:
            # a new proivder
            current_provider = arg[2:]
            if current_line:
                # non-empty,add to local group
                add()
                current_line = []
        current_line.append(arg)
    if(current_line):
        add()
    return AttribuitedDict(global_args_dict), AttribuitedDict(local_args_group)
