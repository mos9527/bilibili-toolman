import os
from threading import Lock
from requests import Session
from io import IOBase
from queue import Queue
from threading import Thread
import json

# wrappers
def JSONResponse(classfunc):
    '''Decodes `Response`s content to JSON'''
    def wrapper(session: Session, *args, **kwargs):
        response = classfunc(session, *args, **kwargs)
        decoded = json.loads(response.text)
        return decoded
    return wrapper

# common models
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

    def create_iterator(self, path, start, end):   
        return _FileIterator(self, path, start, end)

class _FileIterator():
    '''__iter__ impl for `FileManager` with i/o usage monitoring'''
    def __init__(self, fm: FileManager, path, start, end) -> None:
        self.fm, self.path, self.start, self.end = fm, path, start, end

    def __iter__(self):
        start = self.start
        for start in range(self.start, self.end, FileManager.CHUNK_SIZE):
            yield self.fm.read(self.path, start, min(self.end, start + FileManager.CHUNK_SIZE))
        if start + FileManager.CHUNK_SIZE < self.end:
            yield self.fm.read(self.path, start, self.end)

    def __len__(self):
        return self.end - self.start     

class ThreadedWorkQueue(Queue):
    '''Essential Thread pool / queue'''
    def __init__(self, worker_class, worker_count=4) -> None:
        super().__init__()
        self.worker_count = worker_count
        self.workers = [worker_class(self, name='Worker-%s' % i)
                        for i in range(0, worker_count)]

    def run(self):
        '''Start up all the workers'''
        for worker in self.workers:
            worker.start()

    def new_task(self, task):
        '''Assgins new task to queue'''
        self.put(task)

class BiliUploadWorker(Thread):
    '''Upload workers'''
    daemon = True

    def __init__(self, queue, name) -> None:
        super().__init__()
        self.name = name
        self.queue: Queue = queue

    def run(self) -> None:
        '''Fetches new tasks as we run'''
        while True:
            task = self.queue.get()  # blocking
            self.execute(task)
            self.queue.task_done()  # assigns our task has been completed

    def execute(self, task):
        sess, path, endpoint, chunk, config = task
        sess.put(endpoint, params=chunk, headers={
                 'X-Upos-Auth': config['auth']}, 
                 data=file_manager.create_iterator(path, chunk['start'], chunk['end'])
        )

file_manager = FileManager()        