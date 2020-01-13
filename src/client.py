import rpyc
import sys
import os
import logging
import uuid

from model import file_metadata

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)
local_cache = {}


def query_from_server(query):
    print(query)
    ans = input()
    if ans == 'y':
        return True
    else:
        return False
    # return True


def send_to_minion(block_uuid, data, minionInfo):
    host, port = minionInfo
    con = rpyc.connect(host, port=port)
    minion = con.root.Minion()
    minion.put(block_uuid, data)


def read_from_minion(block_uuid, minion):
    host, port = minion
    con = rpyc.connect(host, port=port)
    minion = con.root.Minion()
    return minion.get(block_uuid)


def get(master, f_name, local_path):
    if f_name in local_cache:
        r_file_table, update, timestamp = master.get_file_table_entry(f_name, local_cache[f_name].time_stamp)
    else:
        r_file_table, update, timestamp = master.get_file_table_entry(f_name)
    if update:
        local_cache[f_name] = file_metadata(f_name, r_file_table, timestamp)
        file_table = r_file_table
    else:
        file_table = local_cache[f_name].blocks

    if not file_table:
        LOG.info("404: file not found")
        return
    with open(local_path, 'w') as f:
        for block in file_table:
            block_uuid, minionInfo = block
            data = read_from_minion(block_uuid, minionInfo)
            f.write(data)
    master.read_finished(f_name)


def put(master, source, destination):
    size = os.path.getsize(source)
    blocks, timestamp = master.write(destination, size, query_from_server)
    local_cache[destination] = file_metadata(destination, blocks, timestamp)
    with open(source) as f:
        for b in blocks:
            data = f.read(master.get_block_size())
            block_uuid, minionInfo = b
            send_to_minion(block_uuid, data, minionInfo)
    master.write_finished(destination)


def delete(master, dest):
    master.delete(dest)


def main(args):
    con = rpyc.connect("localhost", port=2131)
    master = con.root.Master()

    if args[1] == "get":
        get(master, args[2], args[3])
    elif args[1] == "put":
        put(master, args[2], args[3])
    elif args[1] == "del":
        delete(master, args[2])
    else:
        LOG.error("try 'put srcFile destFile OR get file'")


if __name__ == "__main__":
    args = sys.argv
    main(args)
