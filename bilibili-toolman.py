'''bilibili-toolman 哔哩哔哩工具人'''
# region Setup
from re import sub
from bilisession import BiliSession,Submission
from providers import DownloadResult
from utils import setup_logging,prepare_temp,report_progress,save_cookies,load_cookies,prase_args,sanitize_string,truncate_string,local_args as largs
import logging,sys,time,urllib.parse

sess = BiliSession()
logger = sess.logger
# sess.verify = False
def download_sources(provider,arg) -> DownloadResult:    
    resource = arg['resource']    
    opts = arg['opts']
    try:
        opts = urllib.parse.parse_qs(opts)
        provider.update_config({k:v[-1] for k,v in opts.items()})
    except:opts = 'INVALID OPTIONS'
    '''Passing options'''
    logger.info('Fectching source video')
    logger.info('  - Type: %s - %s' % (provider.__name__,provider.__desc__))
    logger.info('  - URI : %s' % resource)
    for k,v in largs.items():logger.info('  - %s : %s' % (v[0],arg[k]))
    '''Downloading source'''
    try:
        return provider.download_video(resource)
    except Exception as e:
        logger.error('Cannot download specified resource - %s' % e)
        return        

def upload_sources(sources : DownloadResult,arg,report=report_progress):
    '''To perform a indivudial task

    If multiple videos are given by the provider,the submission will be in multi-parts (P)
    Otherwise,only the given video is uploaded as a single part subject

    Args:

        provider - one of the modules of `providers`
        arg - task arguments dictionary    
            * resource - resoucre URI (must have)
            - opts     - options for uploader in query string e.g. format=best            
            - See `utils.local_args` for more arguments,along with thier details
        report : A function takes (current,max) to show progress of the upload
    '''    
    submission = Submission()    
    if not sources:return None,True
    logging.info('Processing total of %s sources' % len(sources.results))    
    def sanitize(title,desc,**kw):
        blocks = {'title':title,'desc':desc,**kw}
        return sanitize_string(truncate_string(arg['title_fmt'] % blocks,80)),sanitize_string(truncate_string(arg['desc_fmt'] % blocks,2000))                
    for source in sources.results:       
        '''If one or multipule sources'''        
        title,description = sanitize(source.title,source.description)
        logger.info('Uploading: %s' % title)
        '''Summary trimming'''      
        basename, size, endpoint, config, state , pic = [None] * 6
        while True:
            try:
                basename, size, endpoint, config, state = sess.UploadVideo(source.video_path,report=report)
                pic = sess.UploadCover(source.cover_path)['data']['url'] if source.cover_path else ''
                break
            except Exception as e:
                logger.warning('Failed to upload (%s) - skipping' % e)
                break
        if not endpoint:
            continue
        logger.info('Upload complete')
        with Submission() as video:
            '''Creatating a video per submission'''
            video.cover_url = pic
            video.video_endpoint = endpoint
            video.biz_id = config['biz_id']
            '''Sources identifiers'''   
            video.copyright = Submission.COPYRIGHT_REUPLOAD if not source.original else Submission.COPYRIGHT_SELF_MADE
            video.source = sources.soruce         
            video.thread = arg['thread_id']
            video.tags = arg['tags'].split(',')
            video.description = source.description
            video.title = title            
        '''Use the last given thread,tags,cover & description per multiple uploads'''                           
        submission.copyright = video.copyright or submission.copyright
        submission.thread = video.thread or submission.thread        
        submission.tags.extend(video.tags)
        submission.videos.append(video) # to the main submission
    '''Filling submission info'''    
    title,description = sanitize(sources.title,sources.description)
    submission.source = sources.soruce
    submission.title = title
    submission.description = description
    '''Upload cover images for all our submissions as well'''
    pic = sess.UploadCover(sources.cover_path)['data']['url'] if sources.cover_path else ''
    submission.cover_url = pic
    '''Finally submitting the video'''
    submit_result=sess.SubmitVideo(submission,seperate_parts=arg['seperate_parts'])  
    dirty = False
    for result in submit_result['results']:
        if result['code'] == 0:logger.info('Upload success - BVid: %s' % result['data']['bvid'])        
        else:
            logger.warning('Upload Failed: %s' % result['message'])        
            dirty = True
    return submit_result,dirty

def setup_session(cookies:str):
    '''Setup session with cookies in query strings & setup temp root'''
    return prepare_temp() and sess.LoginViaCookiesQueryString(cookies)

global_args,local_args = None,None

def __tasks__():
    logging.info('Total tasks: %s' % len(local_args))
    success,failure = [],[]

    for provider,arg in local_args:
        sources = download_sources(provider,arg)                
        if arg['no_upload']:
            logger.warn('Not uploading - no_upload sepceified on this resource')
        else:
            result,dirty = upload_sources(sources,arg,report_progress if global_args['show_progress'] else lambda current,max:None )
            if not dirty:success.append((arg,result))
            else: failure.append((arg,None))
    if not failure:sys.exit(0)
    logging.warning('Dirty flag set,not all tasks are done properly')
    sys.exit(1)

if __name__ == "__main__":
    setup_logging()
    global_args,local_args = prase_args(sys.argv)
    '''Parsing args'''
    save_cookies(global_args['cookies'])
    '''Saving / Loading cookies'''    
    if not setup_session(load_cookies()):
        logging.fatal('Unable to set working directory,quitting')
        sys.exit(2)    
    else:
        self_info = sess.Self
        if not 'uname' in self_info['data']:
            logger.error('Invalid cookies: %s' % self_info['message'])        
            sys.exit(2)            
        logger.warning('Bilibili-toolman - operating as %s'  % self_info['data']['uname'])        
        __tasks__()