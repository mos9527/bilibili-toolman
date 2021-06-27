import os
from sys import path
from . import DownloadResult
__desc__ = '本地文件'
__cfg_help__ = '''
    cover (str) - 封面图片路径
e.g. --localfile "le videos/" --opts cover="le cover.png" --tags ...'''
options={
    'cover':''
}

def update_config(opt):
    global options
    options = {**options,**opt}

def download_video(res) -> DownloadResult:
    results = DownloadResult()
    if not os.path.isfile(res) and not os.path.isdir(res) or (options['cover'] and os.path.isfile(options['cover'])):
        raise FileNotFoundError
    def append(res):        
        with DownloadResult() as result:        
            result.video_path = res
            result.cover_path = options['cover']            
            result.original = True    
            result.title = os.path.basename(res)
            result.description = '[automated upload of file %s]' % res        
        results.results.append(result)
    if os.path.isfile(res):append(res)
    else:
        for f in os.listdir(res):
            append(os.path.join(res,f))
    results.title = os.path.basename(res)   
    results.description = '[automated upload of file %s]' % res
    return results