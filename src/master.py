import time

import rpyc
import uuid
import threading
import math
import random
import configparser
import signal
import pickle
import sys
import os

from rpyc.utils.server import ThreadedServer

from model import file_metadata


class FileLock:
    def __init__(self):
        self.reader = 0
        self.r_lock = threading.Lock()
        self.w_lock = threading.Lock()

    # implementation of read-write-lock to the file; reader first
    def w_acquire(self):
        self.r_lock.acquire()

    def w_release(self):
        self.r_lock.release()

    def r_acquire(self):
        self.r_lock.acquire()
        if self.reader == 0:
            self.w_lock.acquire()
        self.reader += 1
        self.r_lock.release()

    def r_release(self):
        self.r_lock.acquire()
        self.reader -= 1
        if self.reader == 0:
            self.w_lock.release()
        self.r_lock.release()


def int_handler(signal, frame):
    # pickle.dump(([_.file for _ in MasterService.exposed_Master.file_table],
    # MasterService.exposed_Master.block_mapping),
    pickle.dump(MasterService.exposed_Master.file_table,
                open('fs.img', 'wb'))
    sys.exit(0)


def set_conf():
    conf = configparser.ConfigParser()
    conf.read_file(open('dfs.conf'))
    MasterService.exposed_Master.block_size = int(conf.get('master', 'block_size'))
    MasterService.exposed_Master.replication_factor = int(conf.get('master', 'replication_factor'))
    minions = conf.get('master', 'minions').split(',')
    for m in minions:
        id, host, port = m.split(":")
        MasterService.exposed_Master.minions[id] = (host, port)

    if os.path.isfile('fs.img'):
        MasterService.exposed_Master.file_table = pickle.load(
            open('fs.img', 'rb'))


class MasterService(rpyc.Service):
    class exposed_Master():
        file_table = {}
        file_locks = {}
        tableLock = threading.Lock()
        minions = {}

        block_size = 2
        replication_factor = 1

        def __init__(self):
            # 加载文件元数据的同时初始化文件锁，默认所有锁此时处于打开状态
            for f in MasterService.exposed_Master.file_table:
                if f not in MasterService.exposed_Master.file_locks:
                    MasterService.exposed_Master.file_locks[f] = FileLock()

        def exposed_read(self, fname):
            mapping = self.__class__.file_table[fname]
            return mapping

        def exposed_write(self, dest, size, query):
            if self.exists(dest):
                ans = query('The file \'%s\' already exists, would you like to overwrite it?' % dest)
                if ans:
                    self.exposed_delete(dest)

            # self.__class__.file_table[dest] = []
            # TODO 是否需要改进以下file_table的形式？？？
            self.__class__.tableLock.acquire()
            self.__class__.file_table[dest] = file_metadata(fname=dest)
            self.__class__.file_locks[dest] = FileLock()
            # 创建文件的同时上锁，避免同时创建文件
            self.__class__.file_locks[dest].w_acquire()
            self.__class__.tableLock.release()

            num_blocks = self.calc_num_blocks(size)
            blocks = self.alloc_blocks(dest, num_blocks)
            self.__class__.file_table[dest].blocks = blocks
            return blocks, self.__class__.file_table[dest].time_stamp

        def exposed_write_finished(self, destination):
            # 完成上传后client通知master可以释放锁
            self.__class__.file_locks[destination].w_release()

        def exposed_get_file_table_entry(self, f_name, c_time_stamp=None):
            if f_name in self.__class__.file_table:
                self.__class__.file_locks[f_name].r_acquire()
                if c_time_stamp == self.__class__.file_table[f_name].time_stamp:
                    return None, False, None
                else:
                    return self.__class__.file_table[f_name].blocks, True, self.__class__.file_table[f_name].time_stamp
            else:
                return None, True, None

        def exposed_read_finished(self, f_name):
            self.__class__.file_locks[f_name].r_release()

        def exposed_get_block_size(self):
            return self.__class__.block_size

        def exposed_get_minions(self):
            return self.__class__.minions

        def exposed_get_minion(self, id):
            return self.__class__.minions[id]

        def calc_num_blocks(self, size):
            return int(math.ceil(float(size) / self.__class__.block_size))

        def exists(self, file):
            return file in self.__class__.file_table

        def alloc_blocks(self, dest, num):
            blocks = []
            for i in range(0, num):
                block_uuid = uuid.uuid1()  # .urn.lstrip('urn:uuid')
                # nodes_ids = random.sample(self.__class__.minions.keys(), self.__class__.replication_factor)[0]
                nodes_ids = random.sample(self.__class__.minions.keys(), 1)[0]
                # 对于每个block，随机分配一个minion group，因此replication在此为1，备份的事情交给minion group
                # pair = block_minion_pair(block_uuid, self.__class__.minions[nodes_ids])
                blocks.append((block_uuid, self.__class__.minions[nodes_ids]))

            return blocks

        def exposed_delete(self, dest):
            self.__class__.file_locks[dest].w_acquire()
            for block in self.__class__.file_table[dest].blocks:
                block_uuid, minion_info = block
                host, port = minion_info

                conn = rpyc.connect(host, port)
                minion = conn.root.Minion()
                minion.delete(block_uuid)
            self.file_table.__delitem__(dest)
            self.__class__.file_locks[dest].w_release()


if __name__ == "__main__":
    set_conf()
    signal.signal(signal.SIGINT, int_handler)
    t = ThreadedServer(MasterService, port=2131)
    t.start()
