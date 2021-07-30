# region Setup
from ..bilisession import logger
from ..bilisession.common.submission import Submission
from ..providers import DownloadResult
from . import AttribuitedDict,setup_logging,prepare_temp,prase_args,sanitize_string,truncate_string,local_args as largs
import pickle,logging,sys,urllib.parse

TEMP_PATH = 'temp' # TODO : NOT chroot-ing for downloading into a different folder
sess = None

def download_sources(provider,arg) -> DownloadResult:
    '''
    '''
    resource = arg.resource
    opts = arg.opts
    try:
        opts = urllib.parse.parse_qs(opts)
        provider.update_config({k:v[-1] for k,v in opts.items()})
    except:opts = 'INVALID OPTIONS'
    '''Passing options'''
    logger.info('Fectching source video')
    logger.info('  - Type: %s - %s' % (provider.__name__,provider.__desc__))
    logger.info('  - URI : %s' % resource)    
    '''Downloading source'''
    try:
        return provider.download_video(resource)
    except Exception as e:
        logger.error('Cannot download specified resource - %s' % e)
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
    logging.info('Processing total of %s sources' % len(sources.results))    
    def sanitize(title,desc,**kw):
        blocks = {'title':title,'desc':desc,**kw}
        return truncate_string(sanitize_string(arg.title_fmt.format(**blocks)),sess.MISC_MAX_TITLE_LENGTH),truncate_string(sanitize_string(arg.desc_fmt.format(**blocks)),sess.MISC_MAX_DESCRIPTION_LENGTH)
    for source in sources.results:       
        '''If one or multipule sources'''        
        title,description = sanitize(source.title,source.description)
        logger.info('Uploading: %s' % title)
        '''Summary trimming'''
        try:
            endpoint, bid = sess.UploadVideo(source.video_path)
            cover_url = sess.UploadCover(source.cover_path)['data']['url'] if source.cover_path else ''
        except Exception as e:
            logger.warning('Failed to upload (%s) - skipping' % e)
            break
        if not endpoint:
            logger.error('No Endpoint - what\'s going on?')
            continue
        logger.info('Upload complete')
        with Submission() as video:
            '''Creatating a video per submission'''
            # A lot of these doesn't really matter as per-part videos only identifies themselves through UI via their titles
            video.cover_url = cover_url
            video.video_endpoint = endpoint
            video.biz_id = bid
            '''Sources identifiers'''   
            video.copyright = Submission.COPYRIGHT_REUPLOAD if not source.original else Submission.COPYRIGHT_SELF_MADE
            video.source = sources.soruce         
            video.thread = arg.thread_id
            video.tags = arg.tags.split(',')
            # video.description = source.description # This does NOT change per video - Deprecated
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
        if result['code'] == 0:logger.info('Upload success - BVid: %s' % result['data']['bvid'])        
        else:
            logger.warning('Upload Failed: %s' % result['message'])        
            dirty = True
    return submit_result,dirty

global_args,local_args = None,None

def setup_session():
    '''Setup session with cookies in query strings & setup temp root'''
    global sess    
    if global_args.username and global_args.pwd:
        logger.info('Client Session - Logging in with username & password')
        from ..bilisession.client import BiliSession
        sess = BiliSession()        
        result = sess.LoginViaUsername(global_args.username,global_args.pwd)        
        logger.warning('Bilibili-toolman - operating as MID:%s' % sess.mid)
        return result
    elif global_args.cookies:
        logger.info('Web Session - Logging in with cookies')
        from ..bilisession.web import BiliSession
        sess = BiliSession()
        sess.LoginViaCookiesQueryString(global_args.cookies)
        self_ = sess.Self
        if not 'uname' in self_['data']:
            logger.error('Invalid cookies: %s' % self_['message'])        
            return False
        logger.warning('Bilibili-toolman - operating as %s' % self_['data']['uname'])
        for arg in local_args.items():
            arg['seperate_parts'] = True
        logger.warning('Forced seperate_parts to True as Web APIs doesn\'t support multi-part uploads.')  
        return True
    elif global_args.load:
        logger.info('Logging in with previously stored credentials')
        unpickled = pickle.loads(open(global_args.load,'rb').read())
        sess = unpickled['session']
        sess.update(unpickled)
        return True
    else:
        logger.error('You must prvoide credentials to operate')
        return False

def __main__():
    global global_args,local_args
    setup_logging()
    global_args,local_args = prase_args(sys.argv)
    '''Parsing args'''
    if not setup_session():
        logging.fatal('Unable to set up session!')
        sys.exit(2)    
    else:         
        if global_args.save:
            logging.warning('Saving credentials to %s' % global_args.save)
            open(global_args.save,'wb').write(pickle.dumps(sess.__dict__()))            
            sys.exit(0)
        prepare_temp(TEMP_PATH)
        # Output current settings        
        logging.info('Total tasks: %s' % len(local_args.items()))        
        success,failure = [],[]
        fmt = lambda s: ('×','√')[s] if type(s) is bool else s
        for provider,arg_ in local_args.items():
            arg = AttribuitedDict(arg_)
            logger.info('Task info:')
            for k,v in largs.items():
                logger.info('  - %s : %s' % (list(v.values())[0],fmt(arg[k])))
            sources = download_sources(provider,arg)                   
            if arg.no_upload:
                logger.warn('Not uploading - no_upload sepceified on this resource')
            else:
                result,dirty = upload_sources(sources,arg)
                if not dirty:success.append((arg,result))
                else: failure.append((arg,None))
        if not failure:sys.exit(0)
        logging.warning('Dirty flag set,not all tasks are done properly')
        sys.exit(1)