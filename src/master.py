import configparser
import math
import os
import pickle
import random
import signal
import socket
import sys
import threading
import uuid
import toml

import rpyc
from model import FileMetaData
from rpyc.utils.server import ThreadedServer

RPYC_CONFIG = toml.load("config.toml")["rpyc"]


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


# def set_conf():
#     conf = configparser.ConfigParser()
#     conf.read_file(open('dfs.conf'))
#     MasterService.exposed_Master.block_size = int(conf.get('master', 'block_size'))
#     MasterService.exposed_Master.replication_factor = int(conf.get('master', 'replication_factor'))
#     minions = conf.get('master', 'minions').split(',')
#     for m in minions:
#         id, host, port = m.split(":")
#         MasterService.exposed_Master.minions[id] = (host, port)
#
#     if os.path.isfile('fs.img'):
#         MasterService.exposed_Master.file_table = pickle.load(
#             open('fs.img', 'rb'))

def set_conf():
    conf = toml.load("config.toml")
    MasterService.exposed_Master.block_size = conf["master"]["block_size"]
    minions = conf["minion"]["nodes"]
    MasterService.exposed_Master.minions_port = conf["minion"]["port"]
    for gid in range(0, len(minions)):  # group index
        MasterService.exposed_Master.main_minions.append(minions[gid][0])
        if len(minions[gid]) > 1:
            rep_nodes = minions[gid][1:]
            MasterService.exposed_Master.replication_minions.append(rep_nodes)


class MasterService(rpyc.Service):
    class exposed_Master():
        file_table = {}
        file_locks = {}
        tableLock = threading.Lock()
        main_minions = []
        replication_minions = []
        minions_port = -1  # decided by config.toml eventually
        block_size = 1  # decided by config.toml eventually

        # replication_factor = 1

        def __init__(self):
            # 加载文件元数据的同时初始化文件锁，默认所有锁此时处于打开状态
            for f in MasterService.exposed_Master.file_table:
                if f not in MasterService.exposed_Master.file_locks:
                    MasterService.exposed_Master.file_locks[f] = FileLock()

        def exposed_read(self, fname):
            mapping = self.file_table[fname]
            return mapping

        def exposed_write(self, dest, size, query):
            if self.exists(dest):
                ans = query('The file \'%s\' already exists, would you like to overwrite it? [y/n]' % dest)
                if ans:
                    self.exposed_delete(dest)

            # self.__class__.file_table[dest] = []
            self.tableLock.acquire()
            self.file_table[dest] = FileMetaData(fname=dest)
            self.file_locks[dest] = FileLock()
            # 创建文件的同时上锁，避免同时创建文件
            self.file_locks[dest].w_acquire()
            self.tableLock.release()

            num_blocks = self.calc_num_blocks(size)
            self.file_table[dest].blocks, self.file_table[dest].minion_gids = self.alloc_blocks(num_blocks)
            return self.file_table[dest].blocks, self.file_table[dest].time_stamp, self.main_minions

        def exposed_write_finished(self, destination):
            # 完成上传后client通知master可以释放锁
            self.file_locks[destination].w_release()

        def exposed_get_file_table_entry(self, f_name, c_time_stamp=None):
            if f_name in self.file_table:
                self.file_locks[f_name].r_acquire()
                if c_time_stamp == self.file_table[f_name].time_stamp:
                    return None, False, None
                else:
                    return self.file_table[f_name].blocks, True, self.file_table[f_name].time_stamp
            else:
                return None, True, None

        def exposed_read_finished(self, f_name):
            self.file_locks[f_name].r_release()

        def exposed_get_block_size(self):
            return self.block_size

        def exposed_get_minion_port(self):
            return self.minions_port

        def exposed_get_minions(self):
            return self.main_minions

        def exposed_get_minion(self, id):
            return self.main_minions[id]

        def exposed_get_list(self):
            return self.file_table.keys()

        def calc_num_blocks(self, size):
            return int(math.ceil(float(size) / self.block_size))

        def exists(self, file):
            return file in self.file_table

        def alloc_blocks(self, num):
            # self.check_minions()   # check whether current main_minions still alive
            blocks = []
            gids = {}
            for i in range(0, num):
                block_uuid = uuid.uuid1()  # .urn.lstrip('urn:uuid')
                gid = random.randint(0, len(self.main_minions) - 1)
                blocks.append((block_uuid, gid))
                gids[gid] = True
                # nodes_ids = random.sample(self.__class__.minions.keys(), self.__class__.replication_factor)[0]

                # nodes_ids = random.sample(self.main_minions.keys(), 1)[0]
                # 对于每个block，随机分配一个minion group，因此replication在此为1，备份的事情交给minion group
                # pair = block_minion_pair(block_uuid, self.__class__.minions[nodes_ids])
                # blocks.append((block_uuid, self.main_minions[nodes_ids]))

            return blocks, gids.keys()

        def exposed_delete(self, dest):
            self.file_locks[dest].w_acquire()
            for block in self.file_table[dest].blocks:
                block_uuid, gid = block

                conn = rpyc.connect(self.main_minions[gid], self.minions_port, config=RPYC_CONFIG)
                minion = conn.root.Minion()
                minion.delete(block_uuid)
            self.file_table.__delitem__(dest)
            self.file_locks[dest].w_release()


if __name__ == "__main__":
    set_conf()
    signal.signal(signal.SIGINT, int_handler)
    PORT = 2131
    t = ThreadedServer(MasterService, port=PORT)
    print("Will listening on %s:%d ..." % (socket.gethostbyname(socket.gethostname()), PORT))
    t.start()
