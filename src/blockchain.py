import hashlib
import json
from time import time


class Blockchain(object):
    def __init__(self, chain=[]):
        self.chain = chain
        self.transaction_pool = []
        self.transactions_info = {'0': None}  # 0 is a reserved tx hash

        # Create the genesis block
        if len(chain) == 0:
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
                index: <int>
                timestamp: <time>
                transactions: [<transaction dict>]
                proof: <int>
                previous_hash: <str>
            }
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.transaction_pool,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.transaction_pool = []
        self.chain.append(block)

        return block

    def add_transaction(self, sender, recipient, amount, previous_hash):
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
            'amount': amount
        }

        if not self.valid_transaction(tx):
            print('Invalid Transaction!')
            return None

        tx_hash = self.hash(self.hash(tx))

        self.transaction_pool.append(tx_hash)
        self.transactions_info[tx_hash] = tx

        return tx_hash

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

        if previous_hash in self.transaction_pool:
            prev_tx = self.transactions_info[previous_hash]

            if prev_tx['recipient'] != transaction['sender']:
                return False

            if prev_tx['amount'] < transaction['amount']:
                return False
        else:
            return False

        return True

    @staticmethod
    def hash(_dict):
        """
        Create a SHA-256 hash of a dict

        @param block: <dict> Block

        @return: <str>
        """

        # Order the dictionary to ensure consistent block hashes
        dict_str = json.dumps(_dict, sort_keys=True).encode()
        return hashlib.sha256(dict_str).hexdigest()

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Determines if it is a valid proof of work

        @param last_proof: <int>
        @param proof: <int>

        @return: <bool> T/F depending on whether the hash fits the criteria
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

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
            print(f'Block: {block}')
            print(f'Next: {next_block}')

            if block['index'] != i+1 or next_block['index'] != i+2:
                print('Indices aren\'t correct')
                return False

            if block['timestamp'] > next_block['timestamp']:
                print('Timestamps aren\'t ordered!')
                return False

            if Blockchain.hash(block) != next_block['previous_hash']:
                print('Hashes aren\'t correct!')
                return False

            if not Blockchain.is_valid_proof(block['proof'], next_block['proof']):
                print('Proof of Work is not valid!')
                return False

        return True
