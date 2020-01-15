import logging
import os
import sys
import socket
import rpyc
from rpyc.utils.server import ThreadedServer

DATA_DIR = "/data/"
LOG = logging.getLogger(__name__)


class MinionService(rpyc.Service):
    class exposed_Minion():
        blocks = {}

        def __init__(self):
            pass

        def exposed_put(self, block_uuid, data):
            with open(DATA_DIR + str(block_uuid), 'wb') as f:
                f.write(data)
            # if len(minions) > 0:
            #     self.forward(block_uuid, data, minions)

        def exposed_get(self, block_uuid):
            block_addr = DATA_DIR + str(block_uuid)
            if not os.path.isfile(block_addr):
                return None
            with open(block_addr, 'rb') as f:
                return f.read()

        def forward(self, block_uuid, data, minions):
            print("8888: forwaring to:")
            print(block_uuid, minions)
            minion = minions[0]
            minions = minions[1:]
            host, port = minion

            con = rpyc.connect(host, port=port)
            minion = con.root.Minion()
            minion.put(block_uuid, data, minions)

        def exposed_delete(self, uuid):
            file_path = DATA_DIR + str(uuid)
            if os.path.exists(file_path):
                os.remove(file_path)


if __name__ == "__main__":
    args = sys.argv
    port = 8888
    if len(args) > 1:
        port = args[1]
    # DATA_DIR += port + "/"
    # if not os.path.isdir(DATA_DIR) or not os.path.exists(DATA_DIR):
    #     os.mkdir(DATA_DIR)
    t = ThreadedServer(MinionService, port=int(port), protocol_config={"allow_public_attrs": True})
    print("Will listening on %s:%d ..." % (socket.gethostbyname(socket.gethostname()), port))
    t.start()

