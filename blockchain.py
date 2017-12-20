import hashlib
import json
from time import time


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
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
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.current_transactions = []
        self.chain.append(block)

        return block

    def add_transaction(self, sender, recipient, amount):
        """
        Add a new transaction to the list of transactions

        @param sender: <str> Address of sender
        @param recipient: <str> Address of recipient
        @param amount: <int> Amount

        @return: <int> The index of the block that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof):
        """
        Proof of Work Algorithm:
            - Find a number p' such that hash(pp') has 4 leading zeros
            - p was the previous block's proof of work, p' is the goal

        @param last_proof: <int> Last Block's proof of work

        @return <int> proof of work for the new block
        """

        proof = 0
        while self.is_valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def hash(block):
        """
        Create a SHA-256 hash of a block dict

        @param block: <dict> Block

        @return: <str>
        """

        # Order the dictionary to ensure consistent block hashes
        block_str = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_str).hexdigest()

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
