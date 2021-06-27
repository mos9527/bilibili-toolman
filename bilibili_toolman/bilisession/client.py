'''bilibili - PC API implementation'''
from typing import Iterable, Tuple, Union
from requests.sessions import Session
from urllib.parse import quote,urlencode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from hashlib import md5
from base64 import b64encode
import math

from .web import BiliSession,logger
from .common import FileIterator, JSONResponse , ReprExDict, file_manager, check_file 
from .common.submission import Submission

class Crypto:
    '''THANK YOU! https://github.com/FortuneDayssss/BilibiliUploader'''
    APPKEY = 'aae92bc66f3edfab'
    APPSECRET = 'af125a0d5279fd576c1b4418a3e8276d'
    
    @staticmethod
    def iterable_md5(stream : Iterable) -> str:
        md5_ = md5()
        for chunk in stream:
            md5_.update(chunk)
        return md5_.hexdigest()            

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
    def encrypt_login_password(password: str, oauth2_getkey_json: dict) -> str:
        _hash, key = oauth2_getkey_json['data']['hash'], oauth2_getkey_json['data']['key']
        return Crypto.rsa_pkcs115_encrypt_as_base64((_hash + password).encode('utf-8'), key)

    @staticmethod
    def sign(data : Union[str,dict]) -> str: 
        '''salted sign funtion for `dict`(converts to qs then parse) & `str`'''
        if isinstance(data,dict):
            _str = urlencode(data)        
        elif type(data) != str:
            raise TypeError
        return Crypto.md5(_str + Crypto.APPSECRET)

class SingableDict(dict):
    @property
    def sorted(self):
        '''returns a alphabetically sorted version of `self`'''
        return dict(sorted(self.items()))
    @property
    def signed(self):
        '''returns our sorted self with calculated `sign` as a new key-value pair at the end'''
        _sorted = self.sorted
        return {**_sorted, 'sign': Crypto.sign(_sorted)} # tfw this had wasted too much of my time

class ClientUploadChunk(FileIterator):
    url_endpoint : str
    params : dict
    headers : dict    
    files : dict
    cookies : dict
    session : Session        

    def upload_via_session(self,session = None):
        chunk_bytes = self.to_bytes()
        (session or self.session).post(
            self.url_endpoint,
            params=self.params,
            headers=self.headers,
            files={
                **self.files,
                'md5':(None,Crypto.md5(chunk_bytes)),
                'file': (self.path, chunk_bytes, 'application/octet-stream')
            },
            cookies=self.cookies,            
        )

