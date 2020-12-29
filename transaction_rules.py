from blockchain import Transaction
from config import *

# True, when it succeed the test

def test_inside_open_transactions(trans : Transaction):
    ''' Test if another transaction by the sender is already in open state '''
    for open_trans in statics.OPEN_TRANSACTIONS:
        if open_trans.sender == trans.sender:
            return True
    return False

def test_inside_current_block(trans : Transaction):
    ''' Test if another transaction by the sender is in the current block '''
    for open_trans in statics.CURRENT_BLOCK.transactions:
        if open_trans.sender == trans.sender:
            return True
    return False

def test_generel_formal(trans : Transaction):
    return True

#   *** Specific tests
class test_account_creation():
    def __init__(self, trans : Transaction) -> None:
        self.trans = trans

    def result(self):
        if self.test_formal() is False:
            return False
        if self.test_existent() is False:
            return False
        return True

    def test_formal(self):
        if len(self.trans.data) != 1:
            return False

        if not "msg_public_key" in self.trans.data:
            return False

        if isinstance(self.trans.data["msg_public_key"], str) is False:
            return False

        return True

    def test_existent(self):
        # check wheter the sender is already listed
        for block in reversed(statics.CHAIN + [statics.PENDING_BLOCK]):
            if block is None:
                # when pending_block is none
                continue

            for trans in block.transactions:
                if trans.sender == self.trans.sender:
                    return False
        return True

class test_account_setting():
    def __init__(self, trans : Transaction) -> None:
        self.trans = trans

    def result(self):
        if self.test_formal() is False:
            return False
        return True

    def test_formal(self):
        # name, profile_image, short_description, long_description, links, location
        if len(self.trans.data) != 6:
            return False

        if not "name" in self.trans.data or not "profile_image" in self.trans.data or not "links" in self.trans.data:
            return False

        if not "short_description" in self.trans.data or not "long_description" or not "location" in self.trans.data:
            return False

        # Name
        if isinstance(self.trans.data["name"], str) is False:
            return False

        if len(self.trans.data["name"]) > AccountSettings.MAX_NAME_LEN:
            return False

        # Location
        if isinstance(self.trans.data["location"], str) is False:
            return False

        if len(self.trans.data["location"]) > AccountSettings.MAX_LOCATION_STR_LEN:
            return False

        # Profile Image URL
        if isinstance(self.trans.data["profile_image"], str) is False:
            return False

        if len(self.trans.data["profile_image"]) > AccountSettings.MAX_PROFILE_IMAGE_URL_LEN:
            return False

        # Short description
        if isinstance(self.trans.data["short_description"], str) is False:
            return False

        if len(self.trans.data["short_description"]) > AccountSettings.MAX_SHORT_DESCRIPTION_LEN:
            return False

        # Long description
        if isinstance(self.trans.data["long_description"], str) is False:
            return False

        if len(self.trans.data["long_description"]) > AccountSettings.MAX_LONG_DESCRIPTION_LEN:
            return False

        # Links
        if isinstance(self.trans.data["links"], list) is False:
            return False

        if len(self.trans.data["links"]) > AccountSettings.MAX_LINK_COUNT:
            return False

        for link in self.trans.data["links"]:
            if len(link) != 2:
                return False

            if not "url" in link or not "name" in link:
                return False

            if isinstance(link["url"], str) is False or len(link["url"]) >= 2000:
                return False
            
            if isinstance(link["name"], str) is False or len(link["name"]) > AccountSettings.MAX_LINK_NAME_LEN:
                return False


        return True 

