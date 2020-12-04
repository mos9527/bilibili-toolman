'''Bilibili video submission & other APIs'''
import os
from queue import Queue
from re import split
from threading import Lock
from requests import Session
from io import IOBase
import json
import logging
import math
import threading
import time
import mimetypes
import base64

BUILD_VER = (2, 8, 12)
BUILD_NO = int(BUILD_VER[0] * 1e6 + BUILD_VER[1] * 1e4 + BUILD_VER[2] * 1e2)
BUILD_STR = '.'.join(map(lambda v: str(v), BUILD_VER))
'''Build variant & version'''

RETRIES_UPLOAD_ID = 3

DELAY_FETCH_UPLOAD_ID = .1
DELAY_RETRY_UPLOAD_ID = 1
DELAY_VIDEO_SUBMISSION = 30
DELAY_REPORT_PROGRESS = .5

WORKERS_UPLOAD = 3

def JSONResponse(classfunc):
    '''Decodes `Response`s content to JSON'''
    def wrapper(session: Session, *args, **kwargs):
        response = classfunc(session, *args, **kwargs)
        decoded = json.loads(response.text)
        return decoded
    return wrapper

class FileManager(dict):
    '''Lockfull IO manager'''

    def __init__(self) -> None:
        super().__init__()
        self.lock = Lock()

    def open(self, path):
        self.lock.acquire()  # preventing multipule instances from accessing all at once
        if not path in self or self[path]['stream'].closed:
            self[path] = {'stream': open(path, 'rb'), 'read': 0, 'length': os.stat(path).st_size}
        self.lock.release()

    def close(self, path):
        stream: IOBase = self[path]['stream']
        stream.close()
        del self[path]

    def read(self, path, start, end):
        if not path in self:
            self.open(path)  # open for new IO handler
        stream: IOBase = self[path]['stream']
        self.lock.acquire()  # same as open
        stream.seek(start)
        length = end - start
        self[path]['read'] += length
        self.lock.release()
        return stream.read(length)

    def create_iterator(self, path, start, end):
        return FileIterator(self, path, start, end)

class FileIterator():
    '''To help aid `requests` intergrate with `FileManager`'''
    CHUNK_SIZE = 2**16

    def __init__(self, fm: FileManager, path, start, end) -> None:
        self.fm, self.path, self.start, self.end = fm, path, start, end

    def __iter__(self):
        start = self.start
        for start in range(self.start, self.end, FileIterator.CHUNK_SIZE):
            yield self.fm.read(self.path, start, min(self.end, start + FileIterator.CHUNK_SIZE))
        if start + FileIterator.CHUNK_SIZE < self.end:
            yield self.fm.read(self.path, start, self.end)

    def __len__(self):
        return self.end - self.start

file_manager = FileManager()

class BiliUploadWorker(threading.Thread):
    '''Upload workers'''
    daemon = True

    def __init__(self, queue, name) -> None:
        super().__init__()
        self.name = name
        self.queue: Queue = queue

    def run(self) -> None:
        '''Fetches new tasks as we run'''
        while True:
            task = self.queue.get()  # blocking
            self.execute(task)
            self.queue.task_done()  # assigns our task has been completed

    def execute(self, task):
        sess, path, endpoint, chunk, config = task
        sess.put(endpoint, params=chunk, headers={
                 'X-Upos-Auth': config['auth']}, 
                 data=file_manager.create_iterator(path, chunk['start'], chunk['end'])
        )

class ThreadedWorkQueue(Queue):
    '''Essential Thread pool / queue'''

    def __init__(self, worker_class, worker_count=WORKERS_UPLOAD) -> None:
        super().__init__()
        self.worker_count = worker_count
        self.workers = [worker_class(self, name='Worker-%s' % i)
                        for i in range(0, worker_count)]

    def run(self):
        '''Start up all the workers'''
        for worker in self.workers:
            worker.start()

    def new_task(self, task):
        '''Assgins new task to queue'''
        self.put(task)

queue = ThreadedWorkQueue(BiliUploadWorker)
queue.run() # start congesting once module is loaded

