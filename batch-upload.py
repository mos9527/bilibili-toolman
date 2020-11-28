# For demoing how multiple videos can be uploaded without human interaction
import os,time
urls = [
    'https://www.youtube.com/watch?v=-HpJcji9RWw&t=20s&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=UUSf1sBLE98&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=wVi8o3HLMFM&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=DUHo3SbEXk0&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=loCKgzIfqWE&t=1s&ab_channel=Ceekos'
]
command_template = 'python bilibili-toolman.py '
command_template+= '--thread-id 19 --tags "JOJO,HFTF,未来遗产,JOJO的奇妙冒险,Ceekos,TAS" ' # note that cookies are stored
command_template+= '--youtube "%s"'                                                      # once you have put it in the arguments
for url in urls:
    command = command_template % url
    while os.system(command) != 0:
        print('Failed to upload,waiting to try again...')
        time.sleep(5)
print('Successfully uploaded all the videos')