'''basic submission tree model impl'''
from re import sub


class SubmissionVideos(list):
    '''Parent submission'''
    def extend(self, __iterable) -> None:
        for item in __iterable:
            self.append(item)

    def append(self, video) -> None:
        '''Only Submission will be appended to our list'''
        if isinstance(video,dict):
            # try to interpert it as a list of dictionaries sent by server            
            with Submission() as submission:                
                submission.video_endpoint = video['filename']
                submission.video_duration = video['duration']
                submission.title = video['title']            
                submission.bvid = video['bvid']
                submission.biz_id = video['cid']
                submission.aid = video['aid']
                submission.stat = video
                submission.parent = self
            return super().append(submission)            
        elif isinstance(video,Submission):
            return super().append(video)
        else:
            raise Exception("Either a dict or a Submission object can be supplied.")
            
    @property
    def archive(self):
        '''Dumps current videos as archvies that's to be the payload'''
        target = self if self else [self.parent] # fallback to parent node
        return [{
            "filename": video.video_endpoint,
            "title": video.title,
            "desc": video.description,
        } for video in target]

    def __init__(self,parent=None):
        '''Initializes the list
        
            parent : Submission - Used as fallback value when theres no subvideos
        '''
        self.parent = parent
        super().__init__()

class Submission:
    '''Submission meta set'''
    COPYRIGHT_SELF_MADE = 1
    COPYRIGHT_REUPLOAD = 2
    '''Copyright consts'''
    close_reply: bool = False
    close_danmu: bool = False
    '''Access control parameters'''    
    _description: str = ''
    @property
    def description(self):
        return self._description
    @description.setter
    def description(self,v):
        self._description = v or '' # fallback
    '''Description for the video'''
    title: str = ''
    '''Title for the submission'''
    copyright: int = COPYRIGHT_REUPLOAD
    '''Copyright type'''
    source: str = ''
    '''Reupload source'''    
    thread: int = 19
    '''Thread ID'''
    tags: list = None
    '''Tags of video'''
    videos: SubmissionVideos = None
    '''List of videos in submission'''
    _cover_url = ''        
    @property
    def cover_url(self):
        '''Cover image URL'''
        return self._cover_url
    @cover_url.setter
    def cover_url(self,value):
        # note : this will strip the HTTP prefix        
        if value:self._cover_url = '//' + value.split('//')[-1]         
    # region Per video attributes    
    _video_filename = ''
    @property
    def video_endpoint(self):
        '''Endpoint name'''
        return self._video_filename
    @video_endpoint.setter
    def video_endpoint(self,value):
        # note : this will strip the HTTP prefix        
        self._video_filename = value.split('/')[-1].split('.')[0]    
    biz_id = 0
    '''a.k.a cid.for web apis'''        
    bvid = ''
    '''the new video ID'''
    aid = 0
    '''another ID for web apis'''
    thread_name = ''
    '''upload thread name i.e. typename'''
    parent_tname = ''
    '''parent thread name'''
    stat = None
    '''viewer status'''
    reject_reason = ''
    '''rejection'''
    state = 0
    '''status of video'''
    state_desc = ''
    '''status but human readable'''
    video_duration = 0
    '''duration of video'''
    _parent = None
    @property
    def parent(self):
        self._parent : Submission
        return self._parent
    @parent.setter
    def parent(self,v):
        self._parent = v
    '''parent object. used for videos property'''
    # endregion
    def __init__(self) -> None:
        self.tags = [] # creates new instance for mutables
        self.videos = SubmissionVideos(self)
    def __enter__(self):
        '''Creates a new,empty submission'''
        return Submission()
    def __exit__(self,*args):pass
    @property
    def archive(self):
        '''returns a dict containing all our info'''
        kv_pair = {
            "copyright": self.copyright,
            "videos": self.videos.archive,
            "source": self.source,
            "tid": int(self.thread),            
            "title": self.title,
            "tag": ','.join(set(self.tags)),
            # "desc_format_id": 31,
            "desc": self.description,
            # "up_close_reply": self.close_reply,
            # "up_close_danmu": self.close_danmu
        }        
        if self.cover_url:
            kv_pair = {**kv_pair,"cover": self.cover_url}
        return kv_pair
    def __repr__(self) -> str:
        return '< bvid : "%s" , title : "%s", desc : "%s" , video_endpoint : "%s" >' % (self.bvid,self.title,self.description,self.video_endpoint)
def create_submission_by_arc(arc : dict):
    '''Generates a `Submission` object via a `arc` dict'''
    with Submission() as submission:
        submission.stat = arc['stat'] if 'stat' in arc else arc['archive']
        submission.aid = submission.stat['aid']        
        if 'parent_tname' in arc: # Web version only
            submission.parent_tname = arc['parent_tname']
            submission.thread_name = arc['typename']
        if 'Archive' in arc:
            arc['archive'] = arc['Archive']                
        submission.copyright = arc['archive']['copyright']
        submission.bvid = arc['archive']['bvid']
        submission.title = arc['archive']['title']
        submission.cover_url = arc['archive']['cover']
        submission.tags = arc['archive']['tag'].split(',')
        submission.description = arc['archive']['desc']
        submission.source = arc['archive']['source']
        submission.state_desc = arc['archive']['state_desc']
        submission.state = arc['archive']['state']
        submission.reject_reason = arc['archive']['reject_reason']  
        if 'Videos' in arc:
            arc['videos'] = arc['Videos']
        submission.videos.extend(arc['videos'])
    return submission