class test_transfer():
    def __init__(self, trans : Transaction) -> None:
        self.trans = trans

    def result(self):
        if self.test_formal() is False:
            return False
        if self.test_receiver() is False:
            return False
        if self.test_amount() is False:
            return False
        return True

    def test_formal(self):
        if len(self.trans.data) != 3:
            return False

        if not "receiver" in self.trans.data or not "amount" in self.trans.data or not "message" in self.trans.data:
            return False
        
        if isinstance(self.trans.data["receiver"], str) is False:
            return False

        if isinstance(self.trans.data["amount"], int) is False:
            return False
        if self.trans.data["amount"] < 1:
            return False

        if isinstance(self.trans.data["message"], dict) is False:
            return False
        if len(self.trans.data["message"]) != 2:
            return False

        for x in ["sender", "receiver"]:
            if not "enc_aes_key" in self.trans.data["message"][x] or not "nonce" in self.trans.data["message"][x] or not "tag" in self.trans.data["message"][x] or not "ciphertext" in self.trans.data["message"][x]:
                return False
            
            if isinstance(self.trans.data["message"][x]["enc_aes_key"], str) is False or len(self.trans.data["message"][x]["enc_aes_key"]) > 5000:
                return False
            if isinstance(self.trans.data["message"][x]["nonce"], str) is False or len(self.trans.data["message"][x]["nonce"]) > 500:
                return False
            if isinstance(self.trans.data["message"][x]["tag"], str) is False or len(self.trans.data["message"][x]["tag"]) > 500:
                return False
            if isinstance(self.trans.data["message"][x]["ciphertext"], str) is False or len(self.trans.data["message"][x]["ciphertext"]) > 250:
                return False

        return True

    def test_receiver(self):
        # test if receiver exists
        for block in (statics.CHAIN + [statics.PENDING_BLOCK]):
            if block is None:
                # Maybe pending block
                continue

            for trans in block.transactions:
                if str(trans.sender) == self.trans.data["receiver"]:
                    return True

        return False

    def test_amount(self):
        if self.trans.data["amount"] <= 0:
            # Test negative or zero values
            return False

        # Check acc balance
        balance = 1000 if TEST_MODE else 0
        for block in (statics.CHAIN + [statics.PENDING_BLOCK]):
            if block is None:
                # Maybe pending block
                continue

            for trans_listed in block.transactions:  
                if trans_listed.op_name == "transfer":
                    if str(self.trans.sender) == str(trans_listed.sender):
                        balance = balance - trans_listed.data["amount"]
                    elif str(trans_listed.data["receiver"]) == str(self.trans.sender):
                        balance = balance + trans_listed.data["amount"]
        
        if self.trans.data["amount"] > balance:
            # Test if amount is available
            return False
        
        return True
               

class test_set_friend():
    def __init__(self, trans : Transaction) -> None:
        self.trans = trans

    def result(self):
        if self.test_formal() is False:
            return False
        if self.test_target() is False:
            return False
        if self.test_friends() is False:
            return False
        
        return True

    def test_formal(self):
        if len(self.trans.data) != 2:
            return False

        if not "target" in self.trans.data or not "type" in self.trans.data:
            return False

        if self.trans.data["type"] != "add" and self.trans.data["type"] != "remove":
            return False

        if isinstance(self.trans.data["target"], str) is False:
            return False

        return True

    def test_target(self):
        # test if receiver exists
        for block in (statics.CHAIN + [statics.PENDING_BLOCK]):
            if block is None:
                # Maybe pending block
                continue

            for trans in block.transactions:
                if str(trans.sender) == self.trans.data["target"]:
                    return True

        return False

    def test_friends(self):
        '''Check if the friend is already registered'''
        friends = []
        for block in (statics.CHAIN + [statics.PENDING_BLOCK]):
            # Get all friends
            if block is None:
                # Maybe pending block
                continue

            for trans in block.transactions:
                if trans.op_name == "set_friend" and str(trans.sender) == str(self.trans.sender):
                    if trans.data["type"] == "add":
                        friends.append(trans.data["target"])
                    elif trans.data["type"] == "remove":
                        friends.remove(trans.data["target"])

        
        if self.trans.data["type"] == "add":
            # Check if inside
            for friend in friends:
                if friend == self.trans.data["target"]:
                    # Already in
                    return False
            return True
        
        if self.trans.data["type"] == "remove":
            for friend in friends:
                if friend == self.trans.data["target"]:
                    # Inside -> can be removed
                    return True
            return False

        

def check_if_valid(trans : Transaction) -> bool:
    if trans.prove_signature() is False:
        # Singature wrong
        return False

    if test_inside_open_transactions(trans) or test_inside_current_block(trans):
        # Trans sender got a Trans already in open state
        return False

    if test_generel_formal(trans) is False:
        return False

    if trans.op_name == "account_creation":
        if test_account_creation(trans).result() is False:
            return False
    elif trans.op_name == "account_setting":
        if test_account_setting(trans).result() is False:
            return False
    elif trans.op_name == "transfer":
        if test_transfer(trans).result() is False:
            return False
    elif trans.op_name == "set_friend":
        if test_set_friend(trans).result() is False:
            return False
    else:
        return False

    return True

    