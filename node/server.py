from blockchain import Transaction
from threading import Thread
from datetime import datetime
import sys
sys.path.append(".")
from config import *
from transaction_rules import check_if_valid

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
log.disabled = True

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
CORS(app)

@app.route('/')
def index():
    ''' Index site --> Show if everything is good '''
    return VERSION_INFO

@app.route('/get/all', methods=['GET'])
def get_all():
    ''' Complete Blockchain to json '''

    # Opportunity to specify a max_chain_len
    max_chain_len = request.args.get("max_chain_len")
    if max_chain_len:
        max_chain_len = int(max_chain_len)

    blocks = []
    for b in reversed(statics.CHAIN): 
        blocks.append(b.to_json())

        if not max_chain_len is None and len(blocks) >= max_chain_len:
            break

    response = {"status" : "ok", "server_time" : datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), "chain" : blocks, "chain_len" : len(statics.CHAIN)}
    if statics.PENDING_BLOCK:
        response["pending"] = statics.PENDING_BLOCK.to_json()
    if statics.CURRENT_BLOCK:
        response["current"] = statics.CURRENT_BLOCK.to_json()

    return jsonify(response), 200

@app.route('/get/pending', methods=['GET'])
def get_pending():
    ''' Gets the current pending block '''
    if statics.PENDING_BLOCK is None:
        return jsonify({"status" : "waiting"}), 200
    else:
        if request.args.get("data") is None or "mining" in request.args.get("data"):
            d = statics.PENDING_BLOCK.to_json(with_my_hash=False, only_transactions_hashes=True)
            d["nonce"] = 10101010
            return jsonify(d), 200
        if "full" in request.args.get("data"):
            return statics.PENDING_BLOCK.to_json(), 200

@app.route('/get/current', methods=['GET'])
def get_current():
    if statics.CURRENT_BLOCK is None:
        return jsonify({"status" : "waiting"}), 400
    else:
        d = statics.CURRENT_BLOCK.to_json(with_my_hash=True, only_transactions_hashes=False)
        return jsonify(d), 200

@app.route('/get/chain-len', methods=['GET'])
def get_chain_len():
    ''' Block json --> Show a specified block '''
    return jsonify({"status" : "ok", "len" : len(statics.CHAIN)}), 200

@app.route('/get/block', methods=['GET'])
def get_block():
    ''' Block json --> Show a specified block '''
    block_id = request.args.get("block_id")
    if block_id is None:
        return jsonify({"status" : "error", "info" : "no block_id is given"}), 400

    # block_id == block.id == statics.CHAIN[block_id]
    block_id = int(block_id)

    if len(statics.CHAIN) <= block_id:
        # Block does not exist
        return jsonify({"status" : "error", "info" : "block with given id does not exist"}), 404

    # Block found
    b_dict = statics.CHAIN[block_id].to_json()
    return jsonify(b_dict), 200

@app.route('/get/transaction', methods=['GET'])
def get_transaction():
    '''Get Transaction based on a given ID'''
    trans_id = request.args.get("trans_id")
    if trans_id is None:
        return jsonify({"status" : "error", "info" : "no trans_id is given"}), 400

    for block in (statics.CHAIN + [statics.PENDING_BLOCK, statics.CURRENT_BLOCK]):
        if not block is None:
            for trans in block.transactions:
                if trans.id == trans_id:
                    return jsonify(trans.to_json()), 200
    
    return jsonify({"status" : "error", "info" : "no Transaction found"}), 400

@app.route('/get/nodes', methods=['GET'])
def get_nodes():
    ''' Nodes to json & Maybe add'''

    address = request.args.get("address")
    port = request.args.get("port")

    if not port is None and not address is None:
        # Test connection
        link = f'http://{address}:{port}'    
        r = requests.get(link)
        if r.status_code == 200:
            # Test Node Version
            if VERSION_INFO in r.text:
                # Test if inside
                if not link in statics.NODES:
                    # Finally append
                    statics.NODES.append(link)

    return jsonify(statics.NODES), 200

@app.route('/get/accounts', methods=['GET'])
def get_accounts():
    '''List of all accounts (Pub keys and Name)'''
    accs = []
    for block in (statics.CHAIN + [statics.PENDING_BLOCK]):
        if block is None or block.id == 0:
            # Maybe the pending block or genesis
            continue

        for trans in block.transactions:
            if trans.op_name == "account_setting":
                # Only add, when account_settings is availabe
                # --> Get Name and force User to do some Settings
                sender_str = str(trans.sender)
                for index, acc_dict in enumerate(accs):
                    # Remove old item
                    if acc_dict["public_key"] == sender_str:
                        accs.pop(index)
                        break
                
                if len(str(trans.data["name"])) > 1:
                    # Only add if a name is available
                    accs.append({"public_key" : sender_str, "name" : trans.data["name"], "profile_image" : trans.data["profile_image"]})
    
    return jsonify({"status" : "ok", "accounts" : accs}), 200

