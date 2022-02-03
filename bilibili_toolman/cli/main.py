# -*- coding: utf-8 -*-
# region Setup
from bilibili_toolman.bilisession.common import LoginException
from ..bilisession.web import BiliSession
from ..bilisession import logger
from ..bilisession.common.submission import Submission
from ..providers import DownloadResult
from . import AttribuitedDict,setup_logging,prepare_temp,prase_args,sanitize,truncate,local_args as largs
import base64,logging,sys,urllib.parse

TEMP_PATH = 'temp'
sess : BiliSession

def download_sources(provider,arg) -> DownloadResult:
    resource = arg.resource
    opts = arg.opts
    try:
        opts = urllib.parse.parse_qs(opts,keep_blank_values=True)
        provider.update_config({k:v[-1].replace(';','') for k,v in opts.items()}) # shouldnt you use & anyways?
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
            logger.critical('%s 上传失败! - %s - 跳过' % (source,e))            
            continue
        if not endpoint:
            logger.critical('URI 获取失败 - 跳过')
            continue
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
        submission.thread = video.thread or submission.thread        
        submission.tags.extend(video.tags)
        submission.videos.append(video) # to the main submission
    '''Filling submission info'''        
    submission.copyright = submission.COPYRIGHT_REUPLOAD if not arg.original else submission.COPYRIGHT_ORIGINAL
    submission.no_reprint = submission.REPRINT_ALLOWED if not arg.no_reprint else submission.REPRINT_DISALLOWED
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
    if global_args.cookies:
        from ..bilisession.web import BiliSession
        sess = BiliSession()
        sess.FORCE_HTTP = global_args.http
        sess.LoginViaCookiesQueryString(global_args.cookies)
        self_ = sess.Self
        if not 'uname' in self_['data']:
            logger.error('Cookies无效: %s' % self_['message'])        
            return False        
        # for task,arg in local_args:
        #     arg['seperate_parts'] = True
        logger.warning('Web端 API 需 Lv3+ 及 1000+ 关注量才可多 P 上传，若出错请悉知')
        return True
    elif global_args.sms:
        from ..bilisession.client import BiliSession
        sess = BiliSession()
        logger.warning('短信验证码有日发送条数限制（5 条），无论验证成败，超限后将无法发送验证码')
        logger.warning('建议使用 --save 保存验证凭据，再次使用则利用 --load 读取，而不需再次登陆')
        logger.info('准备登陆，输入手机号后，按Enter发送验证码')
        phone = input()                
        sess.RenewSMSCaptcha(phone)
        logger.debug('验证码已发送')
        for i in range(0,5):
            logger.info('输入验证码:')
            captcha=input() 
            try:
                sess.LoginViaSMSCaptcha(phone,captcha)                
                return True                
            except LoginException as e:
                logger.error('验证码无效，请重试：%s' % e)                
        return False
        pass
    elif global_args.load:    
        from ..bilisession.web import BiliSession
        sess = BiliSession.from_bytes(base64.b64decode(global_args.load))
        sess.FORCE_HTTP = global_args.http
        logger.info('加载之前的登陆凭据')
        return True
    else:
        logger.error('缺失认证信息')
        return False

def __main__():
    global global_args,local_args
    setup_logging()
    args = prase_args(sys.argv)
    if args:
        global_args,local_args = args
    else:
        sys.exit(1)
    '''Parsing args'''
    if not setup_session():
        logger.fatal('登陆失败！')
        sys.exit(2)            

    if global_args.http:
        logger.warning('强制使用 HTTP')
    
    if global_args.save:
        logger.info('保存登陆凭据')        
        print(base64.b64encode(sess.to_bytes()).decode())
        sys.exit(0)

    if sess.DEFAULT_UA: # using Web APIs
        bup = {'ws','qn','bda2'}
        bupfetch = {'kodo','gcs','bos'}
        if global_args.cdn in bup:
            sess.UPLOAD_PROFILE = 'ugcupos/bup'                                
        elif global_args.cdn in bupfetch:
            sess.UPLOAD_PROFILE = 'ugcupos/bupfetch'
        sess.UPLOAD_CDN     = global_args.cdn
        logger.info('CDN ： %s [%s]' % (sess.UPLOAD_CDN,sess.UPLOAD_PROFILE))            
        logger.warning('Web 端 API @ ID:%s' % sess.Self['data']['uname'])
    else: # using client APIs
        try:
            logger.warning('上传助手 API @ MID:%s' % sess.mid)    
        except:
            logger.fatal('无效登陆凭据')
            sys.exit(1)
    prepare_temp(TEMP_PATH)    
    # Output current settings        
    logger.info('任务总数: %s' % len(local_args))        
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
          
    if not failure:
        logger.info('任务完毕')
        sys.exit(0)
    logger.warning('上传未完毕')
    sys.exit(1)