'''bilibili-toolman 哔哩哔哩工具人'''
# region Setup
from bilisession import BiliSession,Submission
from providers import DownloadResult
from utils import report_progress,save_cookies,load_cookies,temp_path,prase_args,limit_chars,limit_length,local_args as largs
import coloredlogs,logging,sys,os,time,urllib.parse
coloredlogs.DEFAULT_LOG_FORMAT = '[ %(asctime)s %(name)8s %(levelname)6s ] %(message)s'
coloredlogs.install(0);logging.getLogger('urllib3').setLevel(100);logging.getLogger('PIL.Image').setLevel(100)
'''Logging levels & Save paths'''
global_args,local_args = prase_args(sys.argv)
'''Setting up argparser'''
save_cookies(global_args['cookies'])
sess = BiliSession(load_cookies())
'''Loading cookies'''
# endregion
# region Preparing environment
if not os.path.isdir(temp_path):os.mkdir(temp_path)
os.chdir(temp_path)
# endregion
# region Downloading source
logging.info('Total tasks: %s' % len(local_args))
logging.info('Uploading as: %s' % sess.Self['data']['uname'])
for task in local_args:
    provider,args = task
    resource = args['resource']    
    opts = args['opts']
    try:
        opts = urllib.parse.parse_qs(opts)
        provider.update_config({k:v[-1] for k,v in opts.items()})
    except:opts = 'INVALID OPTIONS'
    '''Passing options'''
    logging.info('Processing task:')
    logging.info('  - Type: %s - %s' % (provider.__name__,provider.__desc__))
    logging.info('  - URI : %s' % resource)
    for k,v in largs.items():logging.info('  - %s : %s' % (v[0],args[k]))
    logging.info('Fetching source video')
    '''Downloading source'''
    source : DownloadResult = provider.download_video(resource)
    source.title = limit_chars(limit_length(args['title_fmt'] % source.title,80))
    source.description = limit_chars(limit_length(args['desc_fmt'] % source.description,2000))
    '''Summary'''
    logging.info('Finished: %s' % source.title)
    logging.info('Summary (trimmed): %s' % f'''

        Title        : {source.title}

        Description  : 
        
        %s
    ''' % '\n      '.join(source.description.split('\n')))
    # endregion
    # region Uploading
    logging.warning('Uploading video')
    while True:
        try:
            basename, size, endpoint, config, state = sess.UploadVideo(source.video_path,report=report_progress)
            pic = sess.UploadCover(source.cover_path)
            break
        except Exception:
            logging.warning('Failed to upload,retrying...')
            time.sleep(1)
    logging.info('Upload complete, preparing to submit')
    with Submission() as submission:
        submission.source = source.soruce
        submission.copyright = Submission.COPYRIGHT_REUPLOAD
        submission.desc = source.description
        submission.title = submission.title_1st_video = source.title
        submission.thread = args['thread_id']
        submission.tags = args['tags'].split(',')    
    submit_result=sess.SubmitVideo(submission,endpoint,pic['data']['url'],config['biz_id'])
    if submit_result['code'] == 0:
        logging.info('Upload success - BVid: %s' % submit_result['data']['bvid'])        
    else:
        logging.error('Failed to upload: %s' % submit_result)
logging.info('All tasks done')
# endregion