class Submission:
    '''Submission meta set'''
    COPYRIGHT_SELF_MADE = 1
    COPYRIGHT_REUPLOAD = 2
    '''Copyright consts'''
    close_reply: bool = False
    close_danmu: bool = False
    '''Access control parameters'''
    description: str = ''
    '''Description for the video'''
    title: str = ''
    '''Title for the submission'''
    copyright: int = 0
    '''Copyright type'''
    source: str = ''
    '''Reupload source'''    
    thread: int = 19
    '''Thread ID'''
    submissions: list = None
    '''Sub-submissions'''
    tags: list = None
    '''Tags of video'''
    def __init__(self) -> None:
        self.tags = []
        self.submissions = []
        # prevents mutable objects not being private per instance
    _video_filename = ''
    @property
    def video_endpoint(self):
        '''Endpoint name'''
        return self._video_filename
    @video_endpoint.setter
    def video_endpoint(self,value):
        # note : this will strip the HTTP prefix        
        self._video_filename = value.split('/')[-1].split('.')[0]    
    _cover_url = ''        
    @property
    def cover_url(self):
        '''Cover image URL'''
        return self._cover_url
    @cover_url.setter
    def cover_url(self,value):
        # note : this will strip the HTTP prefix        
        self._cover_url = '//' + value.split('//')[-1]    
    biz_id = 0
    '''a.k.a cid'''        
    def __dict__(self):
        return {
            "filename": self.video_endpoint,
            "title": self.title,
            "desc": self.description,
            "cid": self.biz_id,
        }
    def __enter__(self):
        '''Creates a new,empty submission'''
        return Submission()
    def __exit__(self,*args):pass

