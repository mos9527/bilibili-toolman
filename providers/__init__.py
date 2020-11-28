'''Content provider modules'''
class DownloadResult:
    video_path : str
    cover_path : str

    title : str = ''
    description : str = ''    
    soruce : str = ''
    def __enter__(self):
        '''Creates a new,empty submission'''
        return DownloadResult()
    def __exit__(self,*args):pass
from . import youtube as provider_youtube