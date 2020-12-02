'''bilibili-toolman 哔哩哔哩工具人'''
# region Setup
from re import sub
from bilisession import BiliSession,Submission
from providers import DownloadResult
from utils import setup_logging,prepare_temp,report_progress,save_cookies,load_cookies,prase_args,limit_chars,limit_length,local_args as largs
import logging,sys,time,urllib.parse

sess = BiliSession()

def perform_task(provider,args):
    '''To perform a indivudial task

    If multiple videos are given by the provider,the submission will be in multi-parts (P)
    Otherwise,only the given video is uploaded as a single part subject

    Args:

        provider - one of the modules of `providers`
        args - task arguments dictionary    
            * resource - resoucre URI (must have)
            - opts     - options for uploader in query string e.g. format=best            
            - See `utils.local_args` for more arguments,along with thier details
    '''
    logger = sess.logger
    resource = args['resource']    
    opts = args['opts']
    try:
        opts = urllib.parse.parse_qs(opts)
        provider.update_config({k:v[-1] for k,v in opts.items()})
    except:opts = 'INVALID OPTIONS'
    '''Passing options'''
    self_info = sess.Self
    if not 'uname' in self_info['data']:
        return logger.error(self_info['message'])        
    logger.warning('Uploading as %s' % self_info['data']['uname'])
    logger.info('Processing task:')
    logger.info('  - Type: %s - %s' % (provider.__name__,provider.__desc__))
    logger.info('  - URI : %s' % resource)
    for k,v in largs.items():logger.info('  - %s : %s' % (v[0],args[k]))
    logger.info('Fetching source video')
    '''Downloading source'''
    try:
        sources : DownloadResult = provider.download_video(resource)
    except Exception as e:
        logger.error('Cannot download specified resource - %s - skipping' % e)
        return 
    submissions = Submission()
    logging.info('Processing total of %s sources' % len(sources.results))
    for source in sources.results:       
        '''If one or multipule sources'''
        format_blocks = {
            'title':source.title,
            'desc':source.description
        }
        source.title = limit_chars(limit_length(args['title_fmt'] % format_blocks,80))
        source.description = limit_chars(limit_length(args['desc_fmt'] % format_blocks,2000))        
        logger.info('Finished: %s' % source.title)
        '''Summary trimming'''
        logger.warning('Uploading video & cover')
        while True:
            try:
                basename, size, endpoint, config, state = sess.UploadVideo(source.video_path,report=report_progress)
                pic = sess.UploadCover(source.cover_path)['data']['url'] if source.cover_path else ''
                break
            except Exception:
                logger.warning('Failed to upload - retrying')
                time.sleep(1)
        logger.info('Upload complete')
        # submit_result=sess.SubmitVideo(submission,endpoint,pic['data']['url'],config['biz_id'])
        with Submission() as submission:
            submission.cover_url = pic
            submission.video_endpoint = endpoint
            submission.biz_id = config['biz_id']
            '''Sources identifiers'''   
            submission.copyright = Submission.COPYRIGHT_REUPLOAD if not source.original else Submission.COPYRIGHT_SELF_MADE
            submission.source = sources.soruce         
            submission.thread = args['thread_id']
            submission.tags = args['tags'].split(',')
            submission.description = source.description
            submission.title = source.title            
        '''Use the last given thread,tags,cover & description per multiple uploads'''                           
        submissions.thread = submission.thread or submissions.thread        
        submissions.tags = submission.tags or submissions.tags
        submissions.submissions.append(submission)        
    '''Filling submission info'''
    submissions.source = sources.soruce

    submissions.title = sources.title
    submissions.description = sources.description

    '''Make cover image for all our submissions as well'''
    pic = sess.UploadCover(sources.cover_path)['data']['url'] if sources.cover_path else ''
    submissions.cover_url = pic
    '''Finally submitting the video'''
    submit_result=sess.SubmitVideo(submissions,seperate_parts=args['is_seperate_parts'] != None)  
    dirty = False
    for result in submit_result['results']:
        if result['code'] == 0:logger.info('Upload success - BVid: %s' % result['data']['bvid'])        
        else:
            logger.warning('Upload Failed: %s' % result['message'])        
            dirty = True
    return submit_result,dirty

def setup_session(cookies:str):
    '''Setup session with cookies in query strings & setup temp root'''
    return prepare_temp() and sess.load_cookies(cookies)

if __name__ == "__main__":
    setup_logging()
    global_args,local_args = prase_args(sys.argv)
    logging.info('Total tasks: %s' % len(local_args))
    success,failure = [],[]
    '''Parsing args'''
    save_cookies(global_args['cookies'])
    '''Saving / Loading cookies'''
    if not setup_session(load_cookies()):
        logging.fatal('Unable to set working directory,quitting')
        sys.exit(2)
    for provider,args in local_args:
        result,dirty = perform_task(provider,args)
        if not dirty:success.append((args,result))
        else: failure.append((args,None))
    if not failure:sys.exit(0)
    logging.warning('Dirty flag set,upload might be unfinished')
    sys.exit(1)
