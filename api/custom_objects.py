import json
import sys
sys.path.append(".")
from config import *
from blockchain import *
import helper

from base64 import b64encode, b64decode
import uuid

import requests

class Account():
    def __init__(self, account_keys, msg_keys, identifier = "") -> None:
        self.sender = account_keys[0] * account_keys[1]
        self.account_keys = account_keys
        self.msg_keys = msg_keys

        self.last_notification_block_id = -1
        self.notifications = []

        self.identifier = identifier
        if self.identifier == "":
            # Make a random one
            self.identifier = uuid.uuid4().hex.upper()

    def send_money(self, receiver_acc_key, receiver_msg_key, amount, message) -> bool:
        msg_obj_sender = helper.Message_Encryption.encrypt_str(self.msg_keys[0], message)
        msg_obj_receiver = helper.Message_Encryption.encrypt_str(receiver_msg_key, message)
        data = {"amount" : int(amount), "receiver" : str(receiver_acc_key), "message" : {"sender" : msg_obj_sender, "receiver" : msg_obj_receiver}}
        op_name = "transfer"
        id = uuid.uuid4().hex.upper() + uuid.uuid4().hex.upper()
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).strftime(format="%d.%m.%Y %H:%M:%S")
        #signature = Transaction.sign_transaction(Transaction(self.sender, id, op_name, data, timestamp = timestamp), self.account_keys)

        # Setup Transaction
        trans = Transaction(self.sender, id, op_name, data, timestamp=timestamp)
        trans.signature = Transaction.sign_transaction(trans, self.account_keys)
        
        # Send
        return trans.broadcast()

        r = requests.post(f'http://{NODE_ADDRESS}:{NODE_PORT}/post/transaction', json={"sender": self.sender, "id" : id, "op" : op_name, "data" : data, "signature" : signature})
        if r.status_code != 200:
            return False
        return True

    def account_settings(self, name : str, profile_image : str, short_description : str, long_description : str, links : list, location : str) -> bool:
        data = {"name" : name, "profile_image" : profile_image, "short_description" : short_description, "long_description" : long_description, "links" : links, "location" : location}
        op_name = "account_setting"
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).strftime(format="%d.%m.%Y %H:%M:%S")
        id = uuid.uuid4().hex.upper() + uuid.uuid4().hex.upper()

       # signature = Transaction.sign_transaction(Transaction(self.sender, id, op_name, data, timestamp = timestamp), self.account_keys)
        
        # Setup Transaction
        trans = Transaction(self.sender, id, op_name, data, timestamp=timestamp)
        trans.signature = Transaction.sign_transaction(trans, self.account_keys)
        
        # Send
        return trans.broadcast()

        r = requests.post(f'http://{NODE_ADDRESS}:{NODE_PORT}/post/transaction', json={"sender": self.sender, "id" : id, "op" : op_name, "data" : data, "signature" : signature})
        if r.status_code != 200:
            return False
        return True

    def add_friend(self, target : str) -> bool:
        data = {"type" : "add", "target" : target}
        op_name = "set_friend"
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).strftime(format="%d.%m.%Y %H:%M:%S")
        id = uuid.uuid4().hex.upper() + uuid.uuid4().hex.upper()

        #signature = Transaction.sign_transaction(Transaction(self.sender, id, op_name, data, timestamp = timestamp), self.account_keys)
        
        # Setup Transaction
        trans = Transaction(self.sender, id, op_name, data, timestamp=timestamp)
        trans.signature = Transaction.sign_transaction(trans, self.account_keys)
        
        # Send
        return trans.broadcast()

        r = requests.post(f'http://{NODE_ADDRESS}:{NODE_PORT}/post/transaction', json={"sender": self.sender, "id" : id, "op" : op_name, "data" : data, "signature" : signature})
        if r.status_code != 200:
            return False
        return True

    def remove_friend(self, target : str) -> bool:
        data = {"type" : "remove", "target" : target}
        op_name = "set_friend"
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).strftime(format="%d.%m.%Y %H:%M:%S")       
        id = uuid.uuid4().hex.upper() + uuid.uuid4().hex.upper()
        #signature = Transaction.sign_transaction(Transaction(self.sender, id, op_name, data, timestamp = timestamp), self.account_keys)

        # Setup Transaction
        trans = Transaction(self.sender, id, op_name, data, timestamp=timestamp)
        trans.signature = Transaction.sign_transaction(trans, self.account_keys)
        
        # Send
        return trans.broadcast()

        r = requests.post(f'http://{NODE_ADDRESS}:{NODE_PORT}/post/transaction', json={"sender": self.sender, "id" : id, "op" : op_name, "data" : data, "signature" : signature})
        if r.status_code != 200:
            return False
        return True


    @staticmethod
    def create_account():
        # Generate keys and init account obj
        account_keys = helper.Signature.generate_key_pair()
        msg_keys = helper.Message_Encryption.generate_rsa_keys()
        acc = Account(account_keys, msg_keys) 
        id = uuid.uuid4().hex.upper() + uuid.uuid4().hex.upper()
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).strftime(format="%d.%m.%Y %H:%M:%S")
        data = {"msg_public_key" : b64encode(msg_keys[0]).decode()}
        op_name = "account_creation"

        # Setup Transaction
        trans = Transaction(acc.sender, id, op_name, data, timestamp=timestamp)
        trans.signature = Transaction.sign_transaction(trans, account_keys)
        
        # Send
        if trans.broadcast():
            # Succes
            return acc
        
        # Error
        return None
        
        signature = Transaction.sign_transaction(Transaction(acc.sender, id, op_name, data, timestamp = timestamp), account_keys)    
        
        r = requests.post(f'http://{NODE_ADDRESS}:{NODE_PORT}/post/transaction', json={"sender": acc.sender, "id" : id, "op" : op_name, "data" : data, "signature" : signature, "timestamp" : timestamp})

        if r.status_code != 200:
            # Something went wrong
            return None
        
        return acc


