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
from mesh.filters import UniqueFilter
from mesh.node import Node as NetworkComponent


class Node(threading.Thread):
    def __init__(self, name, port=5000):
        threading.Thread.__init__(self)

        self.name = name
        self.address = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

        self.peer_info = {}
        self.peers = set()

        self.links = [UDPLink('en0', port=port)]
        self.network = NetworkComponent(self.links, name, Filters=(UniqueFilter,))
        self.keep_listening = True

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
    def send(self, type, message, encoding='UTF-8'):
        data = json.dumps({
            'type': type,
            'name': self.name,
            'address': self.address,
            'message': message
        })

        self.network.send(bytes(data, encoding))

    def recv(self, packet, interface):
        data = json.loads(packet.decode())
        msg_type = data['type']

        if msg_type == 'version':
            pass
        print('\n>> {}'.format(data))

    # Methods
    def register_peer(self, address, name=''):
        """
        Add a new node to the list of nodes

        @param address: <str> Address of the node (eg: 'http://127.0.0.1:5000')
        """

        parsed_url = urlparse(address)

        self.peers.add(f'{parsed_url.netloc}:{name}')
        self.peer_info[f'{parsed_url.netloc}:{name}'] = {
            'name': name,
            'address': parsed_url.netloc,
            'lastrecv': time()
        }

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
