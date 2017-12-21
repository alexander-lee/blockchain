import threading
import json
import netifaces as ni
from time import time, sleep
from urllib.parse import urlparse

try:
    from queue import Empty
except ImportError:
    from Queue import Empty

from mesh.links import UDPLink
from mesh.filters import DuplicateFilter
from mesh.node import Node as NetworkComponent


class Node(threading.Thread):
    def __init__(self, name, port=5000):
        threading.Thread.__init__(self)

        self.name = name
        self.address = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

        self.peer_info = {}
        self.peers = set()

        self.links = [UDPLink('en0', port=5000)]
        self.network = NetworkComponent(self.links, name, Filters=(DuplicateFilter,))

        self.keep_listening = True
        self.ready = False

        # Start Network Component
        [link.start() for link in self.links]
        self.network.start()
        self.start()

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
            'name': self.name,
            'address': self.address,
            'message': message,
            'target': target
        })

        print('sending {}'.format(data))

        self.network.send(bytes(data, encoding))

    def recv(self, packet, interface):
        data = json.loads(packet.decode())

        # Filter Packets not targeted to you
        if len(data['target']) != 0 and data['target'] != self.peer_str(self.address, self.name):
            return

        print('received {}'.format(data))

        # Handle Request
        msg_type = data['type']

        if msg_type == 'version':
            registered = self.register_peer(data['address'], data['name'])

            if registered:
                self.send('verack', target=self.peer_str(data['address'], data['name']))
                self.send('version', target=self.peer_str(data['address'], data['name']))
        if msg_type == 'verack':
            self.ready = True

    # Methods
    def peer_str(self, address, name=''):
        parsed_url = urlparse(address)
        return f'{parsed_url.path}:{name}'

    def register_peer(self, address, name=''):
        """
        Add a new node to the list of nodes

        @param address: <str> Address of the node (eg: '127.0.0.1')
        @param name: <str> Name of the node (eg: 'node-142231')

        @return: <bool> True if a new peer was registered, False otherwise
        """

        peer_str = self.peer_str(address, name)

        if peer_str not in self.peers:
            self.peers.add(peer_str)
            self.peer_info[peer_str] = {
                'name': name,
                'address': address,
                'lastrecv': time()
            }

            return True
        else:
            return False


class BlockchainNode(Node):
    """
    Full Node

    - Maintains the full blockchain and all interactions
    - Independently and authoritatively verifies any transaction
    """
    pass


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
