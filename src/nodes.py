import threading
import json
import netifaces as ni
from time import time, sleep
from random import randint
from urllib.parse import urlparse

try:
    from queue import Empty
except ImportError:
    from Queue import Empty

from mesh.links import UDPLink
from mesh.filters import DuplicateFilter
from mesh.node import Node as NetworkComponent

from .blockchain import Blockchain


class Node(threading.Thread):
    def __init__(self, name, port=5000, blockchain=Blockchain()):
        threading.Thread.__init__(self)

        self.name = name
        self.address = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

        self.blockchain = blockchain

        self.peer_info = {}
        self.peers = set()

        self.links = [UDPLink('en0', port=port)]
        self.network = NetworkComponent(self.links, name, Filters=(DuplicateFilter,))

        self.keep_listening = True
        self.ready = False
        self.synced = False

        # Start Network Component
        [link.start() for link in self.links]
        self.network.start()
        self.start()

    @property
    def identifier(self):
        parsed_url = urlparse(self.address)
        return f'{parsed_url.path}:{self.name}'

    # Threading
    def run(self):
        while self.keep_listening:
            for interface in self.network.interfaces:
                try:
                    self.recv(self.network.inq[interface].get(timeout=0), interface)
                except Empty:
                    sleep(0.01)

    def stop(self):
        self.keep_listening = False
        self.network.stop()
        [link.stop() for link in self.links]

        self.join()

    # I/O
    def send(self, type, message='', target='', encoding='UTF-8'):
        data = json.dumps({
            'type': type,
            'identifier': self.identifier,
            'message': message,
            'target': target
        })

        print('\nsending {}'.format(data))

        self.network.send(bytes(data, encoding))

        # Update Peer Info
        if target in self.peers:
            self.peer_info[target]['lastsend'] = time()

    def recv(self, packet, interface):
        data = json.loads(packet.decode())

        # Filter Packets not targeted to you
        if len(data['target']) != 0 and data['target'] != self.identifier:
            return

        print('\nreceived {}'.format(data))

        self.handle_data(data)

        # Update Peer Info
        sender = data['identifier']
        if sender in self.peers:
            self.peer_info[sender]['lastrecv'] = time()

    def handle_data(self, data):
        # Handle Request
        msg_type = data['type']
        sender = data['identifier']
        message = json.loads(data['message']) if data['message'] else {}

        if msg_type == 'version':
            registered = self.register_peer(sender, height=message.get('height'))

            if registered:
                self.send('verack', target=sender)
                self.send('version', target=sender, message=json.dumps({
                    'height': len(self.blockchain.chain)
                }))
            print(self.peers)
        elif msg_type == 'verack':
            self.ready = True

    # Methods
    def register_peer(self, identifier, height):
        """
        Add a new node to the list of nodes

        @param identifier: <str> Identifier of the node (eg: 'address:name')

        @return: <bool> True if a new peer was registered, False otherwise
        """

        if identifier not in self.peers:
            self.peers.add(identifier)
            self.peer_info[identifier] = {
                'identifier': identifier,
                'lastrecv': time(),
                'lastsend': None,
                'height': height
            }

            return True
        else:
            return False

    def get_peer(self, index=None):
        """
        Returns a random peer identifier unless specified by the parameter

        @param index: <int> Index of the peer in the peer list

        @return: <str> Peer identifier
        """

        if index is None:
            index = randint(0, len(self.peers) - 1)

        i = 0
        for p in self.peers:
            if i == index:
                return p
            i += 1


