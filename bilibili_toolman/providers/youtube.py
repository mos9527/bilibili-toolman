# -*- coding: utf-8 -*-
'''Youtube video provier - youtube-dl'''
from youtube_dl.postprocessor.ffmpeg import FFmpegPostProcessor, FFmpegPostProcessorError
from youtube_dl.utils import encodeArgument, encodeFilename, prepend_extension, shell_quote
from . import DownloadResult
import logging,youtube_dl,os,subprocess,sys
__desc__ = '''Youtube / Twitch / etc 视频下载 (youtube-dl)'''
__cfg_help__ = '''youtube-dl 参数：
    format (str) - 同 youtube-dl -f
    quite (True,False) - 是否屏蔽 youtube-dl 日志 (默认 False)
特殊参数：
    hardcode - 烧入硬字幕选项
        e.g. 启用    ..;hardcode;...
        e.g. 换用字体 ..;hardcode=style:FontName=Segoe UI       
        e.g. NV硬解码   ..;hardcode=input:-hwaccel cuda/output:-c:v h264_nvenc -crf 17 -b:v 5M
        多个选项用 / 隔开   
e.g. --youtube "..." --opts "format=best;quiet=True;hardcode" --tags ...
    此外，还提供其他变量:
        {id}
        {title}    
        {descrption}
        {upload_date}
        {uploader}
        {uploader_id}
        {uploader_url}
        {channel_id}
        {channel_url}
        {duration}
        {view_count}
        {avereage_rating}
        ...
默认配置：不烧入字幕，下载最高质量音视频，下载字幕但不操作
'''
ydl = None
logger = logging.getLogger('youtube')
youtube_dl.utils.std_headers['User-Agent'] = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
params = {
    'logger':logger,
    'outtmpl':'%(id)s.%(ext)s',
    'format':'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',    
    'writethumbnail':True,
    'writesubtitles':True,   
} # default params,can be overridden
def __to_yyyy_mm_dd(date):
    return date[:4] + '/' + date[4:6] + '/' + date[6:] 
def update_config(cfg):    
    global ydl
    hardcodeSettings = None
    if 'hardcode' in cfg: # private implementation of hardcoding subtitles                    
        hardcodeSettings = HardcodeSettings(from_cmd=cfg['hardcode'])
        del cfg['hardcode']        
    ydl = youtube_dl.YoutubeDL({**params,**cfg})    
    if hardcodeSettings:
        ydl.add_post_processor(HardcodeSubProcesser(ydl,hardcodeSettings))

class HardcodeSettings():
    style = 'FontName=Segoe UI,FontSize=24'
    '''alternative font style for subs filter'''
    input = '' # params for input file
    output = '' # params for output file
    '''other FFMPEG parameters'''
    def __init__(self,from_cmd):
        '''Constructs settings via commandline'''
        for cmd in from_cmd.split('/'):
            if not cmd:break
            idx       = cmd.index(':')
            key,value = cmd[:idx],cmd[idx + 1:]
            setattr(self,key,value)

class HardcodeSubProcesser(FFmpegPostProcessor):
    def run_ffmpeg_multiple_files(self, input_paths, out_path, opts):
        '''making ffmpeg output to stdout instead,and allowing input parameters'''
        self.check_version()

        oldest_mtime = min(
            os.stat(encodeFilename(path)).st_mtime for path in input_paths)

        opts += self._configuration_args()

        files_cmd = []
        for path in input_paths:
            files_cmd.extend([
                encodeArgument('-i'),
                encodeFilename(self._ffmpeg_filename_argument(path), True)
            ])
        cmd =[encodeFilename(self.executable, True), encodeArgument('-y'),encodeArgument('-hide_banner')] + self.settings.input.split()
        # avconv does not have repeat option
        if self.basename == 'ffmpeg':
            cmd += [encodeArgument('-loglevel'), encodeArgument('warning'),encodeArgument('-stats')]
        cmd += (files_cmd
                + [encodeArgument(o) for o in opts]
                + [encodeFilename(self._ffmpeg_filename_argument(out_path), True)])
        self._downloader.to_screen('[debug] ffmpeg command line: %s' % shell_quote(cmd))
        p = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, stdin=subprocess.PIPE)
        p.communicate()
        if p.returncode != 0:
            raise FFmpegPostProcessorError('See stderr for more info')
        self.try_utime(out_path, oldest_mtime, oldest_mtime)

    def __init__(self, downloader,settings : HardcodeSettings):
        self.settings = settings
        super().__init__(downloader=downloader)

    def run(self, information):
        sub = information['requested_subtitles']        
        if sub: 
            lang = list(sub.keys())[0]
            sub_filename = f"{information['display_id']}.{lang}.vtt"
            if os.path.isfile(sub_filename):                
                self._downloader.to_screen('[ffmpeg] 烧入字幕: %s' % sub_filename)                            
                filename = information['filepath']                
                opts = [
                    '-vf',f"subtitles={sub_filename}:force_style='{self.settings.style}'",
                    '-qscale','0',
                    '-c:a','copy'
                ] + self.settings.output.split()

                temp_filename = prepend_extension(filename,'temp')                
                self.run_ffmpeg(filename,temp_filename,opts)
                
                os.remove(encodeFilename(filename))
                os.rename(encodeFilename(temp_filename), encodeFilename(filename))
        return [], information  # by default, keep file and do nothing                            
def download_video(res) -> DownloadResult:            
    with DownloadResult() as results:
        # downloading the cover            
        def append_result(entry):
            with DownloadResult() as result:
                result.extra = entry
                result.title = entry['title']
                result.soruce = entry['webpage_url']
                result.video_path = '%s.%s'%(entry['display_id'],entry['ext'])
                '''For both total results and local sub-results'''
                results.cover_path = result.cover_path = '%s.%s'%(entry['display_id'],'jpg')            
                date = __to_yyyy_mm_dd(entry['upload_date'])
                results.description = result.description = f'''作者 : {entry['uploader']} [{date} 上传]

来源 : https://youtu.be/{entry['id']}

{entry['description']}'''                
            results.results.append(result)
            
        info = ydl.extract_info(res,download=True)
        results.soruce = info['webpage_url']
        results.title = info['title']
        '''Appending our results'''
        if 'entries' in info:
            for entry in info['entries']:
                append_result(entry)
        else:
            append_result(info)
        return results