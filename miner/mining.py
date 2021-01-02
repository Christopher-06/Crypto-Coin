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
average_hashes_per_sec = [0]

def mine():
    while len(pending) == 0:
        time.sleep(0.5)
    
    b = None
    times = 0
    start_time = time.time()
    while 1:
        # pending[0] is none when nothing to do
        b = pending[0]

        if b is None:
            # Nothing to do
            time.sleep(0.002)
            times = 0
            start_time = time.time()
            continue

        # Calc hash
        times += 1
        b.nonce = random.randint(0, sys.maxsize)
        b.calc_hash()
        if b.check_valid(only_hash_start_seq=True):
            solutions.append(b.nonce)

            try:
                hashes_per_sec = (times / (time.time() - start_time)) * MAX_MINING_THREADS

                if(average_hashes_per_sec[0] == 0):
                    average_hashes_per_sec[0] = hashes_per_sec
                else:
                    average_hashes_per_sec[0] += hashes_per_sec
                    average_hashes_per_sec[0] /= 2
            except:
                pass
            times = 0
            start_time = time.time()
        

def manager():   
    while 1:
        while len(statics.NODES) == 0:
            print("", end=f"\r Mining Threads: {MAX_MINING_THREADS}     NO NODES    Hashes/Sec: {average_hashes_per_sec[0]}                        ")
            time.sleep(0.05)

        current_node = statics.NODES[0]
        for index, _ in enumerate(solutions):
            #break
            print("", end=f"\r Mining Threads: {MAX_MINING_THREADS}     GOT SOLUTION    Hashes/Sec: {average_hashes_per_sec[0]}                        ")

            # Got a solution -> Tell everybody
            for n in statics.NODES:
                Thread(target=get_json_from_site, args=(n + "/set/nonce?nonce=" + str(solutions[0]),)).start()
            
            # Succes, the responses does not matter
            solutions.pop(0)
            pending.append(None)

            if index > 10:
                break

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
            print("", end=f"\r Mining Threads: {MAX_MINING_THREADS}     WAITING    Hashes/Sec: {average_hashes_per_sec[0]}                        ")
            continue
    
        # Got job
        b = Block(id=result["id"], prev_hash=result["prev_hash"], my_hash="", 
                    transactions=[Transaction(sender="", op_name="", data="", signature="", my_hash=trans_hash, timestamp="") for trans_hash in result["transactions"]],
                    timestamp=result["timestamp"], nonce=0)
        pending.append(b)

        print("", end=f"\r Mining Threads: {MAX_MINING_THREADS}     Current Block ID: {b.id}    Hashes/Sec: {average_hashes_per_sec[0]}                        ")

        





        

def start_miner():
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