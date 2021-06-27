'''Content provider modules'''
class DownloadResult:
    video_path : str = ''
    cover_path : str = ''

    title : str = ''
    description : str = ''    
    soruce : str = ''

    original : bool = False

    results = None
    '''A list of DownloadResult'''
    def __init__(self) -> None:
        self.results = []
    def __enter__(self):
        '''Creates a new,empty submission'''
        return DownloadResult()
    def __exit__(self,*args):pass
from . import youtube as provider_youtube
from . import localfile as provider_localfile