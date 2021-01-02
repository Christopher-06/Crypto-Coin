from threading import Thread
from config import *
import helper

from base64 import b64encode, b64decode
from datetime import datetime, timezone
import time
import json

import requests


class Transaction():
    def __init__(self, sender : str, id : str, op_name : str, data : dict, signature = 0, my_hash = "", timestamp = "") -> None:
        self.sender = sender
        self.id = id
        self.op_name = op_name
        self.data = data
        self.signature = signature

        self.timestamp = timestamp
        if self.timestamp is "":
            self.timestamp = datetime.now(timezone.utc).replace(tzinfo=None).strftime(format = "%d.%m.%Y %H:%M:%S")

        self.my_hash = my_hash
        if self.my_hash == "":
            self.my_hash = helper.hash_str(json.dumps(self.to_json(with_my_hash=False)))
                                
    def check_valid(self, only_hash = False) -> bool:       
        if only_hash:
            if helper.hash_str(json.dumps(self.to_json(with_my_hash=False))) == self.my_hash:
                return True
            else:
                return False

        return True

    def prove_signature(self) -> bool:
        ''' Sender is the public key '''
        testing = {
            "data" : self.data,
            "op_name" : self.op_name,
            "sender" : self.sender, 
            "id" : self.id, 
            "timestamp" : self.timestamp
        }
        test_str = helper.hash_str(json.dumps(testing))

        verify = helper.Signature.verify(self.signature, self.sender)
        if test_str[0:14] == verify:
            return True

        return False

    def to_json(self, with_my_hash = True) -> dict:
        obj = {
            "id" : self.id,
            "sender" : str(self.sender),
            "op" : self.op_name,
            "data" : self.data,
            "signature" : self.signature,
            "timestamp" : self.timestamp
        }
        if with_my_hash:
            obj["hash"] = self.my_hash

        return obj       

    def broadcast(self) -> bool:
        '''Send transaction to all listed Nodes'''
        if self.signature == 0:
           return False

        # Start all threads
        threads, responses = [], []
        for n in statics.NODES:
            def do(addr):
                try:
                    r = requests.post(f'{addr}/post/transaction', 
                    json={"sender": self.sender, "id" : self.id, "op" : self.op_name, "data" : self.data, "signature" : self.signature, "timestamp" : self.timestamp})
                    responses.append(r)
                except Exception as e:
                    print("frsfd")

            t = Thread(target=do, args=(n, ), daemon=True)
            t.start()
            threads.append(t)

        # wait until all completes or one says: ok
        while len(threads) > 0 or len(responses) > 0:
            for t in threads:
                if not t.isAlive():
                    threads.remove(t)

            if len(responses) > 0:
                if responses[0].status_code == 200:
                    # Succes
                    return True
                responses.pop(0)

            
        # Nobody said: ok
        return False

    @staticmethod
    def sign_transaction(trans, keys) -> int:
        sign_str = helper.hash_str(json.dumps({"data" : trans.data, "op_name" : trans.op_name,"sender" : trans.sender, "id" : trans.id, "timestamp" : trans.timestamp}))[0:14]
        return helper.Signature.signe_string(sign_str, keys)

class Block():
    def __init__(self, id = -1, prev_hash = None, my_hash = None, transactions = None, timestamp = "", nonce = 0) -> None:
        if transactions is None:
            # Otherwise it will have always the same list
            transactions = []

        # Block
        self.id = id
        self.prev_hash = prev_hash
        self.my_hash = my_hash
        self.transactions = transactions
        self.nonce = nonce
        self.timestamp = timestamp

    def to_json(self, with_my_hash = True, only_transactions_hashes = False) -> dict:
        obj = {
            "id" : self.id,
            "prev_hash" : self.prev_hash,
            "transactions" : [trans.to_json() for trans in self.transactions],
            "nonce" : self.nonce,
            "timestamp" : self.timestamp
        }

        if with_my_hash:
            obj["hash"] = self.my_hash
        if only_transactions_hashes:
            obj["transactions"] = [trans.my_hash for trans in self.transactions]

        return obj

    def append_transaction(self, trans : Transaction) -> bool:
        # Only one transaction by a sender per block
        for trans_check in self.transactions:
            if trans_check.sender == trans.sender:
                # Prevent double spend problem
                return False

        self.transactions.append(trans)
        return True

    def calc_hash(self, in_place=True) -> str:
        block_str = json.dumps(self.to_json(with_my_hash=False, only_transactions_hashes=True)).replace(" ", "")
        hash = helper.hash_str(block_str)

        if in_place:
            self.my_hash = hash

        return hash

    def check_valid(self, only_hash_start_seq=False) -> bool:
        if only_hash_start_seq:
            if self.my_hash[:len(HASH_START_SEQ)] == HASH_START_SEQ:
                return True
            else:
                return False

        if self.calc_hash(in_place=False) != self.my_hash:
            # Hash is wrong
            return False

        return True

    #   *** STATIC METHODS ***  

    @staticmethod
    def add_to_blockchain(block, adjust_values = True) -> bool:
        if adjust_values:
            block.id = len(statics.CHAIN)
            block.prev_hash = statics.CHAIN[-1].my_hash
            block.nonce = 0
            block.my_hash = ""

        if len(block.transactions) == 0:
            # No transaction are listed
            return False

        statics.CHAIN.append(block)
        return True
        

def init_blockchain():
    transes = [Transaction("Genesis", "0161060", "create first block", {}, 0)]
    if TEST_MODE:
        keys = (596995943162869979, 658656388049988001)
        msg_keys = helper.Message_Encryption.generate_rsa_keys()
        # Create admin account
        transes.append(Transaction(str(keys[0] * keys[1]), "0", "account_creation", {"msg_public_key" : b64encode(msg_keys[0]).decode()}, 0))
        transes.append(Transaction(str(keys[0] * keys[1]), "1", "account_setting", { "links" : [], "long_description" : "My name is Admin, I am 18 years old and own this whole thing. Have fun while using it and donate something to me", "profile_image" : "", "name" : "Admin", "short_description" : "Hello, I am the admin of this whole ecosystem", "location" : "Germany"}, 0))
        # Transfer to admin
        msg_obj_receiver = helper.Message_Encryption.encrypt_str(msg_keys[0], "Hello World")
        transes.append(Transaction("0", "2", "transfer", {"amount" : int(2000), "receiver" : str(keys[0] * keys[1]), "message" : {"sender" : {}, "receiver" : msg_obj_receiver}}, 0))

    b = Block(id=0, prev_hash='', my_hash='',
             transactions=transes,
             timestamp=datetime.now(timezone.utc).replace(tzinfo=None).strftime(format="%d.%m.%Y %H:%M:%S"),
             nonce=0)
    
    statics.PENDING_BLOCK = b
    statics.CURRENT_BLOCK = Block(id=1, 
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None).strftime(format="%d.%m.%Y %H:%M:%S"))

    
    
