import json
import time
from threading import Thread
import sys
sys.path.append(".")
from config import *
import helper

from base64 import b64encode, b64decode
import requests, urllib3
import random
# python testing\many_bots.py

MUST_TRANSACTIONS = 500
BOT_COUNTS = 20
BOT_KEYS = [] # (acc_key, msg_key)




def create_account(acc_keys, msg_keys):
    data = {"msg_public_key" : b64encode(msg_keys[0]).decode()}
    op_name = "account_creation"
    sender = acc_keys[0] * acc_keys[1]
    testing = {
            "data" : data,
            "op_name" : op_name,
            "sender" : sender
        }
    sign_str = helper.hash_str(json.dumps(testing))[0:14]
    signature = helper.Signature.signe_string(sign_str, acc_keys)
   
    try:
        r = requests.post(f'http://{NODE_ADDRESS}:{NODE_PORT}/post/transaction', json={"sender": sender, "op" : op_name, "data" : data, "signature" : signature})
        return r.status_code
    except (requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError):
        # DDoS Protection raised
        return -1

def account_settings(acc_keys, name): 
    data = {"name" : name, "profile_image" : "www.google.com", "short_description" : "Hello, I am a tester", "long_description" : "I have send the Admin some money or will do it!", "links" : [], "location" : "Germany"}
    op_name = "account_setting"
    sender = acc_keys[0] * acc_keys[1]
    testing = {
            "data" : data,
            "op_name" : op_name,
            "sender" : sender
        }
    sign_str = helper.hash_str(json.dumps(testing))[0:14]
    signature = helper.Signature.signe_string(sign_str, acc_keys)

    try:
        r = requests.post(f'http://{NODE_ADDRESS}:{NODE_PORT}/post/transaction', json={"sender": sender, "op" : op_name, "data" : data, "signature" : signature})
        return r.status_code
    except (requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError):
        # DDoS Protection raised
        return -1

def transfer_money(acc_keys, msg_pub_key, receiver_pub_key, receiver_pub_msg, message, amount : float):
    msg_obj_sender = helper.Message_Encryption.encrypt_str(msg_pub_key, message)
    msg_obj_receiver = helper.Message_Encryption.encrypt_str(receiver_pub_msg, message)
    data = {"amount" : float(amount), "receiver" : str(receiver_pub_key), "message" : {"sender" : msg_obj_sender, "receiver" : msg_obj_receiver}}
    op_name = "transfer"
    sender = acc_keys[0] * acc_keys[1]
    testing = {
            "data" : data,
            "op_name" : op_name,
            "sender" : sender
        }
    sign_str = helper.hash_str(json.dumps(testing))[0:14]
    signature = helper.Signature.signe_string(sign_str, acc_keys)

    try:
        r = requests.post(f'http://{NODE_ADDRESS}:{NODE_PORT}/post/transaction', json={"sender": sender, "op" : op_name, "data" : data, "signature" : signature})
        return r.status_code
    except (requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError):
        # DDoS Protection raised
        return -1

def bot_live(bot_key_index):
    # Generate and Split keys   
    keys = (helper.Signature.generate_key_pair(), helper.Message_Encryption.generate_rsa_keys())
    acc_keys, msg_keys = keys
    BOT_KEYS.append(keys)

    while len(BOT_KEYS) != BOT_COUNTS:
        # wait to start together
        time.sleep(0.2)

    # Create account
    while create_account(acc_keys, msg_keys) != 200:
        # Retry until something happens
        time.sleep(1)
    time.sleep(MIN_BLOCK_TIME_DELTA)

    # Set settings
    while account_settings(acc_keys, "I am " + str(bot_key_index)) != 200:
        # Retry until something happens
        time.sleep(1) 

    # Do transactions
    for i in range(MUST_TRANSACTIONS):
        time.sleep(MIN_BLOCK_TIME_DELTA)
        rec_pub_keys, rec_msg_keys = random.choice(BOT_KEYS)
        while transfer_money(acc_keys, msg_keys[0], rec_pub_keys[0] * rec_pub_keys[1], rec_msg_keys[0], f"Transfer - {i}", 1) != 200:
            # Retry until it succeses
            time.sleep(1)

    BOT_KEYS.remove(keys)

    # Get rid of all money
    while len(BOT_KEYS) > 0:
        # Endless process, until program exits
        rec_pub_keys, rec_msg_keys = random.choice(BOT_KEYS)
        transfer_money(acc_keys, msg_keys[0], rec_pub_keys[0] * rec_pub_keys[1], rec_msg_keys[0], "Transfer", 1)
        time.sleep(MIN_BLOCK_TIME_DELTA * 5)

if __name__ == "__main__":
    print("[INFO] Creating Bots...")
    for i in range(BOT_COUNTS):
        t = Thread(target=bot_live, args=(i, ))
        t.daemon = True
        t.start()

    while  len(BOT_KEYS) == 0:
        # wait to have at least
        time.sleep(0.2)

    print("[INFO] All Bot-Threads are running")
    print("")
    while len(BOT_KEYS) > 0:
        try:
            time.sleep(0.2)
            print("", end=f"\r Bots Alive: {len(BOT_KEYS)}      ")
        except KeyboardInterrupt:
            break