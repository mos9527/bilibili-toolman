# -*- coding: utf-8 -*-
'''Content provider modules'''
from typing import List


class DownloadResult:
    video_path : str = ''
    cover_path : str = ''

    title : str = ''
    description : str = ''    
    soruce : str = ''

    original : bool = False # now this really is just a placeholder
    results = None

    extra = dict() # BAD MOVE! though this SHOULD be overwritten and not accessed

    @property
    def results(self):
        '''A list of sub download results'''
        self._results : List[DownloadResult] # hack to allow typing of ourself
        return self._results    
    
    def __init__(self) -> None:
        self._results = []

    def __enter__(self):        
        return DownloadResult()
    def __exit__(self,*args):pass
from . import youtube as provider_youtube
from . import localfile as provider_localfile