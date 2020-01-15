import logging
import os
import sys
import socket
import rpyc
import toml
import uuid
from rpyc.utils.server import ThreadedServer

DATA_DIR = "/data/"
RPYC_CONFIG = toml.load("config.toml")["rpyc"]
slaves = []


def set_conf(localhost):
    conf = toml.load("config.toml")
    MinionService.exposed_Minion.port = conf["minion"]["port"]
    nodes = conf["minion"]["nodes"]
    if (int((localhost.split(".")[-1])) - 10) % 3 == 1:  # leader node
        for g in nodes:
            if g[0] == localhost:
                slaves.extend(g[1:])


class MinionService(rpyc.Service):
    class exposed_Minion():
        port = -1
        blocks = {}
        slave_list = []

        def __init__(self):
            pass

        def exposed_put(self, block_uuid, data):
            with open(DATA_DIR + str(block_uuid), 'wb') as f:
                f.write(data)

            # forward
            for s in slaves:
                con = rpyc.connect(s, self.port, config=RPYC_CONFIG)
                minion = con.root.Minion()
                minion.put(block_uuid, data)

            # if len(minions) > 0:
            #     self.forward(block_uuid, data, minions)

        def exposed_get(self, block_uuid):
            block_addr = DATA_DIR + str(block_uuid)
            if not os.path.isfile(block_addr):
                return None
            with open(block_addr, 'rb') as f:
                return f.read()

        # def exposed_forward(self, block_uuid, data, minions):
        #     print("8888: forwaring to:")
        #     print(block_uuid, minions)
        #     minion = minions[0]
        #     minions = minions[1:]
        #     host, port = minion
        #
        #     con = rpyc.connect(host, port=port)
        #     minion = con.root.Minion()
        #     minion.put(block_uuid, data, minions)

        def exposed_delete(self, uuid):
            file_path = DATA_DIR + str(uuid)
            if os.path.exists(file_path):
                os.remove(file_path)

            # forward
            for s in slaves:
                con = rpyc.connect(s, self.port, config=RPYC_CONFIG)
                minion = con.root.Minion()
                minion.delete(uuid)


if __name__ == "__main__":
    localhost = socket.gethostbyname(socket.gethostname())
    set_conf(localhost)
    port = MinionService.exposed_Minion.port
    # DATA_DIR += port + "/"
    # if not os.path.isdir(DATA_DIR) or not os.path.exists(DATA_DIR):
    #     os.mkdir(DATA_DIR)
    t = ThreadedServer(MinionService, port=int(port), protocol_config={"allow_public_attrs": True})
    print("Will listening on %s:%d ..." % (localhost, port))
    t.start()
