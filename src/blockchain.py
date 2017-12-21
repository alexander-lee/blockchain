import hashlib
import json
import requests
from time import time
from urllib.parse import urlparse


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

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

        @return: <int> proof of work for the new block
        """

        proof = 0
        while self.is_valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    def register_node(self, address, identifer=None):
        """
        Add a new node to the list of nodes

        @param address: <str> Address of the node (eg: 'http://127.0.0.1:5000')
        @param identifer: <str> UUID of the node
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def resolve_conflicts(self):
        """
        The Consensus Algorithm, replaces our chain with the longest valid chain in the network

        @return: <bool> True if our chain was replaced, False otherwise
        """

        neighbours = self.nodes
        new_chain = None

        max_chain_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                node_data = response.json()
                chain = node_data['chain']
                length = node_data['length']
                print(self.valid_chain(chain))

                if length > max_chain_length and self.valid_chain(chain):
                    new_chain = chain
                    max_chain_length = length

        # Replace our chain if we found a longer one
        if new_chain is not None:
            self.chain = new_chain
            return True

        return False

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
