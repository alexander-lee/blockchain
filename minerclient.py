from shortuuid import uuid
import time
import json
import argparse

from src.nodes import MinerNode
from src.blockchain import Blockchain


"""
===========
 MAIN CODE
===========
"""

parser = argparse.ArgumentParser()
parser.add_argument('-n', type=str, help='node name')
parser.add_argument('-p', type=int, help='port number (default: 5000)')
parser.add_argument('--file', type=str, help='specified file storing the blockchain (default: \'blockchain.json\')')
parser.add_argument('-o', type=str, help='output file without requiring an initial blockchain file to read from (default: \'blockchain.json\')')

args = parser.parse_args()
node_id = uuid()

if __name__ == '__main__':
    # Load Blockchain File
    filename = args.file
    if filename:
        data = json.load(open(filename))
        blockchain = Blockchain(data['chain'], data['tx_info'])
    else:
        filename = args.o
        blockchain = Blockchain()

    node = MinerNode(
        name=args.n or f'node-{node_id}',
        port=args.p or 5000,
        blockchain=blockchain
    )

    try:
        print(f'Starting node-{node_id}')

        # Establish Connection
        while not node.ready:
            node.send('version', message=json.dumps({
                'height': len(node.blockchain.chain)
            }))
            time.sleep(1)

        # Sync up with the other nodes
        while not node.synced:
            node.resolve_conflicts()
            time.sleep(5)

        # Mine blocks
        while True:
            user_input = input('\nType anything to mine: ')
            if (user_input):
                print(f'{node.identifier} is mining!')
                node.mine()
                node.blockchain.save(filename or 'blockchain.json')

            time.sleep(1)

    except (EOFError, KeyboardInterrupt):
        node.stop()
        node.blockchain.save(filename or 'blockchain.json')
