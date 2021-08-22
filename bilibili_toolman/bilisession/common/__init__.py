import os
from threading import Lock
from typing import Tuple
from requests import Session
from io import IOBase
from queue import Queue
import time

from requests.models import Response
# region Wrappers
def JSONResponse(classfunc) -> dict:
    '''Decodes `Response`s content to JSON dict'''
    def wrapper(session: Session, *args, **kwargs):
        response: Response = classfunc(session, *args, **kwargs)
        return response.json()
    return wrapper
# endregion

# common models
class LoginException(Exception):
    def __init__(self, resp : Response,desc='') -> None:
        super().__init__('登陆失败：%s\n<Response %s>:%s' % (desc,resp.status_code,resp.text))
class ReprExDict(dict): 
    '''fancy __repr__-ed dict'''
    def __repr__(self) -> str:
        return '(%s)' % ' '.join(['%s/%s' % (k,v) for k,v in self.items()])

class FileManager(dict):
    '''single-instance threadsafe file IO manager'''
    CHUNK_SIZE = 2**16

    def __init__(self) -> None:
        super().__init__()
        self.lock = Lock()

    def open(self, path):
        self.lock.acquire()  # preventing multipule instances from accessing all at once
        if not path in self or self[path]['stream'].closed:
            self[path] = {'stream': open(path, 'rb'), 'read': 0, 'length': os.stat(path).st_size}
        self.lock.release()

    def close(self, path):
        stream: IOBase = self[path]['stream']
        stream.close()
        del self[path]

    def read(self, path, start, end):
        if not path in self:
            self.open(path)  # open for new IO handler
        stream: IOBase = self[path]['stream']
        self.lock.acquire()  # same as open
        stream.seek(start)
        length = end - start
        self[path]['read'] += length
        self.lock.release()
        return stream.read(length)

class FileIterator():
    '''__iter__ impl for `FileManager` with i/o usage monitoring'''
    def __init__(self, path, start, end) -> None:
        self.path, self.start, self.end = path, start, end

    def __getattr__(self,name): # defining fallback
        return {}

    def __iter__(self):
        start = self.start
        for start in range(self.start, self.end, FileManager.CHUNK_SIZE):
            yield file_manager.read(self.path, start, min(self.end, start + FileManager.CHUNK_SIZE))
        if start + FileManager.CHUNK_SIZE < self.end:
            yield file_manager.read(self.path, start, self.end)

    def __len__(self):
        return self.end - self.start

    def to_bytes(self):
        buffer = bytearray()
        for chunk in self:buffer.extend(chunk)
        return buffer

def get_timestamp() -> int:
    '''returns current time in ms'''
    return int(time.time() * 1000)

def check_file(path) -> Tuple[str, str, int]:
    '''checks if targeted path is a file then returns its Full Path, Basename, Size (in Bytes)'''
    assert os.path.isfile(path)
    size = os.stat(path).st_size
    return path, os.path.basename(path), size

chunk_queue   = Queue()
file_manager = FileManager()
