'''bilibili - Web API implmentation'''
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Thread
from requests import Session
from typing import List, Tuple
from . import logger
import math,time,mimetypes,base64

from .common import JSONResponse , FileIterator , file_manager , chunk_queue , check_file
from .common.submission import Submission , create_submission_by_arc

class WebUploadChunk(FileIterator):
    url_endpoint : str
    params : dict
    headers : dict    
    session : Session
    
    def upload_via_session(self,session = None):
        (session or self.session).put(
            self.url_endpoint,
            params=self.params,
            headers=self.headers,
            data=self
        )

class BiliSession(Session):
    '''Bilibili Web Upload API Implementation'''
    BUILD_VER = (2, 8, 12)
    BUILD_NO = int(BUILD_VER[0] * 1e6 + BUILD_VER[1] * 1e4 + BUILD_VER[2] * 1e2)
    BUILD_STR = '.'.join(map(lambda v: str(v), BUILD_VER))
    DEFAULT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
    '''Build variant & version'''

    RETRIES_UPLOAD_ID = 5

    DELAY_FETCH_UPLOAD_ID = .1
    DELAY_RETRY_UPLOAD_ID = 1
    DELAY_VIDEO_SUBMISSION = 30
    DELAY_REPORT_PROGRESS = .5

    WORKERS_UPLOAD = 3

    def __init__(self, cookies: str = '') -> None:      
        super().__init__()
        self.LoginViaCookiesQueryString(cookies)
        self.headers['User-Agent'] = self.DEFAULT_UA        
    
    # region Web-client APIs
    def LoginViaCookiesQueryString(self,cookies:str):
        '''Login via cookies from query string - returns the parsing result which

            DOES NOT return the true login state - use `Self` to check.
        '''
        if not cookies: return
        for item in cookies.replace(' ', '').split(';'):
            if '=' in item:
                self.cookies.set(*item.split('=')[:2])
            else:
                self.cookies.set(item,'')
        return True    

    def _self(self):
        return self.get('https://api.bilibili.com/x/web-interface/nav')

    @property
    @JSONResponse
    def Self(self):
        '''Info of current user'''
        return self._self()

    @JSONResponse
    def _upload_status(self, endpoint, name, upload_id, biz_id):
        '''Checks upload status , used by web-uploads only'''
        return self.post(endpoint, params={
            'output': 'json',
            'profile': 'ugcupos/bup',
            'name': name,
            'uploadId': upload_id,
            'biz_id': biz_id
        })

    def _list_archives(self,params):
        return self.get('https://member.bilibili.com/x/web/archives',params=params)

    @JSONResponse
    def ListArchives(self,pubing=True,pubed=True,not_pubed=True,pn=1,ps=10):
        '''Enumerates uploaded videos

        Args:
            pubing (bool, optional): Show PUBLISHING videos?. Defaults to True.
            pubed (bool, optional): Show PUBLISHED videos?. Defaults to True.
            not_pubed (bool, optional): Show FAILED-TO-PUBLISH videos?. Defaults to True.
            pn (int, optional): page-number. Defaults to 1.
            ps (int, optional): number of archives to fetch. Defaults to 10.

        Returns:
            dict
        '''
        return self._list_archives({
            'status':('%s%s%s' % (',is_pubing'*pubing,',pubed'*pubed,',not_pubed'*not_pubed))[1:],
            'pn':pn,
            'ps':ps,
            'interactive':1,
            'coop':1
        })
    
    def _view_archive(self,bvid):
        return self.get('https://member.bilibili.com/x/web/archive/view',params={'bvid':bvid})

    @JSONResponse
    def ViewArchive(self,bvid):
        '''Gather info on speceific video by `bvid`

        Args:
            bvid (str): why,bvid ofc

        Returns:
            dict
        '''
        return self._view_archive(bvid)
    
    def _edit_archive(self,json : dict):
        return self.post('https://member.bilibili.com/x/vu/web/edit',json=json,params={'csrf': self.cookies.get('bili_jct')})

    @JSONResponse
    def EditArchvie(self,submission : Submission):
        '''Editing submission

        Args:
            submission (Submission): A submission Object, its content will override your video sharing its same `aid` property

        Returns:
            dict
        '''
        if not submission.videos:
            logger.warning('No video was defined,using archive videos')
            submission.videos.extend(self.ViewArchive(submission.bvid)['data']['videos'])
        return self._edit_archive({
                "aid": submission.aid,
                "copyright": submission.copyright,
                "videos": submission.videos.archive,
                "source": submission.source,
                "tid": int(submission.thread),
                "cover": submission.cover_url,
                "title": submission.title,
                "tag": ','.join(set(submission.tags)),
                "desc_format_id": 31,
                "desc": submission.description,
                "up_close_reply": submission.close_reply,
                "up_close_danmu": submission.close_danmu,        
        })

    def ListSubmissions(self,pubing=True,pubed=True,not_pubed=True,limit=1000) -> List[Submission]:
        '''Helper function for `ListArchives`,allows one to fetch videos 
        by numeric limit instead of page-numbers & parsing them to `Submission` objects

        Args: refer to `ListArchives` ; `limit` specifies the count of videos to be fetched

        Returns:
            List[Submission]: Selected submissions
        '''
        args = pubing,pubed,not_pubed
        submissions = []
        count = 0
        def add_to_submissions(arcs):       
            nonlocal count
            for arc in arcs['arc_audits']:
                count += submissions.append(create_submission_by_arc(arc)) or 1
                if count >= limit:raise Exception("Hit fetch limit (%s)" % limit)                        
        arc = self.ListArchives(*args,pn=1)['data']
        add_to_submissions(arc)
        for pn in range(2,math.ceil(arc['page']['count'] / arc['page']['ps']) + 1):
            add_to_submissions(self.ListArchives(*args,pn=pn)['data'])
        return submissions

    def _preupload(self, name='a.flv', size=0):        
        return self.get('https://member.bilibili.com/preupload', params={
            'name': name,
            'size': int(size),
            'r': 'upos',
            'profile': 'ugcupos/bup',
            'ssl': 0,
            'version': self.BUILD_STR,
            'build': self.BUILD_NO,
            'upcdn': 'bda2',
            'probe_version': self.BUILD_NO
        })

    def _upload_id(self, endpoint):
        time.sleep(self.DELAY_FETCH_UPLOAD_ID)  # adding delay as the `auth` token needs to be updated server-side
        return self.post(endpoint + '?uploads', params={
            'output': 'json'
        },headers={
            'Origin': 'https://member.bilibili.com',
            'Referer':'https://member.bilibili.com/'
        })    

    def _upload_chunks_to_endpoint_blocking(self,chunk_iter : List[WebUploadChunk]):
        '''consuming all chunks through any means,blocks code until done'''
        for chunk in chunk_iter:chunk_queue.put(chunk)
        executor = ThreadPoolExecutor(max_workers=self.WORKERS_UPLOAD)
        class ConsumerThread(Thread):
            daemon = True
            def run(self) -> None:
                while chunk_queue.unfinished_tasks >= 0:
                    chunk : WebUploadChunk = chunk_queue.get()             
                    future = executor.submit(chunk.upload_via_session)           
                    future.add_done_callback(lambda future:chunk_queue.task_done())
        tConsume = ConsumerThread()
        tConsume.start()
        from . import cli        
        while chunk_queue.unfinished_tasks >= 0:       
            read_all,size_all = 0 , 0
            for v in file_manager.values():
                read_all += v['read'] 
                size_all += v['length']
            cli.report_progress(read_all,size_all)
            if chunk_queue.unfinished_tasks == 0: break
            time.sleep(0.5)
        del tConsume
        return True

    def UploadVideo(self, path: str) -> Tuple[str,int]:
        '''Uploading a video via local path, returing its URL (and CID if available) post-upload
        
        Args:
            path : Local path to video resource

        Returns:
            Endpoint URL (str) , bvid (int) (if applicable)
        '''
        path, basename, size = check_file(path)
        logger.debug('Opened file %s (%s B) for reading' % (basename,size))
        '''Loading files'''
        def generate_upload_chunks(name, size):
            def fetch_upload_id():
                '''Generating uplaod chunks'''            
                for i in range(1,self.RETRIES_UPLOAD_ID + 1):
                    try:
                        config = self._preupload(name=name, size=size).json()
                        self.headers['X-Upos-Auth'] = config['auth']
                        '''X-Upos-Auth header'''
                        endpoint = 'https:%s/ugcboss/%s' % (config['endpoint'], config['upos_uri'].split('/')[-1])
                        logger.debug('Endpoint URL %s' % endpoint)
                        logger.debug('Fetching token (%s)' % i)
                        upload_id = self._upload_id(endpoint).json()['upload_id']
                        return config,endpoint,upload_id
                    except Exception as e:               
                        logger.error('Unable to upload the video as the server has rejected our request,retrying')     
                        time.sleep(self.DELAY_RETRY_UPLOAD_ID)            
                return None,None,None
            config,endpoint,upload_id = fetch_upload_id()
            if not upload_id:
                raise Exception("Unable to fetch upload id in %s tries" % self.RETRIES_UPLOAD_ID)
            '''Upload endpoint & keys'''
            chunksize = config['chunk_size']
            chunkcount = math.ceil(size/chunksize)
            file_manager.open(path) # opens file for reading
            logger.debug('Upload chunks: %s' % chunkcount)
            logger.debug('Upload chunk size: %s' % chunksize)
            def iter_chunks():
                for chunk_n in range(0,chunkcount):   
                    start = chunksize * chunk_n
                    end = min(start + chunksize,size)
                    chunk = WebUploadChunk(path,start,end)
                    chunk.url_endpoint = endpoint
                    chunk.session = self
                    chunk.params = {
                        'partNumber': chunk_n + 1,
                        'uploadId': upload_id,
                        'chunk': chunk_n,
                        'chunks': chunkcount,
                        'start': start,
                        'end': end,
                        'total': size
                    }
                    chunk.headers = {
                        'X-Upos-Auth': config['auth']
                    }
                    yield chunk            
            config['upload_id'] = upload_id
            return endpoint, config, iter_chunks()
        endpoint, config, chunks = generate_upload_chunks(basename, size)
        '''Generates upload config'''
        logger.debug('Waiting for uploads to finish')
        self._upload_chunks_to_endpoint_blocking(chunks)        
        '''Wait for current upload to finish'''        
        file_manager.close(path)
        state = self._upload_status(endpoint, basename, config['upload_id'], config['biz_id'])
        if(state['OK']==1):
            logger.debug('Successfully finished uploading' )
        else:
            raise Exception('Failed to upload target video (ret:%s)' % state)
        return endpoint, config['biz_id']
    
    def _upload_cover(self,image_binary : bytes,image_mime : str):
        return self.post('https://member.bilibili.com/x/vu/web/cover/up', data={
            'cover': 'data:{%s};base64,' % image_mime + base64.b64encode(image_binary).decode(),
            'csrf': self.cookies.get('bili_jct')
        })

    @JSONResponse
    def UploadCover(self, path: str):
        '''Uploading a cover via local path

        Args:
            path (str): Local path for cover image

        Returns:
            dict
        '''
        mime = mimetypes.guess_type(path)[0] or 'image/png' # fall back to png
        logger.debug('Guessed mime type for %s as %s' % (path,mime))
        content = open(path, 'rb').read()
        logger.debug('Uploading cover image (%s B)' % len(content))
        return self._upload_cover(content,mime)

    def _submit_submission(self,submission : Submission):
        return self.post("https://member.bilibili.com/x/vu/web/add", json=submission.archive, params={'csrf': self.cookies.get('bili_jct')})

    def SubmitSubmission(self, submission: Submission,seperate_parts=False):
        '''Submitting a submission. May contain many sub-submissions in `submission.videos`

        Args:
            submission (Submission): A Submission object

        Returns:
            dict
        '''
        if not seperate_parts:
            logger.debug('Posting multi-part submission %s' % submission.title)            
            result = self._submit_submission(submission).json()
            return {'code:':result['code'],'results':[result]}
        else:
            results = []
            code_accumlation = 0
            logger.warning('Posting multipule submissions')
            for submission in submission.videos:
                logger.debug('Posting single submission `%s`' % submission.title)
                while True:
                    result = self._submit_submission(submission).json()
                    if result['code'] == 21070:
                        logger.warning('Hit anti-spamming measures (%s),retrying' % result['code'])
                        time.sleep(self.DELAY_VIDEO_SUBMISSION)
                        continue 
                    elif result['code'] != 0:
                        logger.error('Error (%s): %s - skipping' % (result['code'],result['message']))
                        logger.error('Video title: %s' % submission.title)
                        logger.error('Video description:\n%s' % submission.description)
                        break       
                    else:
                        break             
                code_accumlation += result['code']             
                results.append(result)
            return {'code':code_accumlation,'results':results}
    # endregion

    # region Pickling
    def __dict__(self):
        return {'cookies':self.cookies,'session':self}
    
    def update(self,state_dict : dict):
        self.cookies = state_dict['cookies']        
    # endregion
