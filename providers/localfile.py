import os
from . import DownloadResult
__desc__ = '本地文件'
options={
    'cover':''
}

def update_config(opt):
    global options
    options = {**options,**opt}

def download_video(res) -> DownloadResult:
    if not os.path.isfile(res) or (options['cover'] and not os.path.isfile(options['cover'])):
        raise FileNotFoundError
    with DownloadResult() as result:        
        result.video_path = res
        result.cover_path = options['cover']            
        result.original = True                
    return result