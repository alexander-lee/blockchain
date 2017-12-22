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

from blockchain import Blockchain


class Node(threading.Thread):
    def __init__(self, name, port=5000):
        threading.Thread.__init__(self)

        self.name = name
        self.address = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

        self.peer_info = {}
        self.peers = set()

        self.links = [UDPLink('en0', port=port)]
        self.network = NetworkComponent(self.links, name, Filters=(DuplicateFilter,))

        self.keep_listening = True
        self.ready = False

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

        print('sending {}'.format(data))

        self.network.send(bytes(data, encoding))

        # Update Peer Info
        if target in self.peers:
            self.peer_info[target]['lastsend'] = time()

    def recv(self, packet, interface):
        data = json.loads(packet.decode())

        # Filter Packets not targeted to you
        if len(data['target']) != 0 and data['target'] != self.identifier:
            return

        print('received {}'.format(data))

        # Handle Request
        msg_type = data['type']
        identifier = data['identifier']

        if msg_type == 'version':
            registered = self.register_peer(identifier)

            if registered:
                self.send('verack', target=identifier)
                self.send('version', target=identifier)
        if msg_type == 'verack':
            self.ready = True

        # Update Peer Info
        if identifier in self.peers:
            self.peer_info[identifier]['lastrecv'] = time()

    # Methods
    def register_peer(self, identifier):
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
                'lastsend': None
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
    """

    def __init__(self, name, port=5000, blockchain=Blockchain()):
        self.blockchain = blockchain
        Node.__init__(self, name, port)

    def resolve_conflicts(self):
        """
        The Consensus Algorithm, replaces our chain with the longest valid chain in the network

        @return: <bool> True if our chain was replaced, False otherwise
        """

        neighbours = self.peers
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

class MinerNode(Node):
    pass


class SPVNode(Node):
    """
    Simplified Payment Verification Node

    - Download only block headers
    - Unable to verify UTXOs (Unspent Transaction Output)
    - Downloads a block header and the 6 next succeeding block headers related to a transaction
    """
    pass
