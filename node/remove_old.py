import sys
sys.path.append(".")


from node import server
from config import *
from blockchain import *


def remove_friend(block_index : int, trans_index : int) -> bool:
    '''Remove old Add and Remove Data from Transaction, when it revoke it other''' 
    # Prepare Sender and Target
    sender = statics.CHAIN[block_index].transactions[trans_index].sender
    target = statics.CHAIN[block_index].transactions[trans_index].data["target"]

    for index, block in enumerate(statics.CHAIN):
        if index >= block_index:
            # Cannot reach it anymore
            break
        
        for trans in block.transactions:
                if trans.op_name == "set_friend" and trans.data != {} and trans.data["type"] == "add":
                    # An add transaction -> Test Sender and Target
                    if trans.sender == sender and trans.data["target"] == target:
                        # Got correct -> Delete both
                        trans.data = {}
                        statics.CHAIN[block_index].transactions[trans_index].data = {}
                        return True
    return False


def remove_account_settings(block_index : int, trans_index : int) -> bool:
    '''Remove old Account Settings, when it it updated''' 

    # Prepare
    sender = statics.CHAIN[block_index].transactions[trans_index].sender

    for index, block in enumerate(statics.CHAIN):
        if index >= block_index:
            # Cannot reach it anymore
            # Newest acc settings transaction is unseen
            break
        
        for trans in block.transactions:
                if trans.op_name == "account_setting" and trans.data != {} and trans.sender == sender:
                    # An old acc settings transaction by the sender -> delete
                    trans.data = {}
                    return True
                    
    return False


def agent():
    # Remove old data like account_settings, add and remove friend, very old transfers
    while 1:
        for block_index, block in enumerate(statics.CHAIN):

            if((len(statics.CHAIN) - block_index) <= MIN_BLOCKS_BEFORE_REMOVE):
                # Need more blocks between them
                break

            for trans_index, trans in enumerate(block.transactions):
                if statics.SYNC_BLOCKCHAIN:
                    break
                
                if trans.data == {}:
                    # already cleared
                    continue

                if trans.op_name == "account_setting":
                    remove_account_settings(block_index, trans_index)

                if trans.op_name == "set_friend" and trans.data["type"] == "remove":
                    remove_friend(block_index, trans_index)

                if trans.op_name == "transfer":
                    pass