class BiliSession(Session):
    '''BiliSession - see BiliSession() for more info'''

    def __init__(self, cookies: str = '') -> None:
        '''BiliSession

        Args:
            cookies (str): Your login cookies,which must contain at least `SESSDATA` & `bili_jct`

        Cookies:
            Many ways are available for you to fetch,however,using Selenium is usually the perfered choice

            Another route would be going through Application tab in DevTools and find your cookies there

            AFAIK,The exipration period is ususally 1 year

            e.g.
                `cookies=SESSDATA=cb06a231%FFFFFFFFFF%2C29187*81; bili_jct=675017fffffffffffc76fda177052`
        '''
        super().__init__()
        self.load_cookies(cookies)
        self.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
        self.logger = logging.getLogger('BiliSession')
    
    def load_cookies(self,cookies:str):
        '''Load cookies from query string'''
        if not cookies: return
        for item in cookies.replace(' ', '').split(';'):
            if '=' in item:
                self.cookies.set(*item.split('='))
            else:
                self.cookies.set(item,'')
        return True
    
    @property
    @JSONResponse
    def Self(self):
        '''Info of current user'''
        return self.get('https://api.bilibili.com/x/web-interface/nav')

    @JSONResponse
    def Preupload(self, name='a.flv', size=0):
        '''Acquire remote upload config'''
        return self.get('https://member.bilibili.com/preupload', params={
            'name': name,
            'size': int(size),
            'r': 'upos',
            'profile': 'ugcupos/bup',
            'ssl': 0,
            'version': BUILD_STR,
            'build': BUILD_NO,
            'upcdn': 'bda2',
            'probe_version': BUILD_NO
        })

    @JSONResponse
    def UploadId(self, endpoint):
        '''Fetch upload ID'''
        time.sleep(DELAY_FETCH_UPLOAD_ID)  # adding delay as the `auth` token needs to be updated server-side
        return self.post(endpoint + '?uploads', params={
            'output': 'json'
        },headers={
            'Origin': 'https://member.bilibili.com',
            'Referer':'https://member.bilibili.com/'
        })

    @JSONResponse
    def UploadStatus(self, endpoint, name, upload_id, biz_id):
        '''Check upload status'''
        return self.post(endpoint, params={
            'output': 'json',
            'profile': 'ugcupos/bup',
            'name': name,
            'uploadId': upload_id,
            'biz_id': biz_id
        })

    def UploadVideo(self, path: str ,report=lambda current,max:None):
        '''Uploading a video via local path

        Args:
            path (str): Local path of video
            report : A function takes (current,max) to show progress of the upload
        
        Returns:
            File basename,File size,Upload Endpoint,Remote Config,Upload Status
        '''
        def load_file(path):
            size = os.stat(path).st_size
            return path, os.path.basename(path), size
        path, basename, size = load_file(path)
        self.logger.debug('Opened file %s (%s B) for reading' % (basename,size))
        '''Loading files'''
        def generate_upload_chunks(name, size):
            def fetch_upload_id():
                '''Generating uplaod chunks'''            
                for i in range(1,RETRIES_UPLOAD_ID + 1):
                    try:
                        config = self.Preupload(name=name, size=size)
                        self.headers['X-Upos-Auth'] = config['auth']
                        '''X-Upos-Auth header'''
                        endpoint = 'https:%s/ugcboss/%s' % (config['endpoint'], config['upos_uri'].split('/')[-1])
                        self.logger.debug('Endpoint URL %s' % endpoint)
                        self.logger.debug('Fetching token (%s)' % i)
                        upload_id = self.UploadId(endpoint)['upload_id']
                        return config,endpoint,upload_id
                    except Exception as e:               
                        self.logger.error('Unable to upload the video as the server has rejected our request,retrying')     
                        time.sleep(DELAY_RETRY_UPLOAD_ID)            
                return None,None,None
            config,endpoint,upload_id = fetch_upload_id()
            if not upload_id:
                raise Exception("Unable to fetch upload id in %s tries" % RETRIES_UPLOAD_ID)
            '''Upload endpoint & keys'''
            chunks = []
            chunksize = config['chunk_size']
            chunkcount = math.ceil(size/chunksize)
            start, end, chunk = 0, chunksize, 0
            self.logger.debug('Upload chunks: %s' % chunkcount)
            self.logger.debug('Upload chunk size: %s' % chunksize)
            self.logger.debug('Upload threads: %s' % queue.worker_count)
            def append():
                chunks.append({
                    'partNumber': chunk + 1,
                    'uploadId': upload_id,
                    'chunk': chunk,
                    'chunks': chunkcount,
                    'start': start,
                    'end': end,
                    'total': size
                })
            while (end < size):
                append()
                start = end
                end += chunksize
                chunk += 1
            if (end != size):
                end = size
                append()
            config['upload_id'] = upload_id
            return endpoint, config, chunks
        endpoint, config, chunks = generate_upload_chunks(basename, size)
        '''Generates upload config'''
        file_manager.open(path) # opens file for reading
        for chunk in chunks:
            queue.new_task((
                self,
                path,
                endpoint,
                chunk,
                config
            ))
        '''Assigns job'''
        self.logger.debug('Waiting for uploads to finish')
        while (queue.unfinished_tasks > 0):                                        
            report(file_manager[path]['read'],size)
            time.sleep(DELAY_REPORT_PROGRESS)
        '''Wait for current upload to finish'''        
        file_manager.close(path)
        state = self.UploadStatus(endpoint, basename, config['upload_id'], config['biz_id'])
        if(state['OK']==1):
            self.logger.debug('Successfully finished uploading' )
        else:
            raise Exception('Failed to upload target video (ret:%s)' % state)
        return basename, size, endpoint, config, state

    @JSONResponse
    def UploadCover(self, path: str):
        '''Uploading a cover via local path

        Args:
            path (str): Local path for cover image

        Returns:
            dict
        '''
        mime = mimetypes.guess_type(path)[0] or 'image/png' # fall back to png
        self.logger.debug('Guessed mime type for %s as %s' % (path,mime))
        content = base64.b64encode(open(path, 'rb').read()).decode()
        self.logger.debug('Uploaded cover image (%s B)' % len(content))
        return self.post('https://member.bilibili.com/x/vu/web/cover/up', data={
            'cover': 'data:{%s};base64,' % mime + content,
            'csrf': self.cookies.get('bili_jct')
        })

    def SubmitVideo(self, submission: Submission,seperate_parts=False):
        '''Submitting a video

        Args:
            submission (Submission): Submission object

        Returns:
            dict
        '''
        @JSONResponse
        def upload_one(submission,single=False):
            payload = {
                "copyright": submission.copyright,
                "videos": [ sub.__dict__() for sub in submission.submissions ] if not single else [ submission.__dict__() ],
                "source": submission.source,
                "tid": int(submission.thread),
                "cover": submission.cover_url,
                "title": submission.title,
                "tag": ','.join(set(submission.tags)),
                "desc_format_id": 31,
                "desc": submission.description,
                "up_close_reply": submission.close_reply,
                "up_close_danmu": submission.close_danmu
            }        
            return self.post("https://member.bilibili.com/x/vu/web/add", data=json.dumps(payload), params={'csrf': self.cookies.get('bili_jct')})
        if not seperate_parts:
            self.logger.debug('Posting multi-part submission `%s`' % submission.title)            
            result = upload_one(submission)            
            return {'code:':result['code'],'results':[result]}
        else:
            results = []
            code_accumlation = 0
            self.logger.warning('Posting multipule submissions')
            for submission in submission.submissions:
                self.logger.debug('Posting single submission `%s`' % submission.title)
                while True:
                    result = upload_one(submission,single=True)
                    if result['code'] == 21070:
                        self.logger.warning('Hit anti-spamming measures (%s),retrying' % result['code'])
                        time.sleep(DELAY_VIDEO_SUBMISSION)
                        continue 
                    elif result['code'] != 0:
                        self.logger.error('Error (%s): %s - skipping' % (result['code'],result['message']))
                        self.logger.error('Video title: %s' % submission.title)
                        self.logger.error('Video description:\n%s' % submission.description)
                        break                    
                code_accumlation += result['code']             
                results.append(result)
            return {'code':code_accumlation,'results':results}
        
