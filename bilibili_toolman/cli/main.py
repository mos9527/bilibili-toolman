# -*- coding: utf-8 -*-
# region Setup
from ..bilisession import logger
from ..bilisession.common.submission import Submission
from ..providers import DownloadResult
from . import AttribuitedDict,setup_logging,prepare_temp,prase_args,sanitize,truncate,local_args as largs
import pickle,logging,sys,urllib.parse

TEMP_PATH = 'temp'
sess = None

def download_sources(provider,arg) -> DownloadResult:
    resource = arg.resource
    opts = arg.opts
    try:
        opts = urllib.parse.parse_qs(opts,keep_blank_values=True)
        provider.update_config({k:v[-1] for k,v in opts.items()})
    except:opts = '无效选项'
    '''Passing options'''
    logger.info('下载源视频')
    logger.info('  - Type: %s - %s' % (provider.__name__,provider.__desc__))
    logger.info('  - URI : %s' % resource)    
    '''Downloading source'''
    try:
        return provider.download_video(resource)
    except Exception as e:
        logger.error('无法下载指定资源 - %s' % e)
        return        

def upload_sources(sources : DownloadResult,arg):
    '''To perform a indivudial task

    If multiple videos are given by the provider,the submission will be in multi-parts (P)
    Otherwise,only the given video is uploaded as a single part subject

    Args:

        provider - one of the modules of `providers`
        arg - task arguments dictionary    
            * resource - resoucre URI (must have)
            - opts     - options for uploader in query string e.g. format=best            
            - See `utils.local_args` for more arguments,along with thier details        
    '''    
    submission = Submission()    
    if not sources:return None,True
    logging.info('上传资源数：%s' % len(sources.results))    
    for source in sources.results:       
        '''If one or multipule sources'''        
        blocks      = {'title':source.title,'desc':source.description,**source.extra} # for formatting
        title       = truncate(sanitize(arg.title.format_map(blocks)),sess.MISC_MAX_TITLE_LENGTH)   
        description = truncate(sanitize(arg.desc .format_map(blocks)),sess.MISC_MAX_DESCRIPTION_LENGTH)        
        logger.info('准备上传: %s' % title)
        '''Summary trimming'''
        try:
            endpoint, bid = sess.UploadVideo(source.video_path)
            cover_url = sess.UploadCover(source.cover_path)['data']['url'] if source.cover_path else ''
        except Exception as e:
            logger.critical('上传失败! - %s' % e)
            return [],True
        if not endpoint:
            logger.critical('URI 获取失败!')
            return [],True
        logger.info('资源已上传')
        from bilibili_toolman.cli import precentage_progress
        precentage_progress.close()
        with Submission() as video:
            '''Creatating a video per submission'''
            video.cover_url = cover_url
            video.video_endpoint = endpoint
            video.biz_id = bid
            '''Sources identifiers'''   
            if not arg.original:
                video.copyright = Submission.COPYRIGHT_REUPLOAD
                video.source = sources.soruce         
            else:
                video.copyright = Submission.COPYRIGHT_ORIGINAL
                video.source = ''
            video.thread = arg.thread_id
            video.tags = arg.tags.format_map(blocks).split(',')
            video.description = description
            video.title = title # This shows up as title per-part, invisible if video is single-part only
        '''Use the last given thread,tags,cover & description per multiple uploads'''                           
        submission.copyright = video.copyright or submission.copyright
        submission.thread = video.thread or submission.thread        
        submission.tags.extend(video.tags)
        submission.videos.append(video) # to the main submission
    '''Filling submission info'''        
    submission.source = sources.soruce
    submission.title = title # This shows up as the main title of the submission
    submission.description = description # This is the only description that gets shown
    '''Upload cover images for all our submissions as well'''
    cover_url = sess.UploadCover(sources.cover_path)['data']['url'] if sources.cover_path else ''
    submission.cover_url = cover_url
    '''Finally submitting the video'''
    submit_result=sess.SubmitSubmission(submission,seperate_parts=arg.seperate_parts)  
    dirty = False
    for result in submit_result['results']:
        if result['code'] == 0:logger.info('上传成功 - BVid: %s' % result['data']['bvid'])        
        else:
            logger.warning('%s 上传失败 : %s' % (submission,result['message']))
            dirty = True
    return submit_result,dirty

global_args,local_args = None,None

def setup_session():
    '''Setup session with cookies in query strings & setup temp root'''
    global sess    
    if global_args.username and global_args.pwd:
        from ..bilisession.client import BiliSession
        sess = BiliSession() 
        sess.FORCE_HTTP = global_args.http           
        result = sess.LoginViaUsername(global_args.username,global_args.pwd)        
        logger.warning('MID:%s' % sess.mid)
        return result
    elif global_args.cookies:
        from ..bilisession.web import BiliSession
        sess = BiliSession()
        sess.FORCE_HTTP = global_args.http
        sess.LoginViaCookiesQueryString(global_args.cookies)
        self_ = sess.Self
        if not 'uname' in self_['data']:
            logger.error('Cookies无效: %s' % self_['message'])        
            return False
        logger.warning('ID:%s' % self_['data']['uname'])
        for arg in local_args:
            arg['seperate_parts'] = True
        logger.warning('Web端 API 无法进行多 P 上传！多P项目将被分为多个视频')  
        return True
    elif global_args.load:    
        unpickled = pickle.loads(open(global_args.load,'rb').read())
        sess = unpickled['session']
        sess.update(unpickled)
        sess.FORCE_HTTP = global_args.http
        logger.info('加载之前的登陆态')
        return True
    else:
        logger.error('缺失认证信息')
        return False

def __main__():
    global global_args,local_args
    setup_logging()
    global_args,local_args = prase_args(sys.argv)
    '''Parsing args'''
    if not setup_session():
        logging.fatal('登陆失败！')
        sys.exit(2)    
    else:         
        if global_args.http:
            logger.warning('强制使用 HTTP')
        if sess.DEFAULT_UA: # specifiy CDN whilst using WEB apis
            bup = ['ws','qn','bda2']
            bupfetch = ['kodo','gcs','bos']
            if global_args.cdn in bup:
                sess.UPLOAD_PROFILE = 'ugcupos/bup'                                
            elif global_args.cdn in bupfetch:
                sess.UPLOAD_PROFILE = 'ugcupos/bupfetch'
            sess.UPLOAD_CDN     = global_args.cdn
            logger.info('CDN ： %s [%s]' % (sess.UPLOAD_CDN,sess.UPLOAD_PROFILE))            
        logger.info('使用 %s API' % ('Web端' if sess.DEFAULT_UA else 'PC端'))        
        if global_args.save:
            logging.warning('保存登陆态到： %s' % global_args.save)
            open(global_args.save,'wb').write(pickle.dumps(sess.__dict__()))            
            sys.exit(0)
        prepare_temp(TEMP_PATH)
        # Output current settings        
        logging.info('任务总数: %s' % len(local_args))        
        success,failure = [],[]
        fmt = lambda s: ('×','√')[s] if type(s) is bool else s
        for provider,arg_ in local_args:
            arg = AttribuitedDict(arg_)
            logger.info('任务信息：')
            for k,v in largs.items():
                logger.info('  - %s : %s' % (list(v.values())[0].split()[0],fmt(arg[k])))
            sources = download_sources(provider,arg)                   
            if arg.no_upload:
                logger.warn('已跳过上传')
            else:
                result,dirty = upload_sources(sources,arg)
                if not dirty:success.append((arg,result))
                else: failure.append((arg,None))
        if not failure:sys.exit(0)
        logging.warning('上传未完毕')
        sys.exit(1)