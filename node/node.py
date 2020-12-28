from threading import Thread
import time
import random
from datetime import datetime, timedelta, timezone
import sys
sys.path.append(".")

from node import remove_old
from node import server
from config import *
from blockchain import *


def open_transactions_agent():
    while 1:
        if len(statics.OPEN_TRANSACTIONS) == 0:
            # wait to start
            time.sleep(0.025)
        else:
            # Get random item
            trans = random.choice(statics.OPEN_TRANSACTIONS)

            if statics.CURRENT_BLOCK.append_transaction(trans):
                statics.OPEN_TRANSACTIONS.remove(trans)
      

def pending_block_agent():
    while 1:
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


if __name__ == "__main__":
    # If you run the script solo
    # --> Better performance
    start_node()