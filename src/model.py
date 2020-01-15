import time


def time_stamp_now():
    time_now = int(time.time())
    time_local = time.localtime(time_now)
    return time.mktime(time_local)


class FileMetaData:
    def __init__(self, fname, blocks=None, timestamp=None):
        if blocks is None:
            blocks = []
        self.fname = fname
        self.blocks = blocks
        if timestamp is None:
            self.time_stamp = time_stamp_now()
        else:
            self.time_stamp = timestamp