class BiliSession(BiliSession):
    '''Bilibili Client (ugc_assistant) Upload API Implementation'''
    # this part reused A LOT of old code, some can still be replaced with thier PC counterparts 
    UPLOAD_CHUNK_SIZE = 2 * (1 << 20)
    BUILD_VER = (2, 0, 0,1054)
    BUILD_NO = int(BUILD_VER[0] * 1e8 + BUILD_VER[1] * 1e6 + BUILD_VER[2] * 1e2 + BUILD_VER[3])
    BUILD_STR = '.'.join(map(lambda v: str(v), BUILD_VER))    

    def __init__(self) -> None:
        Session.__init__(self) # no need to init the web variant
        self.headers = {
            'User-Agent': '',
            'Accept-Encoding': 'gzip,deflate'
        }
        self.login_tokens = dict()
    # region Properties
    @property
    def mid(self):
        return self.login_tokens['mid']

    @property
    def access_token(self):
        return self.login_tokens['access_token']

    @property
    def access_key_param(self):
        '''Singed dictionary containing only `access_key` key-value pair'''
        return SingableDict({'access_key':self.access_token}).signed
        
    # endregion

    # region Overrides
    def _preupload(self):
        return self.get(
            "https://member.bilibili.com/preupload",
            params={
                'access_key':self.access_token,
                'mid':self.mid,
                'profile':'ugcfr/pc3'
            }
        )

    def _upload_cover(self,image_binary : bytes,image_mime : str):
        return self.post(
            "https://member.bilibili.com/x/vu/client/cover/up",
            params=self.access_key_param,
            files={'file':('cover.png',image_binary,image_mime)}
        )      

    def _submit_submission(self, submission : Submission):
        return self.post(
            "https://member.bilibili.com/x/vu/client/add",
            params=self.access_key_param,                                    
            json={'build': self.BUILD_VER[-1],**submission.archive}
        )        

    def _view_archive(self, bvid):
        return self.post(
            'https://member.bilibili.com/x/client/archive/view',
            params=SingableDict({
                "access_key": self.access_token,
                "aid": bvid,
                'build': self.BUILD_VER[-1]
            }).signed
        )

    def _edit_archive(self, json: dict):
        return self.post(
            "http://member.bilibili.com/x/vu/client/edit",
            params=self.access_key_param,
            json=json
        )
    # endregion

    # region Client-specific APIs
    @JSONResponse
    def _oauth2_getkey(self):
        return self.post("https://passport.bilibili.com/api/oauth2/getKey", data=SingableDict({
            'appkey': Crypto.APPKEY
        }).signed)

    def _post_complete_upload(self,complete_url,size,basename,md5,chunkcount):
        return self.post(
            complete_url,
            json = {
                'chunks': chunkcount,
                'filesize': size,
                'md5': md5,
                'name': basename,
                'version': self.BUILD_STR,
            })

    def LoginViaCookiesQueryString(self, cookies: str):
        raise NotImplementedError("Not available for Client APIs!")

    @JSONResponse
    def LoginViaUsername(self, username: str, password: str):
        '''Logging in via Username and Password

        Args:
            username (str), password (str)

        Returns:
            dict
        '''
        oauth_json = self._oauth2_getkey()
        resp = self.post(
            "https://passport.bilibili.com/api/oauth2/login",
            data=SingableDict({
                'appkey': Crypto.APPKEY,
                'platform': "pc",                
                'password': Crypto.encrypt_login_password(password, oauth_json),                                
                'username': quote(username)
        }).signed)
        self.login_tokens.update(resp.json()['data'])
        return resp
    
    def UploadVideo(self, path: str) -> Tuple[str,None]:
        # behaves more-or-less the same as in `bilisession.web`,refer to that for more info
        path, basename, size = check_file(path)        
        preupload_token = self._preupload().json()
        # preprae the chunks then uploads them
        chunksize = self.UPLOAD_CHUNK_SIZE
        chunkcount = math.ceil(size/chunksize)
        file_manager.open(path)
        logger.debug('Upload chunks: %s' % chunkcount)
        logger.debug('Upload chunk size: %s' % chunksize)
        def iter_chunks():
            for chunk_n in range(0,chunkcount):
                start = chunksize * chunk_n
                chunk = ClientUploadChunk(path,start,min(start + chunksize,size))
                chunk.session = self
                chunk.url_endpoint = preupload_token['url']
                chunk.files = {
                    'version': (None, self.BUILD_STR),
                    'filesize': (None, chunksize),
                    'chunk': (None, chunk_n),
                    'chunks': (None, chunkcount),                               
                }
                chunk.cookies = {
                    'PHPSESSID':preupload_token['filename']
                }
                yield chunk        
        self._upload_chunks_to_endpoint_blocking(iter_chunks())
        logger.debug('Successfully finished uploading chunks')
        # recalulating md5
        md5_ = Crypto.iterable_md5(FileIterator(path,0,size))        
        file_manager.close(path)
        logger.debug('File hash: %s' % md5_)
        # finalizing upload
        post_r = self._post_complete_upload(preupload_token['complete'],size,basename,md5_,chunkcount)
        logger.debug('Completed upload: %s' % ReprExDict(post_r.json()))
        return preupload_token['filename'], None
    # endregion

    # region Pickling
    def __dict__(self):
        return {
            'cookies':self.cookies,
            'login_tokens':self.login_tokens,
            'session':self
        }
    
    def update(self,state_dict : dict):
        self.cookies = state_dict['cookies']        
        self.login_tokens = state_dict['login_tokens']
    # endregion
