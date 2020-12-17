from config import *
from smart_open import open

import json
import hashlib
import libnum
from base64 import b64encode, b64decode

import Cryptodome
from Cryptodome.Random import get_random_bytes
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES, PKCS1_OAEP
from Cryptodome.Util.number import *
from Cryptodome import Random


from blockchain import *

def hash_str(s : str) -> str:
     return hashlib.sha256(s.encode()).hexdigest()

def get_data_from_site(url : str) -> str:
    try:
        data = ""
        with open(url) as document:
            for doc in document:
                data += doc
        
        return data
    except:
        return None

def get_json_from_site(url : str) -> dict:
    data = get_data_from_site(url)
    if data is None:
        return None
    return json.loads(data)

class Message_Encryption():
    def generate_rsa_keys() -> tuple:
        ''' return: (public_key, private_key)'''
        rsa_key = RSA.generate(1024)
        private_key = rsa_key.export_key()
        public_key = rsa_key.publickey().export_key()
        return (public_key, private_key)

    def encrypt_str(receiver_pub_key, data : str) -> dict:
        '''return: msg_dict (with: enc_aes_key, nonce, tag, ciphertext)'''
        aes_key = get_random_bytes(16)

        # Encrypt AES password with RSA
        cipher_rsa = PKCS1_OAEP.new(RSA.import_key(receiver_pub_key))
        enc_aes_key = cipher_rsa.encrypt(aes_key)

        # Encrypt data with AES
        cipher_aes = AES.new(aes_key, AES.MODE_EAX)
        ciphertext, tag = cipher_aes.encrypt_and_digest(data.encode())
        nonce = cipher_aes.nonce

        # Return msg_dict
        return {"enc_aes_key" : b64encode(enc_aes_key).decode('utf-8'), "nonce" : b64encode(nonce).decode('utf-8'),
                 "tag" : b64encode(tag).decode('utf-8'), "ciphertext" : b64encode(ciphertext).decode('utf-8')}

    def decrypt_str(private_key, msg_dict : dict) -> str:
        # Decrypt the session key with the private RSA key
        cipher_rsa = PKCS1_OAEP.new(RSA.import_key(private_key))
        session_key = cipher_rsa.decrypt(b64decode(msg_dict["enc_aes_key"]))

        # Decrypt the data with the AES session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX, b64decode(msg_dict["nonce"]))
        data = cipher_aes.decrypt_and_verify(b64decode(msg_dict["ciphertext"]), b64decode(msg_dict["tag"]))
        return data


class Signature():
    # Max Characters: 15 (wegen unsigned short)
    # Public Key: n = p*q
    # Private Key: PHI = (p-1)*(q-1)
    # Thanks: https://medium.com/asecuritysite-when-bob-met-alice/rsa-digital-signatures-in-12-lines-of-python-ea0677aad6c9

    def generate_key_pair() -> tuple:
        ''' Generates a key pair'''
        p = Cryptodome.Util.number.getPrime(RSA_BITS, randfunc=Cryptodome.Random.get_random_bytes)
        q = Cryptodome.Util.number.getPrime(RSA_BITS, randfunc=Cryptodome.Random.get_random_bytes)

        return (p, q)

    def signe_string(to_sign : str, keys : tuple) -> int:
        ''' Signe a string '''
        # keys == p, q
        # Prepare text
        D = bytes_to_long(to_sign.encode('utf-8'))    

        # make Variables
        p, q = keys
        PHI = (p-1)*(q-1) 
        n = p*q
        s = (libnum.invmod(RSA_V, PHI))

        # Sign
        signature = pow(D,s, n)
        return signature

    def sign_transaction(trans, keys):
        testing = {
            "data" : trans.data,
            "op_name" : trans.op_name,
            "sender" : trans.sender
        }
        sign_str = hash_str(json.dumps(testing))[0:14]
        signature = Signature.signe_string(sign_str, keys)
        trans.signature = signature
        return trans

    def verify(signature : int, pub_key : int) -> str:
        ''' Verify a signature '''
        # pub_key == n
        res = pow(signature, RSA_V , pub_key)
        
        buffer = long_to_bytes(res)
        try:
            return buffer.decode()
        except UnicodeDecodeError:
            # signature is not right
            # error has no lenght of 14 so
            # it is save to cause an invalid statement
            return "error"


