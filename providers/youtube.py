'''Youtube video provier - youtube-dl'''
from io import BytesIO
import re
from . import DownloadResult
import logging,youtube_dl,requests
__desc__ = '''Youtube Video provider'''
logger = logging.getLogger('youtube')
ydl = youtube_dl.YoutubeDL({
    'logger':logger,
    'merge-output-format':'mp4',
    'outtmpl':'%(id)s.%(ext)s',
    'format':'worst',
})

def __to_yyyy_mm_dd(date):
    return date[:4] + '/' + date[4:6] + '/' + date[6:]

def download_video(res) -> DownloadResult:    
    from PIL import Image
    # downloading the cover
    info = ydl.extract_info(res,download=True)
    cover_url = info['thumbnail']
    cover_path= info['display_id'] + '.png'
    date = __to_yyyy_mm_dd(info['upload_date'])
    # Also converting webp to png
    cover_webp = requests.get(cover_url).content
    cover_webp = Image.open(BytesIO(cover_webp))
    cover_webp.save(cover_path)
    logger.debug('Downloaded cover image %s' % cover_path)
    with DownloadResult() as result:
        result.soruce = info['webpage_url']

        result.video_path = '%s.%s'%(info['display_id'],info['ext'])
        result.cover_path = cover_path
        
        result.title = info['title']
        result.description = f'''作者 : {info['uploader']} [{date} 上传]
来源 : {result.soruce}

{info['description']}
        '''
    return result