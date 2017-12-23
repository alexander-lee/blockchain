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
parser.add_argument('-n', type=str)
parser.add_argument('-p', type=int)
parser.add_argument('--file', type=str)
parser.add_argument('-o', type=str)

args = parser.parse_args()
node_id = uuid()

if __name__ == '__main__':
    # Load Blockchain File
    filename = args.file
    if filename:
        data = json.load(open(filename))
        blockchain = Blockchain(data['chain'])
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
        node.resolve_conflicts()
        while not node.synced:
            time.sleep(1)

        # Mine blocks
        while True:
            user_input = input('\nType anything to mine: ')
            if (user_input):
                print(f'{node.identifier} is mining!')
                node.mine()

                # Save Blockchain to file
                with open(filename or 'blockchain.json', 'w') as outfile:
                    json.dump({'chain': blockchain.chain}, outfile, indent=4)

            time.sleep(1)

    except (EOFError, KeyboardInterrupt):
        node.stop()

        # Save Blockchain to file
        with open(filename or 'blockchain.json', 'w') as outfile:
            json.dump({'chain': blockchain.chain}, outfile, indent=4)
