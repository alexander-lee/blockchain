from shortuuid import uuid
import time
import json
import argparse

from src.nodes import SPVNode
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
        blockchain = Blockchain(list(map(lambda block: block['header'], data['chain'])))
    else:
        filename = args.o
        blockchain = Blockchain()

    node = SPVNode(
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

        # Listen for new blocks being added
        while True:
            user_input = input('\nDo you want to add a transaction? (y/n) ')

            if user_input.lower == 'yes' or user_input.lower == 'y':
                recipient = input('Recipient: ')
                amount = input('Amount: ')
                previous_hash = input('Previous Hash: ')

                tx = node.blockchain.add_transaction(
                    sender=node.identifier,
                    recipient=recipient,
                    amount=amount,
                    previous_hash=previous_hash
                )

                if tx:
                    node.send('addtx', message=json.dumps({
                        'tx': tx
                    }))
            time.sleep(1)

    except (EOFError, KeyboardInterrupt):
        node.stop()
        node.blockchain.save(filename or 'blockchain.json')
