from flask import Flask, jsonify, request
from uuid import uuid4
import time
import validators
import argparse

from nodes import Node

from blockchain import Blockchain

app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # 1. Find the Proof of work
    # 2. Create the block
    # 3. Reward the miner

    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Create a special transaction which acts as the reward for the miner
    # TODO: Change amount so it decreases over time
    blockchain.add_transaction(
        sender='0',
        recipient=node_identifier,
        amount='1'
    )

    previous_hash = blockchain.hash(last_block)
    block = blockchain.add_block(proof, previous_hash)

    response = {
        'message': 'New Block created',
        'hash': Blockchain.hash(block),
        'block': block,
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Validate Request
    required_fields = ['sender', 'recipient', 'amount']
    for field in required_fields:
        if field not in values:
            return f'Error: {field} is missing!', 400

    # Create transaction
    new_index = blockchain.add_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )

    response = {'message': f'Transaction will be added to block {new_index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }

    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes_to_add = values.get('nodes')

    # Validate Nodes
    if nodes_to_add is None or len(nodes_to_add) == 0:
        return 'Error: Please supply a valid lists of nodes', 400

    for node in nodes_to_add:
        if not validators.url(node):
            return f'Error: {node} is not a valid node', 400

    # Register Nodes
    for node in nodes_to_add:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been registered!',
        'nodes': list(blockchain.nodes)
    }

    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    has_replaced = blockchain.resolve_conflicts()
    response = {
        'chain': blockchain.chain
    }

    if has_replaced:
        response['message'] = 'Blockchain has been replaced'
    else:
        response['message'] = 'Blockchain has remained the same'

    return jsonify(response), 200


"""
===========
 MAIN CODE
===========
"""

parser = argparse.ArgumentParser()
parser.add_argument('-n', type=str)
parser.add_argument('-p', type=int)

args = parser.parse_args()

if __name__ == '__main__':
    node = Node(name=args.n or 'node', port=args.p or 5000)

    try:
        while True:
            print("------------------------------")
            message = input('<< ')
            node.send(type='shit', message=message)
            time.sleep(0.3)

    except (EOFError, KeyboardInterrupt):
        del node

    # app.run(host='localhost', port=args.p or 5000)
