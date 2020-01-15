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
        self.minion_gids = []    # 表明该文件放在哪几个minion group中
        if timestamp is None:
            self.time_stamp = time_stamp_now()
        else:
            self.time_stamp = timestamp
