'''bilibili-toolman 哔哩哔哩工具人'''
# region Setup
from bilisession import BiliSession,Submission
from providers import DownloadResult
from utils import setup_logging,prepare_temp,report_progress,save_cookies,load_cookies,prase_args,limit_chars,limit_length,local_args as largs
import logging,sys,time,urllib.parse

sess = BiliSession()

def perform_task(provider,args):
    '''To perform a indivudial task

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
        logger.error(self_info['message'])
        return
    logger.warning('Uploading as %s' % self_info['data']['uname'])
    logger.info('Processing task:')
    logger.info('  - Type: %s - %s' % (provider.__name__,provider.__desc__))
    logger.info('  - URI : %s' % resource)
    for k,v in largs.items():logger.info('  - %s : %s' % (v[0],args[k]))
    logger.info('Fetching source video')
    '''Downloading source'''
    try:
        source : DownloadResult = provider.download_video(resource)
    except Exception as e:
        logger.error('Cannot download specified resource - %s,skipping...' % e)
        return        
    format_blocks = {
        'title':source.title,
        'desc':source.description
    }
    source.title = limit_chars(limit_length(args['title_fmt'] % format_blocks,80))
    source.description = limit_chars(limit_length(args['desc_fmt'] % format_blocks,2000))
    '''Summary'''
    logger.info('Finished: %s' % source.title)
    logger.info('Submission Summary (trimmed): %s' % f'''
    Title        : {source.title}

    Description  :         

        %s''' % '\n      '.join(source.description.split('\n')))
    # endregion
    # region Uploading
    logger.warning('Uploading video & cover')
    while True:
        try:
            basename, size, endpoint, config, state = sess.UploadVideo(source.video_path,report=report_progress)
            pic = sess.UploadCover(source.cover_path) if source.cover_path else ''
            break
        except Exception:
            logger.warning('Failed to upload,retrying...')
            time.sleep(1)
    logger.info('Upload complete, preparing to submit')
    with Submission() as submission:
        submission.source = source.soruce
        submission.copyright = Submission.COPYRIGHT_REUPLOAD if not source.original else Submission.COPYRIGHT_SELF_MADE
        submission.desc = source.description
        submission.title = submission.title_1st_video = source.title
        submission.thread = args['thread_id']
        submission.tags = args['tags'].split(',')    
    submit_result=sess.SubmitVideo(submission,endpoint,pic['data']['url'],config['biz_id'])
    if submit_result['code'] == 0:
        logger.info('Upload success - BVid: %s' % submit_result['data']['bvid'])        
        return submit_result
    else:
        logger.error('Failed to upload: %s' % submit_result)
        return

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
    setup_session(load_cookies())
    for provider,args in local_args:
        result = perform_task(provider,args)
        if result:success.append((args,result))
        else: failure.append((args,None))
    logging.info('Upload summary')
    for succeed in success:
        logging.info ('  - Success: %s [%s]' % (succeed[0]['resource'],succeed[1]['data']['bvid']))
    for failed in failure:
        logging.error('  - Failure: %s' % (failed[0]['resource']))
    if not failure:sys.exit(0)
    sys.exit(1)
