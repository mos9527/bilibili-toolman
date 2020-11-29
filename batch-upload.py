# For demoing how multiple videos can be uploaded without human interaction
import os,time
urls = [
    'https://www.youtube.com/watch?v=wVi8o3HLMFM&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=CiTzgESFRXI&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=2&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=WuiLDGse7hc&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=3&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=wg61RiZ25bw&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=4&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=cpL3qWmTDK0&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=5&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=xiGjKO8ynEY&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=6&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=53at4abZXAk&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=8&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=Dxvsw0mAvfE&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=9&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=MZqBa550s28&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=10&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=KJALlfFQGyY&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=11&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=xzsZeTEO4Xw&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=12&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=-70WqcDb1qM&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=13&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=eJYisCd2MaU&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=14&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=0ckCiANbOlM&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=15&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=rbJB81IAB1U&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=16&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=9vt2u6FmxOU&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=17&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=2gpkw15WAFY&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=18&ab_channel=Ceekos',
    'https://www.youtube.com/watch?v=zQRyN0Vb-Yg&xxx=PLq5o307cvPzfK2B1iPE5y1eu_f_bVNgvj&index=19&ab_channel=Ceekos'
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