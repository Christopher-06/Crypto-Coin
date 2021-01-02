TEST_MODE = True
VERSION_INFO = 'CryptoCoin-Core v0.5'

HASH_START_SEQ = "c000"
RSA_BITS = 60
RSA_V = 65537

# Miner
MAX_MINING_THREADS = 3

# API
API_PORT = 4999
API_ADDRESS = "192.168.178.20"

# Node
NODE_ADDRESS = "192.168.178.13"
NODE_PORT = 8000

MIN_BLOCK_TIME_DELTA = 5 #sec
MIN_BLOCK_TRANSACTIONS = 1
MIN_BLOCKS_BEFORE_REMOVE = 2

class statics:
    RUNNING_PROCESSES = []
    CLOSING = False
    LITE_ACTIVE = True


    # Blockchain
    NODES = []


    # Node
    SYNC_BLOCKCHAIN = False
    CHAIN = []
        # Pending to be finished with mining
    PENDING_BLOCK = None
        # Block, which is filled while the other
        # is pending or it is to early
    CURRENT_BLOCK = None
        # Holds all (formal valid) transactions
        # and add them one by one
    OPEN_TRANSACTIONS = []
        # List to hold all available nonces for
        # the pending block and ONLY ONE process
        # is checking it to prevent double append
    SOLUTIONS = []


    # API
    ACCOUNTS = []
    ALLOW_INTERACTIONS = True
    STATISTICS_DICT = {"chain_len" : 0, "transactions_per_block" : [], "acc_count" : 0, "last_actions" : [], "accounts" : []}


# Account settings
class AccountSettings:
    MAX_NAME_LEN = 50
    MAX_LOCATION_STR_LEN = 50
    MAX_PROFILE_IMAGE_URL_LEN = 2000 # HTTP limit
    MAX_SHORT_DESCRIPTION_LEN = 100
    MAX_LONG_DESCRIPTION_LEN = 500

    MAX_LINK_NAME_LEN = 20
    MAX_LINK_COUNT = 5

TRANSACTION_ID_LEN = 64