class BlockchainNode(Node):
    """
    Full Node

    - Maintains the full blockchain and all interactions
    - Independently and authoritatively verifies any transaction

    1. Send version to be in the network
    2. Synchronize the blockchain
    3. Listen for new blocks and transactions
    """

    def resolve_conflicts(self):
        """
        The Consensus Algorithm, replaces our chain with the longest valid chain in the network

        Note: This is not the algorithm the actual Bitcoin Core uses as it requires much more P2P,
        as a proof of concept, this was more suitable
        """
        print('Resolving Conflicts!')

        max_height = len(self.blockchain.chain)
        max_height_peer = None

        for peer in self.peers:
            peer_info = self.peer_info.get(peer)
            if peer_info:
                height = peer_info.get('height')
                if height > max_height:
                    max_height = height
                    max_height_peer = peer

        # Check if we actually need to update our blockchain
        if max_height_peer:
            self.send('getdata', target=max_height_peer)
        else:
            # Didn't need to update our blockchain
            self.synced = True

    # @override
    def handle_data(self, data):
        Node.handle_data(self, data)

        # Handle Request
        msg_type = data['type']
        sender = data['identifier']
        message = json.loads(data['message']) if data['message'] else {}

        if msg_type == 'getdata':
            self.send('chain', target=sender, message=json.dumps({
                'chain': self.blockchain.chain,
                'tx_info': self.blockchain.tx_info
            }))

        elif msg_type == 'chain':
            chain = message['chain']
            tx_info = message['tx_info']

            # Update Peer Info
            if sender in self.peers:
                self.peer_info[sender]['height'] = len(chain)

            # Update Chain
            if Blockchain.valid_chain(chain):
                self.blockchain.chain = chain
                self.blockchain.tx_info = {**self.blockchain.tx_info, **tx_info}
                self.synced = True
            else:
                # Invaild chain, ask for another peer's
                self.resolve_conflicts()

        elif msg_type == 'addblock':
            new_block = message['block']
            height = message['height']
            tx_info = message['tx_info']

            # Update Peer Info
            if sender in self.peers:
                self.peer_info[sender]['height'] = height

            # Update Chain
            chain = self.blockchain.chain.copy()
            chain.append(new_block)

            if Blockchain.valid_chain(chain):
                self.blockchain.chain = chain
                self.blockchain.tx_info = {**self.blockchain.tx_info, **tx_info}
            else:
                # Invalid chain, ask for another peer's chain
                self.resolve_conflicts()


class MinerNode(BlockchainNode):
    """
    Miner Node

    - In charge of adding new blocks to the blockchain
    """
    def proof_of_work(self, prev_hash):
        """
        Proof of Work Algorithm:
            - Find a number p' such that hash(pp') has 4 leading zeros
            - p was the previous block's hash, p' is the goal

        @param prev_hash: <str> Last Block's hash

        @return: <int> proof of work for the new block
        """

        proof = 0
        while Blockchain.valid_proof(prev_hash, proof) is False:
            proof += 1

        return proof

    def mine(self):
        # 1. Find the Proof of work
        # 2. Create the block
        # 3. Reward the miner

        last_block = self.blockchain.last_block
        prev_hash = Blockchain.hash(last_block)
        proof = self.proof_of_work(prev_hash)

        # Create a special transaction which acts as the reward for the miner
        # TODO: Change amount so it decreases over time
        self.blockchain.add_transaction(
            previous_hash='0',
            sender='0',
            recipient=self.identifier,  # TODO: Change later
            amount=50
        )

        block = self.blockchain.add_block(proof, prev_hash)
        self.send('addblock', message=json.dumps({
            'block': block,
            'tx_info': self.blockchain.tx_info,
            'height': len(self.blockchain.chain)
        }))

    # @override
    def handle_data(self, data):
        BlockchainNode.handle_data(self, data)

        # Handle Request
        msg_type = data['type']
        message = json.loads(data['message']) if data['message'] else {}

        if msg_type == 'addtx':
            # Add Transaction
            new_tx = message['tx']
            self.blockchain.add_transaction(**new_tx)


class SPVNode(Node):
    """
    Simplified Payment Verification Node

    - Download only block headers
    - Unable to verify UTXOs (Unspent Transaction Output)
    - Downloads a block header and the 6 next succeeding block headers related to a transaction
    """
    pass