@app.route('/get/account', methods=['GET'])
def get_account():
    '''Get a specific account'''
    pub_key = request.args.get("q")
    if pub_key is None:
        return jsonify({"status" : "error", "info" : "no q is given"}), 400

    # Get acc
    transes = []
    acc = {"pub_key" : str(pub_key), "msg_pub_key" : "", "balance" : int(1000 if TEST_MODE else 0), "name" : "", "links" : [], "profile_image" : "", "transactions" : [], "friends" : [], "location" : "", "long_description" : "", "short_description" : ""}

    for block in (statics.CHAIN + [statics.PENDING_BLOCK]):
        if block is None:
            # Maybe pending block
            continue

        for trans in block.transactions:
            if str(trans.sender) == pub_key:
                transes.append(trans.to_json())
                if trans.op_name == "account_setting" and trans.data != {}:
                    acc["name"] = trans.data["name"]
                    acc["links"] = trans.data["links"]
                    acc["location"] = trans.data["location"]
                    acc["profile_image"] = trans.data["profile_image"]
                    acc["long_description"] = trans.data["long_description"]
                    acc["short_description"] = trans.data["short_description"]
                if trans.op_name == "account_creation":
                    acc["msg_pub_key"] = trans.data["msg_public_key"]
                if trans.op_name == "set_friend":
                    if trans.data['type'] == "add":
                        acc["friends"] = list(acc["friends"]) + [trans.data["target"]]
                    if trans.data['type'] == "remove":
                        acc["friends"] = list(acc["friends"]) - [trans.data["target"]]
            
            if trans.op_name == "transfer":
                if str(trans.sender) == pub_key:
                    acc["balance"] = acc["balance"] - trans.data["amount"]
                elif trans.data["receiver"] == str(pub_key):
                    acc["balance"] = acc["balance"] + trans.data["amount"]
                    transes.append(trans.to_json())
    
    acc["transactions"] = transes
    return jsonify({"status" : "ok", "account" : acc}), 200

@app.route('/set/nonce', methods=['GET'])
def set_nonce():
    ''' Informative solution'''
    nonce = request.args.get("nonce")
    if nonce is None:
        return jsonify({"status" : "error", "info" : "no nonce is given"}), 400

    if statics.PENDING_BLOCK is None:
        return jsonify({"status" : "error", "info" : "nothing is pending"}), 400

    try:
        d = int(nonce)
    except:
        return jsonify({"status" : "error", "info" : "cannot convert to int"}), 400

    pending_b = statics.PENDING_BLOCK
    # Test all solutions
    pending_b.nonce = int(nonce)
    pending_b.calc_hash()
    if pending_b.check_valid(only_hash_start_seq=True):
        # Succes, have a right hash
        statics.SOLUTIONS.append(int(nonce))   
        return jsonify({"status" : "ok", "info" : "thank you"}), 200
    
    return jsonify({"status" : "error", "info" : "nonce uncorrect"}), 400

@app.route('/post/transaction', methods=['POST'])
def post_transaction():
    if not "sender" in request.json or not "op" in request.json:
        return jsonify({"status" : "error", "info" : "no sender/operation is given"}), 400
    if not "data" in request.json or not "signature" in request.json:
        return jsonify({"status" : "error", "info" : "no data/signature is given"}), 400
    if not "id" in request.json or not "timestamp" in request.json:
        return jsonify({"status" : "error", "info" : "no id/timestamp is given"}), 400

    sender = request.json["sender"]
    data = request.json["data"]
    timestamp = request.json["timestamp"]
    id = request.json["id"]
    op_name = request.json["op"]
    signature = request.json["signature"]
    trans = Transaction(sender, id, op_name, data, signature, timestamp=timestamp)
    
    if trans.prove_signature() is False:
        return jsonify({"status" : "error", "info" : "Signature is wrong"}), 400
   
    if check_if_valid(trans) is False:
        return jsonify({"status" : "error", "info" : "Transaction is invalid"}), 400

    statics.OPEN_TRANSACTIONS.append(trans)
    return jsonify({"status" : "ok"}), 200

def run():
    app.run(host=NODE_ADDRESS, port=NODE_PORT)

def start_server():
    run_thread = Thread(target=run)
    run_thread.daemon = True
    run_thread.name = "Node - Server Thread"
    run_thread.start()
    statics.RUNNING_PROCESSES.append(run_thread)