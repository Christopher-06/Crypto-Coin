import sys, time
import requests
import random

sys.path.append(".")
from config import *
import helper

def blockchain_notifier():
    last_block_id = 0
    while 1:
        time.sleep(2)

        # get current chain len
        data = helper.get_json_from_site(f"http://{NODE_ADDRESS}:{NODE_PORT}/get/chain_len")
        if data is None:
            # No connection is availabe
            time.sleep(5)
            continue

        if int(data["len"] - 1) > last_block_id:
            last_block_id = int(data["len"] - 1)

            # Get block
            data = helper.get_json_from_site(f"http://{NODE_ADDRESS}:{NODE_PORT}/get/block?block_id={last_block_id}")
            if "status" in data:
                # something went wrong
                last_block_id -= 1
                continue
            
            for trans in data["transactions"]:
                # Test if sender is inside accounts
                for acc in statics.ACCOUNTS:
                    while len(acc.notifications) > 5:
                        # Remove old ones (first is always the oldest)
                        acc.notifications.pop(0)

                    if trans["op"] == "account_setting":
                        if trans["sender"] == str(acc.sender):
                            # He send it
                            acc.notifications.append({"operation" : "account_setting"})

                    if trans["op"] == "transfer":
                        # Test if I am the receiver
                        if trans["data"]["receiver"] == str(acc.sender):
                            if isinstance(trans["data"]["message"], str):
                                # Message is plain text
                                message = trans["data"]["message"]
                            else:
                                # Message is encrypted
                                message = helper.Message_Encryption.decrypt_str(acc.msg_keys[1], trans["data"]["message"]["receiver"])


                            acc.notifications.append({"operation" : "transfer", "amount" : trans["data"]["amount"], "message" : message.decode(), "sender" : str(trans["sender"])})


def blockchain_statistics():
    '''Prepare All Statistics to increase performance of statistics.html'''
    while 1:
        # Get data (by only the latest 100 blocks)
        data = helper.get_json_from_site(f"http://{NODE_ADDRESS}:{NODE_PORT}/get/all?max_chain_len=100")
        if data is None:
            # No connection is availabe
            time.sleep(5)
            continue

        # Filter all accounts out
        accounts = []
        for block in data["chain"]:
            for trans in block["transactions"]:
                if not str(trans["sender"]) in accounts:
                    accounts.append(str(trans["sender"]))
        while len(accounts) > 100:
            accounts.remove(random.choice(accounts))

        # Get names for accounts 
        for index, acc in enumerate(accounts):
            result = helper.get_json_from_site(f"http://{NODE_ADDRESS}:{NODE_PORT}/get/account?q={acc}")
            if result is None:
                # Get names
                accounts[index] = None
                continue
            
            acc = result["account"]
            accounts[index] = {"public_key" : acc["pub_key"], "name" : acc["name"], "balance" : acc["balance"]}

        # Remove broken accounts and to many
        accounts = [x for x in accounts if x]
        while len(accounts) > 50:
            accounts.remove(random.choice(accounts))

        # Get last actions and transactions_per_block
        last_actions = []
        transactions_per_block = []
        for block in reversed(data["chain"]):
            transactions_per_block.append([block["id"], len(block["transactions"])])
            for trans in block["transactions"]:
                while len(last_actions) > 30:
                    last_actions.pop(0)
                
                for acc in accounts:
                    # get sender in accounts
                    if str(trans["sender"]) == acc["public_key"]:
                        # insert into
                        last_actions.append({"op" : trans["op"], "sender" : acc["public_key"], "name" : acc["name"], "data" : trans["data"]})
                        
        # Get account_count
        result = helper.get_json_from_site(f"http://{NODE_ADDRESS}:{NODE_PORT}/get/accounts")
        if not result is None:
            statics.STATISTICS_DICT["acc_count"] = len(result["accounts"])

        # Set dict
        statics.STATISTICS_DICT["chain_len"] = int(data["chain_len"])
        statics.STATISTICS_DICT["accounts"] = accounts
        statics.STATISTICS_DICT["transactions_per_block"] = transactions_per_block
        statics.STATISTICS_DICT["last_actions"] = last_actions

