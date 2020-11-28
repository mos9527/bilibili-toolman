'''bilibili-toolman 哔哩哔哩工具人'''
# region Setup
from bilisession import BiliSession,Submission
from providers import DownloadResult
from utils import report_progress
from pathlib import Path
import providers
import coloredlogs,logging,sys,argparse,os
temp_path = 'temp'
cookie_path = os.path.join(str(Path.home()), '.bilibili-toolman')
coloredlogs.DEFAULT_LOG_FORMAT = '[ %(asctime)s %(name)s %(levelname)6s ] %(message)s'
coloredlogs.install(0);logging.getLogger('urllib3').setLevel(100);logging.getLogger('PIL.Image').setLevel(100)
def save_cookies(cookie):
    if not cookie:return
    with open(cookie_path,'w+') as target:target.write(cookie)
def load_cookies():    
    return open(cookie_path).read()
'''Logging levels & Save paths'''
p = argparse.ArgumentParser(description='bilibili-toolman 哔哩哔哩工具人')
p.add_argument('--cookies',metavar='COOKIES',type=str,help='Bilibili 所用 Cookies ( 需要 SESSDATA 及 bili_jct ) e.g.cookies=SESSDATA=cb0..; bili_jct=6750... ')
p.add_argument('--thread-id',type=int,help='分区 ID',default=19)
p.add_argument('--tags',type=str,help='标签 (请用逗号隔开)',default='转载')
provider_dict = dict()
for provider in dir(providers):
    if not 'provider_' in provider:continue
    provider_name = provider.replace('provider_','')    
    provider_dict[provider_name] = getattr(providers,provider)
    p.add_argument('--%s'%provider_name,metavar='%s-URL'%provider_name.upper(),type=str,help=provider_dict[provider_name].__desc__)
if len(sys.argv) < 2:
    sys.stderr.writelines(['No arguments,exiting\n'])
    p.print_help()
    sys.exit(2)
args=p.parse_args().__dict__
provider,resource=None,None
for arg in args: # choose last given provider as our take
    if arg in provider_dict:
        provider=provider_dict[arg]
        resource=args[arg]
if not provider or not resource:
    sys.stderr.writelines(['Missing arguments,exiting\n'])
    p.print_help()
    sys.exit(2)
'''Loading cookies'''
save_cookies(args['cookies'])
'''Setting up argparser & deciding content provider'''
# endregion
# region Preparing
if not os.path.isdir(temp_path):os.mkdir(temp_path)
os.chdir(temp_path)
sess = BiliSession(load_cookies())
logging.info('Logged in as: %s' % sess.Self['data']['uname'])
logging.info('Selected provider: %s - %s' % (provider.__name__,provider.__desc__))
# endregion
# region Downloading source
logging.info('Ready to download resource')
source : DownloadResult = provider.download_video(resource)
logging.info('Finished downloading %s' % source.title)
logging.info('Summary: %s' % f'''

    Title        : {source.title}

    Description  : 
      
      %s
''' % '\n      '.join(source.description.split('\n')))
# endregion
# region Uploading
logging.warning('Uploading video')
basename, size, endpoint, config, state = sess.UploadVideo(source.video_path,onStatusChange=report_progress)
pic = sess.UploadCover(source.cover_path)
if len(source.title) > 80:
    source.title = source.title[:77] + '...'
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
# endregion