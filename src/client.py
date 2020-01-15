import os
import uuid  # DO NOT DELETE
import rpyc
from model import FileMetaData
from config import RPYC_CONFIG

local_cache = {}


def query_from_server(query):
    print(query)
    ans = input()
    if ans == 'y':
        return True
    else:
        return False
    # return True


def send_to_minion(block_uuid, data, minion_info):
    host, port = minion_info
    con = rpyc.connect(host, port=port, config=RPYC_CONFIG)
    minion = con.root.Minion()
    minion.put(block_uuid, data)


def read_from_minion(block_uuid, minion):
    host, port = minion
    con = rpyc.connect(host, port=port, config=RPYC_CONFIG)
    minion = con.root.Minion()
    return minion.get(block_uuid)


def get(master, f_name, local_path):
    if f_name in local_cache:
        r_file_table, update, timestamp = master.get_file_table_entry(f_name, local_cache[f_name].time_stamp)
    else:
        r_file_table, update, timestamp = master.get_file_table_entry(f_name)
    if update:
        local_cache[f_name] = FileMetaData(f_name, r_file_table, timestamp)
        file_table = r_file_table
    else:
        file_table = local_cache[f_name].blocks

    if not file_table:
        print("File not found, please check your input")
        return
    with open(local_path, 'wb') as f:
        for block in file_table:
            block_uuid, minion_info = block
            data = read_from_minion(block_uuid, minion_info)
            f.write(data)
    master.read_finished(f_name)


def put(master, source, destination):
    if not os.path.isfile(source):
        print("The path \'%s\' is not a file or does not exist!" % source)
        return
    if not os.access(source, os.R_OK):
        print("Permission denied. You do not have the read access to the \'%s\'" % source)
        return
    size = os.path.getsize(source)
    blocks, timestamp = master.write(destination, size, query_from_server)
    local_cache[destination] = FileMetaData(destination, blocks, timestamp)

    with open(source, 'rb') as f:
        for b in blocks:
            data = f.read(master.get_block_size())
            block_uuid, minion_info = b
            send_to_minion(block_uuid, data, minion_info)
    master.write_finished(destination)


def delete(master, dest):
    master.delete(dest)


def ls(master):
    file_list = master.get_list()
    for f in file_list:
        print(f)


def print_usage():
    print("Usage:")
    print("1. View files in the distributed filesystem:")
    print("   Command: ls")
    print("2. Put local file in the distributed filesystem:")
    print("   Command: put <local_file_name> <dest_file_name>")
    print("3. Get file from the distributed filesystem:")
    print("   Command: get <dest_file_name> <path_to_save_the_file>")
    print("4. Delete file in the distributed filesystem:")
    print("   Command: del <dest_file_name")
    print("\nType \'exit\' to exit FinalDFS client.")


def print_hello():
    print("Welcome to FinalDFS Client V1.0!")


def main():
    MASTER_IP = "localhost"
    MASTER_PORT = 2131
    con = rpyc.connect(MASTER_IP, port=MASTER_PORT, config=RPYC_CONFIG)
    print("Connected to master@%s:%d." % (MASTER_IP, MASTER_PORT))
    master = con.root.Master()
    print_hello()
    print_usage()
    while True:
        print(">>> ", end="")
        whole_command = input().split(" ")

        main_command = whole_command[0]

        if main_command == '':
            continue

        if main_command == "get":
            if len(whole_command) < 3:
                print("**   Command: get <dest_file_name> <path_to_save_the_file>")
                continue
            get(master, whole_command[1], whole_command[2])
        elif main_command == "put":
            if len(whole_command) < 3:
                print("**   Command: put <local_file_name> <dest_file_name>")
                continue
            put(master, whole_command[1], whole_command[2])
        elif main_command == "del":
            if len(whole_command) < 2:
                print("**   Command: Command: del <dest_file_name>")
                continue
            delete(master, whole_command[1])
        elif main_command == "ls":
            ls(master)
        elif main_command == "exit":
            exit(0)
        else:
            print("Unrecognized command, please retry.")


if __name__ == "__main__":
    main()
