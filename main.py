from threading import  Thread
import argparse
import time

from config import statics
from miner import mining
from node import node
from api import flask_server
from helper import *

#   *** ARG PARSER ***
parser = argparse.ArgumentParser(description=
    '''
        Container to start the NODE or the MINER. You have to select at least one function. All 
        functions are listed on here:
    ''', epilog=
    '''
        Enjoy it. See full code on GitHub
    '''
    )

parser.add_argument('-m', '--miner', action='store_true', help='Start a Miner')
parser.add_argument('-n', '--node', action='store_true', help='Start a NODE')
parser.add_argument('-api', '--api', action='store_true', help='Start the API')
parser.add_argument('-l', '--lite', action='store_true', help='Lite version: No user interface, ...')
args = parser.parse_args()

def node_manager():
    while 1:
        time.sleep(5)
        for n in statics.NODES:
            # test nodes
            result = get_json_from_site(n + "/get/nodes")
            if result is None:
                # Node is dead
                statics.NODES.remove(n)
                continue

            for n2 in result:
                if n2 not in statics.NODES:
                    statics.NODES.append(n2)

def user_interface():
    while 1:
        try:
            _input = input("")

            if _input == "exit":
                statics.CLOSING = True

        except (KeyboardInterrupt, EOFError):
            break

def main():
    # Start node manager
    node_manager_thread = Thread(target=node_manager)
    node_manager_thread.daemon = True
    node_manager_thread.name = "Node Manager Thread"
    node_manager_thread.start()

    # Start user Interface
    if args.lite is False:
        statics.LITE_ACTIVE = False
        user_thread = Thread(target=user_interface)
        user_thread.daemon = True
        user_thread.name = "User Interface"
        user_thread.start()
        statics.RUNNING_PROCESSES.append(user_thread)
        print("[INFO] User interface is available")

    if args.node:
        # Start node
        node_thread = Thread(target=node.start_node)
        node_thread.daemon = True
        node_thread.name = "Node Thread"
        node_thread.start()
        statics.RUNNING_PROCESSES.append(node_thread)

    if args.miner:
        # Start miner
        miner_thread = Thread(target=mining.start_miner)
        miner_thread.daemon = True
        miner_thread.name = "Miner Thread"
        miner_thread.start()
        statics.RUNNING_PROCESSES.append(miner_thread)

    if args.api:
        # Start API
        flask_server.start_api()

    
    print("[INFO] Every task is running")
    # Wait to complete or close statement gived
    while len(statics.RUNNING_PROCESSES) > 0 and statics.CLOSING is False:
        try:
            for process in statics.RUNNING_PROCESSES:
                # Remove dead threads
                if process.is_alive() is False:
                    statics.RUNNING_PROCESSES.remove(process)

            time.sleep(0.25)
        except (KeyboardInterrupt, EOFError):
            print("Keyboard Interrupt detected")
            break
    
    print("[INFO] Closing everything...")
    statics.CLOSING = True
    

if __name__ == "__main__":
    main()