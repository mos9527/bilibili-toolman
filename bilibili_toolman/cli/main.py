# -*- coding: utf-8 -*-
from .. import BiliWebSession as BiliSession
from ..bilisession.common import LoginException
from ..bilisession.common.submission import Submission
from ..providers import DownloadResult
from . import AttribuitedDict,setup_logging,prepare_temp,prase_args,sanitize,truncate,local_args as largs

from collections import defaultdict
import logging,sys,urllib.parse

TEMP_PATH = 'temp'

sess_upload : BiliSession
sess_submit : BiliSession
logger = logging.getLogger('toolman')

def download_sources(provider,arg) -> DownloadResult:
    resource = arg.resource
    opts = arg.opts
    try:
        opts = urllib.parse.parse_qs(opts,keep_blank_values=True)
        provider.update_config({k:v[-1].replace(';','') for k,v in opts.items()})
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
    logger.info('上传资源数：%s' % len(sources.results))    
    def format(source):
        blocks      = defaultdict(lambda:'...',{'title':source.title,'desc':source.description,**source.extra})
        title       = truncate(sanitize(arg.title.format_map(blocks)),sess_submit.MISC_MAX_TITLE_LENGTH)   
        description = truncate(sanitize(arg.desc .format_map(blocks)),sess_submit.MISC_MAX_DESCRIPTION_LENGTH)        
        return blocks,title,description        
            
    for source in sources.results:       
        '''If one or multipule sources'''        
        blocks,title,description = format(source)
        logger.info('准备上传: %s' % title)
        '''Summary trimming'''
        endpoint = None
        for _ in range(0,sess_upload.RETRIES_UPLOAD_ID):
            try:
                endpoint, bid = sess_upload.UploadVideo(source.video_path)
                cover_url = sess_upload.UploadCover(source.cover_path)['data']['url'] if source.cover_path else ''
                break
            except Exception as e:
                logger.warning('%s 上传失败! - %s - 重试' % (source,e))                
        if not endpoint:
            logger.error('URI 获取失败 - 跳过')
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
            video.copyright = submission.COPYRIGHT_REUPLOAD if not arg.original else submission.COPYRIGHT_ORIGINAL            
            video.source = sources.soruce      
            '''Thread,Tags,Description & Title'''   
            video.thread = arg.thread_id
            video.tags = arg.tags.format_map(blocks).split(',')
            video.description = description # Description per-part is implemented. Dunno why their frontend decided to discard this data.
                                            # Still shows up in responses though. Might be of use sometime.
            video.title = title # This shows up as title per-part
        '''Use the last given thread per multiple uploads,while the tags are extended.'''
        submission.thread = video.thread or submission.thread        
        submission.tags.extend(video.tags)
        submission.videos.append(video) # to the main submission
    '''Filling submission info'''        
    submission.copyright = submission.COPYRIGHT_REUPLOAD if not arg.original else submission.COPYRIGHT_ORIGINAL
    submission.no_reprint = submission.REPRINT_ALLOWED if not arg.no_reprint else submission.REPRINT_DISALLOWED
    '''Use title & description from main sources (e.g. Uploading a YT Playlist)'''
    blocks,title,description = format(sources)
    submission.title = title
    submission.description = description # This is the only description that gets shown
    submission.source = sources.soruce
    '''Upload cover images for all our submissions as well'''
    cover_url = sess_upload.UploadCover(sources.cover_path)['data']['url'] if sources.cover_path else ''
    submission.cover_url = cover_url    
    '''Finally submitting the video'''
    if not arg.no_submit:
        submit_result=sess_submit.SubmitSubmission(submission,seperate_parts=arg.seperate_parts)  
        dirty = False
        for result in submit_result['results']:
            if result['code'] == 0:logger.info('上传成功 - BVid: %s' % result['data']['bvid'])        
            else:
                logger.warning('%s 上传失败 : %s' % (submission,result['message']))
                dirty = True
        return submit_result,dirty
    else:
        logger.warning('已跳过稿件提交')
        return '',False
    

global_args,local_args = None,None

def setup_session():
    '''Setup session with cookies in query strings & setup temp root'''
    global sess_upload
    global sess_submit    
    def setup_params(sess):
        if global_args.http:
            logger.warning('强制使用 HTTP')
            sess.FORCE_HTTP = True
        if global_args.noenv:
            logger.warning('不使用环境变量；请求将绕过代理')
            sess.trust_env = False                    
    if global_args.cookies:
        from .. import BiliWebSession
        sess = BiliWebSession(global_args.cookies)    
        setup_params(sess)
        user = sess.Self
        if not 'uname' in user['data']:
            logger.error('Cookies无效: %s' % user['message'])        
            return False                
        logger.warning('Web端 API 需 Lv3+ 及 1000+ 关注量才可多 P 上传，若出错请启用 --seperate_parts')
        sess_upload = sess
        sess_submit = sess        
    elif global_args.sms:        
        from .. import BiliClientSession
        sess = BiliClientSession()
        setup_params(sess)
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
                sess_upload = sess
                sess_submit = sess
                break
            except LoginException as e:
                logger.error('验证码无效，请重试：%s' % e)            
        if i == 4:
            logger.critical('多次重试后无法登录')            
            return False
    elif global_args.load:            
        sess = BiliSession.from_base64_string(global_args.load)
        setup_params(sess)
        sess_upload = sess
        sess_submit = sess
    else:
        logger.error('未提供凭据')
        return False
    # Overriding credentials
    if global_args.load_upload:        
        sess = BiliSession.from_base64_string(global_args.load_upload)
        setup_params(sess)
        sess_upload = sess
    if global_args.load_submit:        
        sess = BiliSession.from_base64_string(global_args.load_submit)
        setup_params(sess)
        sess_submit = sess
    return True

def __main__():
    global global_args,local_args
    global sess_submit,sess_upload
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
    
    if global_args.save and not (global_args.load_upload or global_args.load_submit):
        logger.info('保存登陆凭据')
        print(sess_submit.to_base64_string())
        sys.exit(0)

    for desc,sess in [('提交用',sess_submit),('上传用',sess_upload)]:
        logger.warning('%s配置：' % desc)
        if sess.TYPE == 'web': # using Web APIs
            bup = {'ws','qn','bda2'}
            bupfetch = {'kodo','gcs','bos'}
            if global_args.cdn in bup:
                sess.UPLOAD_PROFILE = 'ugcupos/bup'                                
            elif global_args.cdn in bupfetch:
                sess.UPLOAD_PROFILE = 'ugcupos/bupfetch'
            sess.UPLOAD_CDN     = global_args.cdn
            logger.info('Web 端 API @ ID:%s' % sess.Self['data']['uname'])
            logger.debug('CDN ： %s [%s]' % (sess.UPLOAD_CDN,sess.UPLOAD_PROFILE))            
        elif sess.TYPE == 'client': # using client APIs
            logger.info('上传助手 API @ MID:%s' % sess.mid)    
    
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
    logger.warning('上传未完毕：检查标签，标题，描述内有无非法字符或超长字串；如遇其他问题请提交issue')
    sys.exit(1)