# -*- coding: utf-8 -*-
'''Content provider modules'''
from typing import List


class DownloadResult:
    video_path : str = ''
    cover_path : str = ''

    title : str = ''
    description : str = ''    
    soruce : str = ''
    
    results = None

    extra = dict()

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

    def __repr__(self) -> str:
        return '< title : %s , src : %s>' % (self.title,self.soruce)
from . import youtube as provider_youtube
from . import localfile as provider_localfile