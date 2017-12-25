import json
import math
from time import time
from hashlib import sha256


class Blockchain(object):
    def __init__(self, chain=[], tx_info=None):
        self.chain = chain
        self.transaction_pool = []
        self.tx_info = tx_info or {'0': None}  # 0 is a reserved tx hash for rewards

        # Create the genesis block
        if len(chain) == 0:
            self.verify_and_add_transaction('0', '0', 0, '0')
            self.add_block(previous_hash=1, proof=100)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, proof, previous_hash=None):
        """
        Create new block in the Blockchain

        @param proof: <int> The proof of work
        @param previous_hash: <str> Hash of the previous block

        @return: <dict>
            Block of format: {
                header: {
                    index: <int>
                    timestamp: <time>
                    proof: <int>
                    previous_hash: <str>
                    merkleroot: <str>
                }
                transactions: [<transaction hashes>]
                merkletree: [[<transaction hashes>]]
            }
        """

        merkle_tree = self.find_merkle(self.transaction_pool, self.tx_info)

        block = {
            'header': {
                'index': len(self.chain) + 1,
                'timestamp': time(),
                'proof': proof,
                'previous_hash': previous_hash or self.hash(self.chain[-1]['header']),
                'merkleroot': merkle_tree[0][0]
            },
            'transactions': self.transaction_pool,
            'merkle_tree': merkle_tree
        }

        self.transaction_pool = []
        self.chain.append(block)

        return block

    def verify_and_add_transaction(self, sender, recipient, amount, previous_hash):
        """
        Add a new transaction to the transaction pool.

        - First verify that the previous hash leads to a valid transaction
          where the recipient of that transaction is the sender of this one

        @param sender: <str> Address of sender
        @param recipient: <str> Address of recipient
        @param amount: <int> Amount
        @param previous_hash: <str> hash of the previous transaction used

        @return: <dict> transaction if it was successful, or None
        """

        tx = {
            'previous_hash': previous_hash,
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time()
        }

        if not self.valid_transaction(tx):
            print('Invalid Transaction!')
            return None

        # TxID = Double Hash of the Transaction
        tx_hash = self.hash(self.hash(tx))

        self.transaction_pool.append(tx_hash)
        self.tx_info[tx_hash] = tx

        return tx

    def valid_transaction(self, transaction):
        """
        Determines whether a transaction is valid or not

        It needs to verify three things:
        - Digital Signature
        - Valid Transaction Format
        - Unspent Transaction Output of Sender >= Amount in this transaction

        Note: We aren't tracking UTXOs so we're gonna do a simple verification
              of checking the previous transaction

        @param transaction: <dict>

        @return <bool> True/False depending on whether the transaction is valid
        """

        # Validate keys
        keys = ['sender', 'recipient', 'amount', 'previous_hash']

        for key in keys:
            if key not in transaction:
                return False

        # Validate the transaction's previous_hash
        previous_hash = transaction['previous_hash']

        # Ignore reserved '0'
        if previous_hash == '0':
            return True

        if previous_hash in self.tx_info:
            prev_tx = self.tx_info[previous_hash]

            if prev_tx['recipient'] != transaction['sender']:
                print('Previous transaction\'s recipient is not the current sender')
                return False

            if prev_tx['amount'] < transaction['amount']:
                print('Previous transaction\'s amount is not enough')
                return False
        else:
            print('Cannot find transaction with that hash')
            return False

        return True

    def save(self, filename='blockchain.json'):
        with open(filename, 'w') as outfile:
            json.dump({
                'chain': self.chain,
                'tx_info': self.tx_info,
            }, outfile, indent=4)

    @staticmethod
    def hash(_dict):
        """
        Create a SHA-256 hash of a dict

        @param _dict: <dict> Transaction, Block Header

        @return: <str>
        """

        # Order the dictionary to ensure consistent block hashes
        dict_str = json.dumps(_dict, sort_keys=True).encode()
        return sha256(dict_str).hexdigest()

    @staticmethod
    def find_merkle(tx_list, tx_info):
        """
        Creates a Merkle Tree using a SHA-256 hash with the transactions list

        @param tx_list: [<transaction hashes>] list of transactions
        @param tx_info: <dict> a mapping of transaction hashes to transaction information

        @return: [[<transaction hashes>]]
        - The structure of the tree is stored as a list of lists
        - Where find_merkle[0] = merkle root, find_merkle[1] = layer 2 of the tree, etc...
        """

        # Edge Case tx_list has only 1 item
        if len(tx_list) == 1:
            return [tx_list]

        # Sort Transactions by Timestamp
        tx_info_list = list(map(lambda tx_id: {**tx_info[tx_id], 'hash': tx_id}, tx_list))
        tx_info_list = sorted(tx_info_list, key=lambda tx: tx['timestamp'])
        tx_list = list(map(lambda tx: tx['hash'], tx_info_list))

        tree_height = math.ceil(math.log(len(tx_list), 2)) + 1
        tree = [None] * tree_height

        tree[-1] = tx_list.copy()

        # Go from leaf level (tree_height - 1) to root (0)
        for i in range(tree_height - 1, -1, -1):
            current_level = tree[i]
            next_level = []

            # Repeat the transaction for unfilled levels (needs to 2^x)
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            for t in range(0, len(current_level), 2):
                str_to_hash = f'{current_level[t]}{current_level[t+1]}'
                next_level.append(sha256(sha256(str_to_hash.encode())))

            tree[i] = next_level
        return tree

    @staticmethod
    def valid_proof(prev_hash, proof):
        """
        Determines if it is a valid proof of work

        @param prev_hash: <str>
        @param proof: <int>

        @return: <bool> T/F depending on whether the hash fits the criteria
        """

        guess = f'{prev_hash}{proof}'.encode()
        guess_hash = sha256(guess).hexdigest()

        # TODO: Change the criteria
        return guess_hash[:4] == "0" * 4

    @staticmethod
    def valid_chain(chain):
        """
        Determines whether a blockchain is valid or not

        It needs to verify three things:
        - Blocks are ordered by index and timestamp
        - Each previous_hash matches the hash of the block
        - Proof of Work is correct for each block in the sequence

        @param chain: [<block dict>] A blockchain

        @return <bool> True/False depending on whether the blockchain is valid
        """

        for i in range(0, len(chain)-1):
            block = chain[i]
            next_block = chain[i+1]

            if block['header']['index'] != i+1 or next_block['header']['index'] != i+2:
                print('Indices aren\'t correct')
                print(f'Block: {block}')
                print(f'Next: {next_block}')
                return False

            if block['header']['timestamp'] > next_block['header']['timestamp']:
                print('Timestamps aren\'t ordered!')
                print(f'Block: {block}')
                print(f'Next: {next_block}')
                return False

            if Blockchain.hash(block['header']) != next_block['header']['previous_hash']:
                print('Hashes aren\'t correct!')
                print(f'Block: {block}')
                print(f'Next: {next_block}')
                return False

            if not Blockchain.valid_proof(Blockchain.hash(block['header']), next_block['header']['proof']):
                print('Proof of Work is not valid!')
                print(f'Block: {block}')
                print(f'Next: {next_block}')
                return False

        return True

    @staticmethod
    def valid_headers(headers):
        """
        Determines whether a blockchain is valid or not

        It needs to verify three things:
        - Blocks are ordered by index and timestamp
        - Each previous_hash matches the hash of the block
        - Proof of Work is correct for each block in the sequence

        @param headers: [<block dict>] Block headers

        @return <bool> True/False depending on whether the blockchain is valid
        """

        for i in range(0, len(headers)-1):
            block = headers[i]
            next_block = headers[i+1]

            if block['index'] != i+1 or next_block['index'] != i+2:
                print('Indices aren\'t correct')
                print(f'Block: {block}')
                print(f'Next: {next_block}')
                return False

            if block['timestamp'] > next_block['timestamp']:
                print('Timestamps aren\'t ordered!')
                print(f'Block: {block}')
                print(f'Next: {next_block}')
                return False

            if Blockchain.hash(block) != next_block['previous_hash']:
                print('Hashes aren\'t correct!')
                print(f'Block: {block}')
                print(f'Next: {next_block}')
                return False

            if not Blockchain.valid_proof(Blockchain.hash(block), next_block['proof']):
                print('Proof of Work is not valid!')
                print(f'Block: {block}')
                print(f'Next: {next_block}')
                return False

        return True
