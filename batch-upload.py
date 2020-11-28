# For demoing how multiple videos can be uploaded without human interaction
import os,time
urls = [
    'https://www.youtube.com/watch?v=t5BCkXX099I&t=547s&ab_channel=AlexMoukalaMusic'
]
command_template = 'python bilibili-toolman.py '
command_template+= '--thread-id 130 --tags "音乐,dame dane,如龙,编曲,AlexMoukalaMusic" ' # note that cookies are stored
command_template+= '--youtube "%s"'                                                      # once you have put it in the arguments
for url in urls:
    command = command_template % url
    while os.system(command) != 0:
        print('Failed to upload,waiting to try again...')
        time.sleep(5)
print('Successfully uploaded all the videos')