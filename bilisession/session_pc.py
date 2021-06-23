from .session_web import BiliSession
from hashlib import md5
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64encode
from urllib.parse import quote,urlencode
from typing import Union
import time

class BiliSecurity:
    '''thx! https://github.com/FortuneDayssss/BilibiliUploader'''
    APPKEY = 'aae92bc66f3edfab'
    APPSECRET = 'af125a0d5279fd576c1b4418a3e8276d'
    
    @staticmethod
    def md5(data : Union[str,bytes]) -> str:
        '''generates md5 hex dump of `str` or `bytes`'''
        if type(data) == str:
            return md5(data.encode()).hexdigest()
        return md5(data).hexdigest()

    @staticmethod
    def rsa_pkcs115_encrypt_as_base64(content: bytes, pkcs115_pubkey : str) -> str:
        key = RSA.import_key(pkcs115_pubkey)
        cipher = PKCS1_v1_5.new(key)
        return b64encode(cipher.encrypt(content))

    @staticmethod
    def encrypt_login_password(password: str, oauth2_getkey_resp: dict) -> str:
        _hash, key = oauth2_getkey_resp.json()['data']['hash'], oauth2_getkey_resp.json()['data']['key']
        return BiliSecurity.rsa_pkcs115_encrypt_as_base64((_hash + password).encode('utf-8'), key)

    @staticmethod
    def sign(data : Union[str,dict]) -> str: 
        '''salted sign funtion for `dict`(converts to qs then parse) & `str`'''
        if isinstance(data,dict):
            _str = urlencode(data)        
        elif type(data) != str:
            raise TypeError
        return BiliSecurity.md5(_str + BiliSecurity.APPSECRET)

    @staticmethod
    def get_timestamp() -> int:
        return int(time.time())

class SingedQuery(dict):
    @property
    def signed(self):
        '''returns ourself with calculated `sign` as a new key-value pair'''
        return {**self, 'sign': BiliSecurity.sign(self)}

class BiliSession(BiliSession):
    # this part reused A LOT of old code, some can still be replaced with thier PC counterparts  
    def __init__(self) -> None:
        super().__init__() # so far just linear MRO...could bite my ass later on
        self.headers = {
            'User-Agent': '',
            'Accept-Encoding': 'gzip,deflate'
        }

    def _get_oauth2_getkey_resp(self):
        return self.post("https://passport.bilibili.com/api/oauth2/getKey", data=SingedQuery({
            'appkey': BiliSecurity.APPKEY
        }).signed)

    def LoginViaCookiesQueryString(self, cookies: str):
        raise NotImplementedError # nope

    def LoginViaUsername(self, username: str, password: str):
        '''Logging in via Username and Password

        Args:
            username (str), password (str)

        Returns:
            dict
        '''
        oauth_resp = self._get_oauth2_getkey_resp()
        return self.post(
            "https://passport.bilibili.com/api/oauth2/login",
            data=SingedQuery({
                'appkey': BiliSecurity.APPKEY,
                'password': BiliSecurity.encrypt_login_password(password, oauth_resp),
                'platform': "pc",
                'username': quote(username)
        }).signed)