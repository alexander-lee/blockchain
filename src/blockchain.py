import hashlib
import json
from time import time


class Blockchain(object):
    def __init__(self, chain=[]):
        self.chain = chain
        self.transaction_pool = set()
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
            'transactions': list(self.transaction_pool),
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.transaction_pool = set()
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

        @return: <str> transaction hash if it was successful, or None
        """

        # Small validation of the transaction
        if previous_hash in self.transaction_pool:
            prev_tx = self.transactions_info[previous_hash]
            if prev_tx['recipient'] != sender:
                return None

        tx = {
            'previous_hash': previous_hash,
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }

        tx_hash = self.hash(tx)

        self.transaction_pool.add(tx_hash)
        self.transactions_info[tx_hash] = tx

        return tx_hash

    def proof_of_work(self, last_proof):
        """
        Proof of Work Algorithm:
            - Find a number p' such that hash(pp') has 4 leading zeros
            - p was the previous block's proof of work, p' is the goal

        @param last_proof: <int> Last Block's proof of work

        @return: <int> proof of work for the new block
        """

        proof = 0
        while self.is_valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

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
    def is_valid_proof(last_proof, proof):
        """
        Determines if it is a valid proof of work

        @param last_proof: <int>
        @param proof: <int>

        @return: <bool> T/F depending on whether the hash fits the criteria
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        # TODO: Change the criteria
        return guess_hash[:4] == "0000"

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
                print('index are off')
                return False

            if block['timestamp'] > next_block['timestamp']:
                print('timestamps suck')
                return False

            if Blockchain.hash(block) != next_block['previous_hash']:
                print('hash failed')
                return False

            if not Blockchain.is_valid_proof(block['proof'], next_block['proof']):
                print('unalid proof')
                return False

        return True

    @staticmethod
    def valid_transaction(transaction):
        """
        Determines whether a transaction is valid or not

        It needs to verify two things:
        - Digital Signature
        - Unspent Transaction Output of Sender >= Amount in this transaction

        @param transaction: <dict>

        @return <bool> True/False depending on whether the transaction is valid
        """
        pass
