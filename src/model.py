import time


def timeStampNow():
    time_now = int(time.time())
    time_local = time.localtime(time_now)
    return time.mktime(time_local)


class file_metadata:
    def __init__(self, fname, blocks=None, timestamp=None):
        if blocks is None:
            blocks = []
        self.fname = fname
        self.blocks = blocks
        if timestamp is None:
            self.time_stamp = timeStampNow()
        else:
            self.time_stamp = timestamp
