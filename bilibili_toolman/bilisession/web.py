'''bilibili - Web API implmentation'''
from concurrent.futures.thread import ThreadPoolExecutor
from os import stat
from pickle import FALSE
from threading import Thread
from requests import Session
from typing import List, Tuple
from . import logger
import math,time,mimetypes,base64

from .common import JSONResponse , FileIterator, ReprExDict , file_manager , chunk_queue , check_file
from .common.submission import Submission , create_submission_by_arc

class WebUploadChunk(FileIterator):
    url_endpoint : str
    params : dict
    headers : dict    
    session : Session
    
    def upload_via_session(self,session = None):
        for retries in range(1,BiliSession.RETRIES_UPLOAD_ID+1):
            try:
                (session or self.session).put(
                    self.url_endpoint,
                    params=self.params,
                    headers=self.headers,
                    data=self
                )
                return True
            except Exception as e:
                logger.warning('第 %s 次重试时：%s' % (retries,e))

class BiliSession(Session):
    '''哔哩哔哩网页上传 API'''
    BUILD_VER = (2, 8, 12)
    BUILD_NO = int(BUILD_VER[0] * 1e6 + BUILD_VER[1] * 1e4 + BUILD_VER[2] * 1e2)
    BUILD_STR = '.'.join(map(lambda v: str(v), BUILD_VER))
    '''Build variant & version'''
    
    DEFAULT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
    
    UPLOAD_PROFILE = 'ugcupos/bup'    
    UPLOAD_CDN     = 'bda2'

    RETRIES_UPLOAD_ID = 5

    DELAY_FETCH_UPLOAD_ID = .1
    DELAY_RETRY_UPLOAD_ID = 1
    DELAY_VIDEO_SUBMISSION = 30
    DELAY_REPORT_PROGRESS = .5

    WORKERS_UPLOAD = 3

    MISC_MAX_TITLE_LENGTH = 80
    MISC_MAX_DESCRIPTION_LENGTH = 2000

    FORCE_HTTP = False

    def request(self, method: str, url,*a,**k):
        if self.FORCE_HTTP and url[:5] == 'https':
            url='http' + url[5:]                                   
        return super().request(method, url,*a,**k)


    def __init__(self, cookies: str = '') -> None:      
        super().__init__()
        self.LoginViaCookiesQueryString(cookies)
        self.headers['User-Agent'] = self.DEFAULT_UA        
    
    # region Web-client APIs
    def LoginViaCookiesQueryString(self,cookies:str):
        '''设置本 Session 的 Cookies

        Args:
            cookies (str): e.g. SESSDATA=cb0..; bili_jct=6750...
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
        '''个人信息，限网页端使用'''
        return self._self()

    @JSONResponse
    def _upload_status(self, endpoint, name, upload_id, biz_id):
        '''检查网页端上传结果，限网页端使用'''
        return self.post(endpoint, params={
            'output': 'json',
            'profile': self.UPLOAD_PROFILE,
            'name': name,
            'uploadId': upload_id,
            'biz_id': biz_id
        })

    def _list_archives(self,params):
        return self.get('https://member.bilibili.com/x/web/archives',params=params)

    @JSONResponse
    def ListArchives(self,pubing=True,pubed=True,not_pubed=True,pn=1,ps=10):
        '''分页查看已上传的作品,*推荐使用`ListSubmissions`*

        Args:
            pubing (bool, optional): 是否获取*正在审核*的作品. Defaults to True.
            pubed (bool, optional): 是否获取*已发布*的作品. Defaults to True.
            not_pubed (bool, optional): 是否获取*被打回*的作品. Defaults to True.
            pn (int, optional): 页码. Defaults to 1.
            ps (int, optional): 个数. Defaults to 10.

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
    
    @JSONResponse
    def _view_archive(self,bvid):
        return self.get('https://member.bilibili.com/x/web/archive/view',params={'bvid':bvid})
    
    def _edit_archive(self,json : dict):
        return self.post('https://member.bilibili.com/x/vu/web/edit',json=json,params={'csrf': self.cookies.get('bili_jct')})

    @JSONResponse
    def EditSubmission(self,submission : Submission):
        '''编辑作品，适用于重新上传

        Args:
            submission (Submission): 可由 `ViewArchive` 取得

        Returns:
            dict
        '''
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
        })

    def ViewSubmission(self,bvid) -> Submission:
        '''以 BVid 获取作品信息

        Args:
            bvid

        Returns:
            Submission: 作品信息
        '''
        arc = self._view_archive(bvid)['data']
        return create_submission_by_arc(arc)

    def ListSubmissions(self,pubing=True,pubed=True,not_pubed=True,limit=1000) -> List[Submission]:
        '''查看已上传的作品

        Args:
            pubing (bool, optional): 是否获取*正在审核*的作品. Defaults to True.
            pubed (bool, optional): 是否获取*已发布*的作品. Defaults to True.
            not_pubed (bool, optional): 是否获取*被打回*的作品. Defaults to True.
            limit (int, optional): 最多获取量. Defaults to 1000.

        Raises:
            Exception: 被限流时引发

        Returns:
            List[Submission]: 请求到的作品

        注：此 API 无法获取完整作品信息，推荐通过所得BVID以其他API检索
        '''
        args = pubing,pubed,not_pubed
        submissions = []
        count = 0
        def add_to_submissions(arcs):       
            nonlocal count
            for arc in arcs['arc_audits']:
                count += submissions.append(create_submission_by_arc(arc)) or 1
                if count >= limit:return False  
            return True             
        arc = self.ListArchives(*args,pn=1)['data']
        result = add_to_submissions(arc)
        if result:
            for pn in range(2,math.ceil(arc['page']['count'] / arc['page']['ps']) + 1):
                add_to_submissions(self.ListArchives(*args,pn=pn)['data'])
        return submissions

    def _preupload(self, name='a.flv', size=0):        
        return self.get('https://member.bilibili.com/preupload', params={
            'name': name,
            'size': int(size),
            'r': 'upos',
            'profile': self.UPLOAD_PROFILE,
            'ssl': 0,
            'version': self.BUILD_STR,
            'build': self.BUILD_NO,
            'upcdn': self.UPLOAD_CDN,
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
        '''上传视频

        Args:
            path (str): 视频文件路径

        Returns:
            Tuple[str,str]: [远端 URI,biz_id]        
        '''
        path, basename, size = check_file(path)
        def generate_upload_chunks(name, size):
            def fetch_upload_id():
                '''Generating uplaod chunks'''            
                for i in range(1,self.RETRIES_UPLOAD_ID + 1):
                    try:
                        config = self._preupload(name=name, size=size).json()
                        self.headers['X-Upos-Auth'] = config['auth']
                        '''X-Upos-Auth header'''
                        endpoint = 'https:%s/ugcboss/%s' % (config['endpoint'], config['upos_uri'].split('/')[-1])
                        logger.debug('远端结点： %s' % endpoint)
                        logger.debug('第 %s 次刷新 TOKEN...' % i)
                        upload_id = self._upload_id(endpoint).json()['upload_id']
                        return config,endpoint,upload_id
                    except Exception as e:               
                        logger.warning('第 %s 上传未成功,重试...' % i)
                        time.sleep(self.DELAY_RETRY_UPLOAD_ID)            
                return None,None,None
            config,endpoint,upload_id = fetch_upload_id()
            if not upload_id:
                raise Exception("经 %s 次重试后仍无法获取 TOKEN" % self.RETRIES_UPLOAD_ID)
            '''Upload endpoint & keys'''
            chunksize = config['chunk_size']
            chunkcount = math.ceil(size/chunksize)
            file_manager.open(path)
            logger.debug('上传分块: %s' % chunkcount)
            logger.debug('分块大小: %s B' % chunksize)
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
        self._upload_chunks_to_endpoint_blocking(chunks)        
        '''Wait for current upload to finish'''        
        file_manager.close(path)
        state = self._upload_status(endpoint, basename, config['upload_id'], config['biz_id'])
        if(state['OK']==1):
            logger.debug('上传完毕: %s' % ReprExDict(state))
        else:
            raise Exception('上传失败: %s' % ReprExDict(state))
        return endpoint, config['biz_id']
    
    def _upload_cover(self,image_binary : bytes,image_mime : str):
        return self.post('https://member.bilibili.com/x/vu/web/cover/up', data={
            'cover': 'data:{%s};base64,' % image_mime + base64.b64encode(image_binary).decode(),
            'csrf': self.cookies.get('bili_jct')
        })

    @JSONResponse
    def UploadCover(self, path: str):
        '''上传封面'''
        mime = mimetypes.guess_type(path)[0] or 'image/png' # fall back to png
        logger.debug('%s -> %s' % (path,mime))
        content = open(path, 'rb').read()
        logger.debug('上传封面图 (%s B)' % len(content))
        return self._upload_cover(content,mime)

    def sub_submit_submission(self,submission : Submission):
        return self.post("https://member.bilibili.com/x/vu/web/add", json=submission.archive, params={'csrf': self.cookies.get('bili_jct')})

    def SubmitSubmission(self, submission: Submission,seperate_parts=False):
        '''提交作品，适用于初次上传；否则请使用 `EditSubmission`

        Args:
            submission (Submission): 作品
            seperate_parts (bool, optional): 是否将多个子视频单独上传. Defaults to False.        
        '''
        if not seperate_parts:
            logger.debug('准备提交多 P 内容: %s' % submission.title)            
            result = self._submit_submission(submission).json()
            return {'code:':result['code'],'results':[result]}
        else:
            results = []
            codes = 0
            for submission in submission.videos:
                logger.debug('准备提交单 P 内容: %s' % submission.title)
                while True:
                    result = self._submit_submission(submission).json()
                    if result['code'] == 21070:
                        logger.warning('请求受限（限流），准备重试')
                        time.sleep(self.DELAY_VIDEO_SUBMISSION)
                        continue 
                    elif result['code'] != 0:
                        logger.critical('其他错误 (%s): %s - 跳过上传' % (result['code'],result['message']))                        
                        break       
                    else:
                        break             
                codes += result['code'] # we want to see if its 0 or else
                results.append(result)
            return {'code':codes,'results':results}
    # endregion

    # region Pickling
    def __dict__(self):
        return {'cookies':self.cookies,'session':self}
    
    def update(self,state_dict : dict):
        self.cookies = state_dict['cookies']        
    # endregion
