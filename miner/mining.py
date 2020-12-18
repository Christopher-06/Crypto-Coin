from threading import Thread
import time
import random
import sys
sys.path.append(".")
from blockchain import *
from helper import get_json_from_site, hash_str
from config import *

pending = [None] 
solutions = []

def mine():
    while len(pending) == 0:
        time.sleep(0.5)
    
    b = None
    while 1:
        # pending[0] is none when nothing to do
        b = pending[0]

        if b is None:
            # Nothing to do
            time.sleep(0.02)
            continue

        # Calc hash
        b.nonce = random.randint(0, sys.maxsize)
        b.calc_hash()
        if b.check_valid(only_hash_start_seq=True):
            solutions.append(b.nonce)
        

def manager():   
    while 1:
        while len(statics.NODES) == 0:
            print("", end=f"\r Mining Threads: {MAX_MINING_THREADS}     NO NODES                        ")
            time.sleep(0.05)

        current_node = statics.NODES[0]
        while len(solutions) > 0:
            print("", end=f"\r Mining Threads: {MAX_MINING_THREADS}     GOT SOLUTION                           ")

            # Got a solution -> Tell everybody
            for n in statics.NODES:
                Thread(target=get_json_from_site, args=(n + "/set/nonce?nonce=" + str(solutions[0]),)).start()
            
            # Succes, the responses does not matter
            solutions.pop(0)
            pending.append(None)

        while len(pending) > 1:
            # remove old ones
            pending.pop(0)

        result = get_json_from_site(current_node + "/get/pending")
        if result is None:
            # Node is dead, will be removed
            continue

        if "status" in result and "waiting" in result["status"]:
            # No block for pending --> wait
            pending.append(None)
            print("", end=f"\r Mining Threads: {MAX_MINING_THREADS}     WAITING                    ")
            continue
    
        # Got job
        b = Block(id=result["id"], prev_hash=result["prev_hash"], my_hash="", 
                    transactions=[Transaction(sender="", op_name="", data="", signature="", my_hash=trans_hash, timestamp="") for trans_hash in result["transactions"]],
                    timestamp=result["timestamp"], nonce=0)
        pending.append(b)

        print("", end=f"\r Mining Threads: {MAX_MINING_THREADS}     Current Block ID: {b.id}           ")

        





        

def start_miner():
    if len(statics.NODES) == 0:
        # Add localhost if nothing else is defined
        statics.NODES.append(f"http://{NODE_ADDRESS}:{NODE_PORT}")

    for i in range(MAX_MINING_THREADS):
        t = Thread(target=mine)
        t.daemon = True
        t.name = "Miner - " + str(i + 1)
        t.start()
    manager()

if __name__ == "__main__":
    # If you run the script solo
    # --> Better performance
    start_miner()