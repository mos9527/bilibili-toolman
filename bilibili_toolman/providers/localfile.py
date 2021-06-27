import os
from sys import path
from . import DownloadResult
__desc__ = '本地文件'
__cfg_help__ = '''
    cover (str) - 封面图片路径    
e.g. --localfile "le video.mp4" --opts cover="le cover.png" --tags ...'''
options={
    'cover':''
}

def update_config(opt):
    global options
    options = {**options,**opt}

def download_video(res) -> DownloadResult:
    results = DownloadResult()
    if not os.path.isfile(res) or (options['cover'] and os.path.isfile(options['cover'])):
        raise FileNotFoundError
    with DownloadResult() as result:        
        result.video_path = res
        result.cover_path = options['cover']            
        result.original = True    
        result.title = os.path.basename(res)            
        result.description = '[automated upload of file %s]' % res        
    results.results.append(result)
    return results