# System
from threading import Thread
from datetime import datetime
import sys

# Own
from api.custom_objects import *
from api.background import *
sys.path.append(".")
from config import *
from blockchain import *
import helper


# Flask
from flask import Flask, jsonify, request
from flask_cors import CORS

# Disable logging
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
log.disabled = True

# Make flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
CORS(app)

@app.route('/')
def index():
    ''' Index site --> Show if everything is good '''
    return VERSION_INFO

@app.route('/create-user')
def create_user():
    '''Creates a new account. Returns the status, identifier and public_key'''
    acc = Account.create_account()
    statics.ACCOUNTS.append(acc)

    return jsonify({"status" : "ok", "identifier" : acc.identifier, "public_key" : str(acc.sender)}), 200

@app.route('/send-money', methods=["POST"])
def send_money():
    '''Transfers money to someone else. Return true or false'''
    if not "identifier" in request.json or not "receiver" in request.json:
        return jsonify({"status" : "error", "info" : "no identifier/receiver is given"}), 400
    if not "amount" in request.json or not "message" in request.json:
        return jsonify({"status" : "error", "info" : "no amount/message is given"}), 400


    sender_acc = None
    for acc_search in statics.ACCOUNTS:
        if acc_search.identifier == request.json["identifier"]:
            sender_acc = acc_search
            break 
    
    if sender_acc is None:
        # no sender found
        return jsonify({"status" : "error", "info" : "identifier not found"}), 400

    receiver_acc = None
    for acc_search in statics.ACCOUNTS:
        if str(acc_search.sender) == str(request.json["receiver"]):
            receiver_acc = acc_search
            break
    
    if receiver_acc is None:
        # no receiver found
        return jsonify({"status" : "error", "info" : "no receiver found"}), 400

    if sender_acc.send_money(receiver_acc.sender, receiver_acc.msg_keys[0], request.json["amount"], request.json["message"]):
        return jsonify({"status" : "ok"}), 200
    
    return jsonify({"status" : "failed"})

@app.route('/add-friend', methods=["GET"])
def add_friend():
    '''Node Request to add a new friend'''
    identifier = request.args.get("identifier")
    target = request.args.get("target") 
    if identifier is None or target is None:
        # Check identifier value
        return jsonify({"status" : "failed", "msg" : "no identifier/target is given"}), 400 

    # Get acc
    for acc_search in statics.ACCOUNTS:
        if acc_search.identifier == identifier:
            if acc_search.add_friend(target):
                return jsonify({"status" : "ok"}), 200  
            else:
                 return jsonify({"status" : "error", "info" : "node said no"}), 400  
    
    # no acc found
    return jsonify({"status" : "error", "info" : "identifier not found"}), 400  

@app.route('/remove-friend', methods=["GET"])
def remove_friend():
    '''Node Request to remove a new friend'''
    identifier = request.args.get("identifier")
    target = request.args.get("target") 
    if identifier is None or target is None:
        # Check identifier value
        return jsonify({"status" : "failed", "msg" : "no identifier/target is given"}), 400 

    # Get acc
    for acc_search in statics.ACCOUNTS:
        if acc_search.identifier == identifier:
            if acc_search.remove_friend(target):
                return jsonify({"status" : "ok"}), 200  
            else:
                 return jsonify({"status" : "error", "info" : "node said no"}), 400  
    
    # no acc found
    return jsonify({"status" : "error", "info" : "identifier not found"}), 400  
    

@app.route('/account-settings', methods=["POST"])
def account_settings():
    '''Changing account settings Returns: OK or False'''
    if not "name" in request.json or not "profile_image" in request.json:
        return jsonify({"status" : "error", "info" : "no name/profile_image is given"}), 400
    if not "short_description" in request.json or not "long_description" in request.json:
        return jsonify({"status" : "error", "info" : "no short_description/long_description is given"}), 400
    if not "links" in request.json or not "location" in request.json:
        return jsonify({"status" : "error", "info" : "no links/location is given"}), 400

    # Get acc
    sender_acc = None
    for acc_search in statics.ACCOUNTS:
        if acc_search.identifier == request.json["identifier"]:
            sender_acc = acc_search
            break
    
    if sender_acc is None:
        # no sender found
        return jsonify({"status" : "error", "info" : "identifier not found"}), 400  

    if sender_acc.account_settings(request.json["name"], request.json["profile_image"], request.json["short_description"], request.json["long_description"], request.json["links"], request.json["location"]) is True:
        return jsonify({"status" : "ok"}), 200
    
    return jsonify({"status" : "failed"}), 400

@app.route('/check-notifications', methods=["GET"])
def check_notifications():
    '''Get latest Notifications'''
    identifier = request.args.get("identifier")
    if identifier is None:
        # Check identifier value
        return jsonify({"status" : "failed", "msg" : "no identifier is given"}), 400 

    for acc in statics.ACCOUNTS:
        # Find acc
        if identifier == acc.identifier:
            return jsonify({"status" : "ok", "notifications" : acc.notifications}), 200
    
    return jsonify({"status" : "failed", "msg" : "no account was found"}), 400 

@app.route('/get-allow-interactions', methods=["GET"])
def get_allow_interactions():
    return jsonify({"status" : "ok", "allow" : statics.ALLOW_INTERACTIONS}), 200 

@app.route('/set-allow-interactions', methods=["GET"])
def set_allow_interactions():
    d = request.args.get("allow")
    if d is None:
        return jsonify({"status" : "failed", "msg" : "no allow is given"}), 400 
    
    if "1" in d or "true" in d.lower():
        statics.ALLOW_INTERACTIONS = True
    elif "0" in d or "false" in d.lower():
        statics.ALLOW_INTERACTIONS = False
    else:
        return jsonify({"status" : "failed", "msg" : "accept 1/true or 0/false only"}), 400

    return jsonify({"status" : "ok"}), 200

@app.route('/get-statistics')
def get_statistics():
    '''Return statistics'''
    return jsonify(statics.STATISTICS_DICT), 200

def run():
    app.run(host=API_ADDRESS, port=API_PORT)

def start_api():
    # Flask Server
    run_thread = Thread(target=run)
    run_thread.daemon = True
    run_thread.name = "API - Server Thread"
    run_thread.start()
    statics.RUNNING_PROCESSES.append(run_thread)

    # Blockchain statistics
    blockchain_statistics_thread = Thread(target=blockchain_statistics)
    blockchain_statistics_thread.daemon = True
    blockchain_statistics_thread.name = "API - Statistic Thread"
    blockchain_statistics_thread.start()
    statics.RUNNING_PROCESSES.append(run_thread)

    # Blockchain notifier
    blockchain_statistics_thread = Thread(target=blockchain_notifier)
    blockchain_statistics_thread.daemon = True
    blockchain_statistics_thread.name = "API - Notifie"
    blockchain_statistics_thread.start()
    statics.RUNNING_PROCESSES.append(run_thread)

if __name__ == "__main__":
    start_api()

    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
