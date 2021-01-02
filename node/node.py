from threading import Thread
import time
import json
import random
from datetime import datetime, timedelta, timezone
import sys
sys.path.append(".")

from node import remove_old
from node import server
from config import *
from blockchain import *
from transaction_rules import test_trans_id

import requests
from operator import itemgetter

def open_transactions_agent():
    while 1:
        while statics.SYNC_BLOCKCHAIN:
            time.sleep(0.025)

        if len(statics.OPEN_TRANSACTIONS) == 0:
            # wait to start
            time.sleep(0.025)
        else:
            # Get random item
            trans = random.choice(statics.OPEN_TRANSACTIONS)

            if test_trans_id(trans):
                # Check if transaction is already inside
                # No double spending, when chain is synced for example...
                statics.CURRENT_BLOCK.append_transaction(trans)
            statics.OPEN_TRANSACTIONS.remove(trans)
      

def pending_block_agent():
    while 1:
        while statics.SYNC_BLOCKCHAIN:
            time.sleep(0.025)
            statics.SOLUTIONS.clear()

        if statics.PENDING_BLOCK is None:
            # Nothing pending -> no solutions
            statics.SOLUTIONS.clear()

            # test if currentblock is ready to set on pending
            if len(statics.CURRENT_BLOCK.transactions) >= MIN_BLOCK_TRANSACTIONS:
                # got needed transactions -> test time delta
                block_time = datetime.now(timezone.utc).replace(tzinfo=None).strptime(statics.CURRENT_BLOCK.timestamp, "%d.%m.%Y %H:%M:%S")
                now_time = datetime.now(timezone.utc).replace(tzinfo=None)

                if now_time >= (block_time + timedelta(seconds=MIN_BLOCK_TIME_DELTA)):
                    # block is old enough -> enter
                    b = Block(id=len(statics.CHAIN) + 1, # + 1 because one is always pending 
                        timestamp=datetime.now(timezone.utc).replace(tzinfo=None).strftime(format="%d.%m.%Y %H:%M:%S"))

                    statics.CURRENT_BLOCK.prev_hash = statics.CHAIN[-1].my_hash
                    statics.PENDING_BLOCK = statics.CURRENT_BLOCK
                    statics.CURRENT_BLOCK = b


        pending_b = statics.PENDING_BLOCK
        for nonce in statics.SOLUTIONS:
            # Test all solutions
            pending_b.nonce = nonce
            pending_b.calc_hash()
            if pending_b.check_valid(only_hash_start_seq=True):
                # Succes, have a right hash
                statics.CHAIN.append(pending_b)
                statics.PENDING_BLOCK = None
                statics.SOLUTIONS.clear()
                break


def sync_blockchain_agent():
    '''Compare own blockchain to other'''
    while 1:
        # Check who has the longest thing
        chain_lengths = [] # (len, link)
        get_threads = []

        for n in statics.NODES:
            # Get len from all
            def get_len(address):
                try:
                    r = requests.get(address + "/get/chain-len")
                except:
                    return

                if r.status_code == 200:
                    # TODO: Implement a check_valid function
                    length = int(json.loads(r.text)["len"])
                    chain_lengths.append((length, address))

            t = Thread(target=get_len, args=(n, ), daemon=True)
            t.start()
            get_threads.append(t)
        

        for t in get_threads:
            # Wait for all to finish (max. 10 sec)
            # --> No one blocks this process
            t.join(timeout=10)
        
        if len(chain_lengths) == 0:
            # No one else is there
            time.sleep(1)
            continue

        chain_lengths = sorted(chain_lengths, key=itemgetter(0)) # last element is the longest
        if chain_lengths[-1][0] <= len(statics.CHAIN):
            # Got longest one -> next time
            time.sleep(1)
            continue
        
        # Get data by the longest and adjust my chain
        # TODO: Valid all inputs
        statics.SYNC_BLOCKCHAIN = True

        try:
            r = requests.get(chain_lengths[-1][1] + "/get/all")
            result = json.loads(r.text)
        except:
            continue
                        
        # Set current
        if "current" in result:
            current = result["current"]
            statics.CURRENT_BLOCK = Block(id=current["id"], prev_hash=current["prev_hash"], my_hash="", 
                        transactions=[Transaction(sender=trans["sender"], op_name=trans["op"], data=trans["data"], signature=trans["signature"], my_hash=trans["hash"], timestamp=trans["timestamp"], id=trans["id"]) for trans in current["transactions"]],
                        timestamp=current["timestamp"], nonce=0)
        # Set pending
        if "pending" in result:
            pending = result["pending"]
            statics.PENDING_BLOCK = Block(id=pending["id"], prev_hash=pending["prev_hash"], my_hash="", 
                        transactions=[Transaction(sender=trans["sender"], op_name=trans["op"], data=trans["data"], signature=trans["signature"], my_hash=trans["hash"], timestamp=trans["timestamp"], id=trans["id"]) for trans in pending["transactions"]],
                        timestamp=pending["timestamp"], nonce=0)
        else:
            statics.PENDING_BLOCK = None

        # Adjust my chain
        chain = result["chain"]
        statics.CHAIN = [Block(id=b["id"], prev_hash=b["prev_hash"], my_hash="", 
                        transactions=[Transaction(sender=trans["sender"], op_name=trans["op"], data=trans["data"], signature=trans["signature"], my_hash=trans["hash"], timestamp=trans["timestamp"], id=trans["id"]) for trans in b["transactions"]],
                        timestamp=b["timestamp"], nonce=0) for b in chain]

        statics.SYNC_BLOCKCHAIN = False


       

def start_node():
    init_blockchain()
    server.start_server()

    # Pending agent
    pending_agent_thread = Thread(target=pending_block_agent)
    pending_agent_thread.daemon = True
    pending_agent_thread.name = "Pending block Agent"
    pending_agent_thread.start()

    # Open Transaction agent
    open_trans_agent_thread = Thread(target=open_transactions_agent)
    open_trans_agent_thread.daemon = True
    open_trans_agent_thread.name = "Open Transaction Agent"
    open_trans_agent_thread.start()

    # Remove Old agent
    remove_agent_agent_thread = Thread(target=remove_old.agent)
    remove_agent_agent_thread.daemon = True
    remove_agent_agent_thread.name = "Remove Old Agent"
    remove_agent_agent_thread.start()

    # Sync chain agent
    sync_chain_agent_thread = Thread(target=sync_blockchain_agent)
    sync_chain_agent_thread.daemon = True
    sync_chain_agent_thread.name = "Sync Blockchain Agent"
    sync_chain_agent_thread.start()


if __name__ == "__main__":
    # If you run the script solo
    # --> Better performance
    start_node()